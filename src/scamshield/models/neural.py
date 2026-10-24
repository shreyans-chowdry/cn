"""Neural models trained from scratch: word-level BiGRU vs character-level CNN."""
import re
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score

torch.set_num_threads(max(1, torch.get_num_threads()))
_WORD_RE = re.compile(r"[\w\u0B80-\u0BFF]+|[^\w\s\u0B80-\u0BFF]", re.UNICODE)


def word_tokens(t):
    return _WORD_RE.findall(t.lower())


def char_tokens(t):
    return list(t.lower())


class Vocab:
    def __init__(self, tokens_iter, min_freq=2, max_size=50000):
        c = Counter(tok for toks in tokens_iter for tok in toks)
        self.itos = ["<pad>", "<unk>"] + [w for w, f in c.most_common(max_size) if f >= min_freq]
        self.stoi = {w: i for i, w in enumerate(self.itos)}

    def encode(self, toks, max_len):
        ids = [self.stoi.get(t, 1) for t in toks[:max_len]]
        return ids or [1]


class WordBiGRU(nn.Module):
    def __init__(self, vocab_size, emb=128, hid=128, n_cls=3, drop=0.3):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb, padding_idx=0)
        self.rnn = nn.GRU(emb, hid, batch_first=True, bidirectional=True)
        self.drop = nn.Dropout(drop)
        self.out = nn.Linear(4 * hid, n_cls)

    def forward(self, x):
        mask = (x != 0).unsqueeze(-1).float()
        h, _ = self.rnn(self.drop(self.emb(x)))
        mx = (h - 1e4 * (1 - mask)).max(1).values
        mean = (h * mask).sum(1) / mask.sum(1).clamp(min=1)
        return self.out(self.drop(torch.cat([mx, mean], -1)))


class CharCNN(nn.Module):
    def __init__(self, vocab_size, emb=64, filters=128, kernels=(3, 5, 7), n_cls=3, drop=0.3):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb, padding_idx=0)
        self.convs = nn.ModuleList([nn.Conv1d(emb, filters, k, padding=k // 2) for k in kernels])
        self.conv2 = nn.Conv1d(filters * len(kernels), 256, 3, padding=1)
        self.drop = nn.Dropout(drop)
        self.out = nn.Linear(256, n_cls)

    def forward(self, x):
        e = self.emb(x).transpose(1, 2)
        h = torch.cat([F.relu(c(e)) for c in self.convs], 1)
        h = F.max_pool1d(h, 2)
        h = F.relu(self.conv2(self.drop(h)))
        return self.out(self.drop(h.max(-1).values))


class TorchTextModel:
    family = "neural"

    def __init__(self, name, granularity, epochs=12, batch_size=64, lr=2e-3, patience=3):
        self.name, self.granularity = name, granularity
        self.epochs, self.bs, self.lr, self.patience = epochs, batch_size, lr, patience
        self.tok = word_tokens if granularity == "word" else char_tokens
        self.max_len = 80 if granularity == "word" else 320

    def _batches(self, X, y=None, shuffle=False, rng=None):
        idx = np.arange(len(X))
        if shuffle:
            rng.shuffle(idx)
        for s in range(0, len(idx), self.bs):
            b = idx[s:s + self.bs]
            seqs = [self.vocab.encode(self.tok(X[i]), self.max_len) for i in b]
            L = max(len(q) for q in seqs)
            arr = torch.zeros(len(seqs), max(L, 7), dtype=torch.long)
            for j, q in enumerate(seqs):
                arr[j, :len(q)] = torch.tensor(q)
            yield arr, (torch.tensor(np.asarray(y)[b]) if y is not None else None)

    def fit(self, X, y, Xv=None, yv=None, seed=0):
        X = list(X)
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        self.vocab = Vocab((self.tok(t) for t in X), min_freq=2 if self.granularity == "word" else 1,
                           max_size=50000 if self.granularity == "word" else 3000)
        self.net = (WordBiGRU if self.granularity == "word" else CharCNN)(len(self.vocab.itos))
        y = np.asarray(y)
        w = torch.tensor(len(y) / (3 * np.bincount(y, minlength=3).clip(1)), dtype=torch.float)
        opt = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=1e-4)
        best, best_state, bad = -1, None, 0
        for ep in range(self.epochs):
            self.net.train()
            for xb, yb in self._batches(X, y, shuffle=True, rng=rng):
                opt.zero_grad()
                loss = F.cross_entropy(self.net(xb), yb, weight=w)
                loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                opt.step()
            if Xv is not None:
                f1 = f1_score(yv, self.predict_proba(list(Xv)).argmax(1), average="macro")
                if f1 > best:
                    best, bad = f1, 0
                    best_state = {k: v.clone() for k, v in self.net.state_dict().items()}
                else:
                    bad += 1
                    if bad >= self.patience:
                        break
        if best_state is not None:
            self.net.load_state_dict(best_state)
        self.best_val_f1 = best
        return self

    @torch.no_grad()
    def predict_proba(self, X, batch_size=None):
        self.net.eval()
        out = [F.softmax(self.net(xb), -1).numpy() for xb, _ in self._batches(list(X))]
        return np.concatenate(out) if out else np.zeros((0, 3))

    def n_params(self):
        return sum(p.numel() for p in self.net.parameters())

    def save(self, path):
        torch.save({"vocab": self.vocab.itos, "state": self.net.state_dict(), "name": self.name,
                    "granularity": self.granularity}, path)

    def load(self, path):
        ck = torch.load(path, weights_only=False)
        self.vocab = Vocab([])
        self.vocab.itos = ck["vocab"]
        self.vocab.stoi = {w: i for i, w in enumerate(self.vocab.itos)}
        self.net = (WordBiGRU if self.granularity == "word" else CharCNN)(len(self.vocab.itos))
        self.net.load_state_dict(ck["state"])
        self.net.eval()
        return self


def make(name, seed=0):
    return {"word_bigru": lambda: TorchTextModel("word_bigru", "word"),
            "char_cnn": lambda: TorchTextModel("char_cnn", "char")}[name]()


NAMES = ["word_bigru", "char_cnn"]
