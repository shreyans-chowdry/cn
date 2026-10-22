"""Fine-tuned multilingual transformers (subword: DistilmBERT, XLM-R, MuRIL; character: CANINE)."""
import time

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import f1_score

def _device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


HF_MODELS = {
    "distil_mbert": ("distilbert-base-multilingual-cased", "subword", 5e-5),
    "xlmr": ("xlm-roberta-base", "subword", 3e-5),
    "muril": ("google/muril-base-cased", "subword", 3e-5),
    "canine": ("google/canine-s", "char", 5e-5),
}


FREEZE_WORD_EMBEDDINGS = {"xlmr", "muril"}


class HFModel:
    family = "transformer"

    def __init__(self, name, epochs=3, batch_size=16, max_len=96, verbose=True):
        self.name = name
        self.hf_id, self.granularity, self.lr = HF_MODELS[name]
        self.epochs, self.bs, self.verbose = epochs, batch_size, verbose
        self.max_len = 320 if self.granularity == "char" else max_len
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(self.hf_id)
        self.device = _device()

    def _enc(self, texts):
        enc = self.tok(list(texts), padding=True, truncation=True, max_length=self.max_len,
                       return_tensors="pt")
        return {k: v.to(self.device) for k, v in enc.items()}

    def fit(self, X, y, Xv=None, yv=None, seed=0):
        from transformers import AutoModelForSequenceClassification, get_linear_schedule_with_warmup
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        X, y = list(X), np.asarray(y)
        self.net = AutoModelForSequenceClassification.from_pretrained(self.hf_id, num_labels=3).to(self.device)
        if self.name in FREEZE_WORD_EMBEDDINGS:
            # 250k/197k-token vocabularies: freezing the input embedding matrix keeps AdamW state within CPU memory
            self.net.get_input_embeddings().weight.requires_grad_(False)
        params = [p for p in self.net.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=self.lr, weight_decay=0.01)
        steps = self.epochs * ((len(X) + self.bs - 1) // self.bs)
        sch = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
        w = torch.tensor(len(y) / (3 * np.bincount(y, minlength=3).clip(1)), dtype=torch.float).to(self.device)
        # length-bucketed batches -> far less padding on CPU
        lens = np.array([len(t) for t in X])
        best, best_state = -1, None
        t0 = time.time()
        for ep in range(self.epochs):
            self.net.train()
            order = np.argsort(lens + rng.uniform(0, 25, len(lens)))
            batches = [order[i:i + self.bs] for i in range(0, len(order), self.bs)]
            rng.shuffle(batches)
            for k, b in enumerate(batches):
                enc = self._enc([X[i] for i in b])
                logits = self.net(**enc).logits
                loss = F.cross_entropy(logits, torch.tensor(y[b]).to(self.device), weight=w)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step(); sch.step(); opt.zero_grad()
                if self.verbose and k % 100 == 0:
                    print(f"  [{self.name}] ep{ep} step {k}/{len(batches)} loss {loss.item():.3f} "
                          f"({time.time() - t0:.0f}s)", flush=True)
            if Xv is not None:
                f1 = f1_score(yv, self.predict_proba(list(Xv)).argmax(1), average="macro")
                if self.verbose:
                    print(f"  [{self.name}] epoch {ep} val macro-F1 {f1:.4f}", flush=True)
                if f1 > best:
                    best = f1
                    if self.epochs > 1:  # with one epoch the final weights are the best weights
                        best_state = {k: v.detach().clone() for k, v in self.net.state_dict().items()}
        if best_state is not None:
            self.net.load_state_dict(best_state)
        self.best_val_f1 = best
        return self

    @torch.no_grad()
    def predict_proba(self, X, batch_size=64):
        self.net.eval()
        X = list(X)
        if not X:
            return np.zeros((0, 3))
        order = np.argsort([len(t) for t in X])
        out = np.zeros((len(X), 3), dtype=np.float32)
        for s in range(0, len(X), batch_size):
            b = order[s:s + batch_size]
            enc = self._enc([X[i] for i in b])
            out[b] = F.softmax(self.net(**enc).logits, -1).float().cpu().numpy()
        return out

    def n_params(self):
        return sum(p.numel() for p in self.net.parameters())

    def save(self, path):
        self.net.save_pretrained(path)
        self.tok.save_pretrained(path)

    def load(self, path):
        from transformers import AutoModelForSequenceClassification
        self.net = AutoModelForSequenceClassification.from_pretrained(path).to(self.device)
        self.net.eval()
        return self


def make(name, seed=0, **kw):
    return HFModel(name, **kw)


NAMES = list(HF_MODELS)
