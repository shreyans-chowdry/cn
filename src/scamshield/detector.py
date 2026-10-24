"""
The ScamShield production detector: the single model behind the web app, the TCP/UDP
services and (exported to JSON) the Android app.

    text --canonicalise--> char 2-5-gram TF-IDF --> logistic regression --> P(legit, promo, scam)
                                                                        |
    links in the text --> lexical + DNS + CIDR link intelligence -------+--> fused verdict + reasons

Why this model: in the experiments, character n-grams on canonicalised text gave the best mix of
robustness to obfuscation, calibration and latency (about 1 ms per message on a CPU), and it can
run on a phone with no ML runtime. Fusion: P'(scam) = 1 - (1 - P(scam)) * (1 - 0.6 * link_risk).
"""
import json
import re
import time
from pathlib import Path

import numpy as np

from .langid import identify
from .metrics import LABELS
from .net import urlintel
from .obfuscation import normalize, split_affixes

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts"
LINK_WEIGHT = 0.6
SCAM_THRESHOLD = 0.5

# Multilingual cue rules (English plus each supported code-mixed language). They only *explain* a
# verdict (shown to the user); they do not change scores.
CUES = [
    ("pin_to_receive", "Asks for your UPI PIN to receive money. A PIN is only ever needed to send money.",
     [r"\bpin\b.*(receive|get the amount|accept|money will come|பெற|வரும்|வந்த|पाने|पैसे आ|आ जाएँगे)",
      r"(receive|பெற|வரும்|पाने के लिए).*\bpin\b"]),
    ("share_otp", "Asks you to share an OTP, card number or CVV.",
     [r"(share|tell|reply|சொல்லுங்கள்|reply செய்யவும்|बताएँ|बताओ|reply करें).{0,25}(otp|cvv|card number)",
      r"(otp|cvv)-?ஐ? ?(சொல்லுங்கள்|share|बताएँ|बताओ)"]),
    ("urgency", "Creates urgency (today, immediately, last day).",
     [r"\b(immediately|urgent|within 24|last day|today only|tonight|expire[sd]? today)\b",
      r"(உடனே|உடனடியாக|இப்போதே|இன்றே|கடைசி நாள்|இன்று இரவு|24 மணி)",
      r"(तुरंत|फ़ौरन|आज रात|आखिरी दिन|24 घंटे|सिर्फ आज)"]),
    ("threat", "Threatens to block, suspend or disconnect, or mentions police / FIR.",
     [r"\b(block(ed)?|suspend(ed)?|disconnect(ed)?|seized|police|fir)\b",
      r"(துண்டிக்கப்படும்|பறிமுதல்|block செய்யப்படும்|suspend)",
      r"(काट दिया जाएगा|काट दी जाएगी|ज़ब्त|पुलिस|दर्ज होगी)"]),
    ("fee_first", "Asks you to pay a fee first to get a prize, loan, job or parcel.",
     [r"(registration|processing|joining|release|file) (fee|charge)"]),
    ("remote_access", "Asks you to install a screen-sharing app (AnyDesk, TeamViewer).",
     [r"\b(anydesk|teamviewer|quicksupport|rustdesk)\b"]),
    ("prize", "Claims you won a prize or lucky draw.",
     [r"\b(won|winner|lucky draw|prize|congrat)", r"(பரிசு|வென்றுள்ள|வாழ்த்துக்கள்)", r"(इनाम|जीते हैं|बधाई हो)"]),
    ("qr_scan", "Asks you to scan a QR code to receive money.", [r"\bscan\b.{0,30}\bqr\b|\bqr\b.{0,30}\bscan\b"]),
    ("wrong_transfer", "Claims money was sent to you by mistake and asks for it back.",
     [r"(by mistake|wrong number|sent .* to you by mistake)", r"(தவறுதலாக|தவறான எண்ணுக்கு)", r"(गलती से|गलत नंबर)"]),
    ("job_lure", "Offers easy money for simple tasks or part-time work.",
     [r"(part time job|work from home|daily income|simple tasks|like youtube)", r"(घर बैठे|task पूरे)"]),
]
SAFE_CUES = [r"(do not share|never asks|பகிர வேண்டாம்|கேட்காது|not required to receive|தேவையில்லை|"
             r"share न करें|नहीं माँगता|ज़रूरत नहीं)"]


def explain_cues(text):
    t = normalize(text)
    hits = []
    for cid, msg, pats in CUES:
        if any(re.search(p, t, re.I) for p in pats):
            hits.append({"id": cid, "text": msg})
    if any(re.search(p, t, re.I) for p in SAFE_CUES):
        hits = [h for h in hits if h["id"] not in ("share_otp", "pin_to_receive")]
    return hits


class Detector:
    def __init__(self, path=None, resolver=None):
        import joblib
        self.path = Path(path or ART / "production.joblib")
        bundle = joblib.load(self.path)
        self.pipe = bundle["pipeline"]
        self.meta = bundle.get("meta", {})
        self.vec = self.pipe.named_steps["tfidf"]
        self.clf = self.pipe.named_steps["clf"]
        self.classes = list(self.clf.classes_)
        self.resolver = resolver
        self._vocab_inv = None

    def proba(self, texts):
        p = self.pipe.predict_proba(list(texts))
        return p[:, [self.classes.index(c) for c in LABELS]]

    def _highlights(self, text, x_row):
        """Per-token contribution to the scam logit (relative to the other classes)."""
        if self._vocab_inv is None:
            self._vocab_inv = self.vec.vocabulary_
        coef = self.clf.coef_
        si = self.classes.index("scam")
        w = coef[si] - coef.mean(axis=0)
        out = []
        for tok in text.split():
            pre, core, post = split_affixes(tok)
            norm = normalize(core) if core else ""
            score = 0.0
            for word in norm.split():
                padded = f" {word} "
                for n in range(2, 6):
                    for i in range(max(1, len(padded) - n + 1)):
                        j = self._vocab_inv.get(padded[i:i + n])
                        if j is not None:
                            score += x_row[0, j] * w[j]
            out.append({"token": tok, "score": round(float(score), 3)})
        return out

    def analyse(self, text, use_dns=True, explain=True):
        t0 = time.perf_counter()
        x = self.vec.transform([text])
        p = self.clf.predict_proba(x)[0]
        probs = {c: float(p[self.classes.index(c)]) for c in LABELS}
        t_model = time.perf_counter() - t0
        links = urlintel.analyse(text, self.resolver if use_dns else None)
        fused = dict(probs)
        if links["risk"] > 0:
            ps = 1 - (1 - probs["scam"]) * (1 - LINK_WEIGHT * links["risk"])
            rest = 1 - probs["scam"]
            for c in ("legit", "promo"):
                fused[c] = probs[c] * (1 - ps) / rest if rest > 0 else 0.0
            fused["scam"] = ps
        label = "scam" if fused["scam"] >= SCAM_THRESHOLD else max(("legit", "promo"), key=lambda c: fused[c])
        lid = identify(text)
        out = {"label": label, "probs": fused, "text_probs": probs, "links": links["links"],
               "link_risk": links["risk"], "language": {"code": lid["lang"], "name": lid["name"], "cmi": lid["cmi"],
                                                         "tokens": lid["tokens"]},
               "normalized": normalize(text), "model_ms": round(t_model * 1000, 3),
               "total_ms": round((time.perf_counter() - t0) * 1000, 3)}
        if explain:
            out["cues"] = explain_cues(text)
            out["highlights"] = self._highlights(text, x)
        return out

    # ------------------------------------------------------------------ export for Android
    def export_mobile(self, path):
        """Everything the Kotlin port needs to reproduce `proba` exactly."""
        from . import scripts as S
        from .langid import EN_VOCAB
        from .obfuscation import REVERSE_HOMOGLYPHS, DELEET
        vocab = self.vec.vocabulary_
        terms = [None] * len(vocab)
        for t, i in vocab.items():
            terms[i] = t
        order = [self.classes.index(c) for c in LABELS]
        model = {
            "format": "scamshield-charlr-v1", "classes": LABELS,
            "ngram_range": list(self.vec.ngram_range), "sublinear_tf": bool(self.vec.sublinear_tf),
            "terms": terms, "idf": [round(float(v), 6) for v in self.vec.idf_],
            "coef": [[round(float(v), 6) for v in self.clf.coef_[k]] for k in order],
            "intercept": [float(self.clf.intercept_[k]) for k in order],
            "link_weight": LINK_WEIGHT, "scam_threshold": SCAM_THRESHOLD,
            "normalize": {"homoglyphs": REVERSE_HOMOGLYPHS, "deleet": DELEET,
                          "lookalikes": S.LOOKALIKE_TO_LETTER, "native2en": S.X2EN},
            "scripts": [{"code": m.CODE, "name": m.NAME, "lo": m.LO, "hi": m.HI, "roman": sorted(m.ROMAN),
                         "roman_regex": m.ROMAN_RE} for m in S.SCRIPTS.values()],
            "cues": [{"id": c, "text": m, "patterns": p} for c, m, p in CUES], "safe_cues": SAFE_CUES,
            "langid": {"en_vocab": sorted(EN_VOCAB)},
            "links": {"shorteners": sorted(urlintel.SHORTENERS), "risky_tlds": sorted(urlintel.RISKY_TLDS),
                      "official": {k: sorted(v) for k, v in urlintel.OFFICIAL.items()},
                      "risky_special": list(urlintel.RISKY_SPECIAL)},
            "meta": {k: v for k, v in self.meta.items() if k != "eval"},
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, separators=(",", ":"))
        return Path(path)


_DEFAULT = None


def get_detector():
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = Detector()
    return _DEFAULT
