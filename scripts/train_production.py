"""
Train the production detector served by the web app, the TCP/UDP services and the Android app.

    python scripts/train_production.py

Training data
  * UPI-BiSMS train + val (English and Tamil-English), plus one obfuscated copy of 50% of them
    (levels L1-L4 drawn uniformly, so the model has also seen transliterated text)
  * Mishra & Soni public SMS corpus, train portion: ham / spam / smishing -> legit / promo / scam
  * UCI and ExAIS genuine (ham) messages, train portion -> legit
    (their spam labels mix scams and adverts, so they are only used for binary evaluation)

Outputs
  artifacts/production.joblib                       model + metadata (loaded by scamshield.detector)
  android/app/src/main/assets/model.json            the same model for the phone
  android/app/src/test/resources/parity.json        texts + expected probabilities (Kotlin parity test)
  results/production_eval.json, results/tables/table12_production.csv
"""
import json
import random
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scamshield.data import public as PUB          # noqa: E402
from scamshield.metrics import LABELS, all_metrics  # noqa: E402
from scamshield.obfuscation import normalize, obfuscate  # noqa: E402

LAB = {l: i for i, l in enumerate(LABELS)}


def build_pipeline():
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True,
                          max_features=60000, preprocessor=normalize, lowercase=False, dtype=np.float64)
    clf = LogisticRegression(C=10.0, max_iter=4000, class_weight="balanced")
    return Pipeline([("tfidf", vec), ("clf", clf)])


def training_data(seed=0):
    rng = random.Random(seed)
    bisms = pd.read_csv(ROOT / "data" / "upi_bisms.csv")
    tr = bisms[bisms.split != "test"]
    aug = [(obfuscate(t, rng.choice([1, 2, 3, 4]), seed=50_000 + i), l)
           for i, (t, l) in enumerate(zip(tr.text, tr.label)) if rng.random() < 0.5]
    pub = PUB.load_public()
    ptr, pte = PUB.grouped_split(pub, 0.2, seed=seed)
    ptr3 = ptr[ptr.label3.isin(LABELS)]                       # drop binary-only 'spam'
    texts = list(tr.text) + [a for a, _ in aug] + list(ptr3.text)
    labels = list(tr.label) + [b for _, b in aug] + list(ptr3.label3)
    sources = ["upi_bisms"] * len(tr) + ["upi_bisms_aug"] * len(aug) + list(ptr3.source)
    return texts, labels, sources, bisms[bisms.split == "test"], pte


def evaluate(pipe, bisms_test, pub_test):
    out = {}
    order = [list(pipe.classes_).index(c) for c in LABELS]
    y = bisms_test.label.map(LAB).values
    for lv in range(5):
        if lv == 0:
            texts = bisms_test.text.tolist()
        else:
            texts = pd.read_csv(ROOT / "data" / "obf" / f"L{lv}_targeted_s0.csv").text.fillna("").tolist()
        p = pipe.predict_proba(texts)[:, order]
        m = all_metrics(p, y)
        out[f"upi_bisms_L{lv}"] = {k: v for k, v in m.items() if k != "confusion"}
        for lang in ("en", "ta"):
            k = (bisms_test.lang == lang).values
            mm = all_metrics(p[k], y[k])
            out[f"upi_bisms_L{lv}_{lang}"] = {k2: v for k2, v in mm.items() if k2 != "confusion"}
    for src, g in pub_test.groupby("source"):
        p = pipe.predict_proba(g.text.tolist())[:, order]
        pred_unwanted = (p[:, LAB["legit"]] < 0.5).astype(int)
        yb = g.binary.values
        res = {"n": len(g), "binary_f1_macro": float(f1_score(yb, pred_unwanted, average="macro")),
               "unwanted_recall": float((pred_unwanted[yb == 1] == 1).mean()) if (yb == 1).any() else None,
               "legit_fpr": float((pred_unwanted[yb == 0] == 1).mean()) if (yb == 0).any() else None}
        if g.label3.isin(LABELS).all():
            m = all_metrics(p, g.label3.map(LAB).values)
            res.update({k: v for k, v in m.items() if k != "confusion"})
        out[f"public_{src}"] = res
    return out


def main():
    t0 = time.time()
    texts, labels, sources, bisms_test, pub_test = training_data()
    print(f"training on {len(texts)} messages:", pd.Series(sources).value_counts().to_dict(), flush=True)
    pipe = build_pipeline().fit(texts, labels)
    print(f"fit in {time.time() - t0:.0f}s, vocabulary {len(pipe.named_steps['tfidf'].vocabulary_)}")
    ev = evaluate(pipe, bisms_test, pub_test)
    meta = {"trained": time.strftime("%Y-%m-%d"), "n_train": len(texts), "sources": pd.Series(sources).value_counts().to_dict(),
            "eval": {k: {m: round(v, 4) if isinstance(v, float) else v for m, v in d.items()} for k, d in ev.items()}}
    (ROOT / "artifacts").mkdir(exist_ok=True)
    joblib.dump({"pipeline": pipe, "meta": meta}, ROOT / "artifacts" / "production.joblib", compress=3)
    (ROOT / "results").mkdir(exist_ok=True)
    json.dump(meta, open(ROOT / "results" / "production_eval.json", "w"), indent=1)
    rows = []
    for k, d in ev.items():
        rows.append({"test set": k, "n": d.get("n", ""), "macro-F1": round(d.get("macro_f1", float("nan")), 3),
                     "scam FNR": round(d.get("fnr_scam", float("nan")), 3), "scam FPR": round(d.get("fpr_scam", float("nan")), 3),
                     "ECE": round(d.get("ece", float("nan")), 3),
                     "binary macro-F1": round(d["binary_f1_macro"], 3) if "binary_f1_macro" in d else "",
                     "unwanted recall": round(d["unwanted_recall"], 3) if d.get("unwanted_recall") is not None else "",
                     "genuine FPR": round(d["legit_fpr"], 3) if d.get("legit_fpr") is not None else ""})
    (ROOT / "results" / "tables").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(ROOT / "results" / "tables" / "table12_production.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))

    # ---- mobile export + parity fixtures
    from scamshield.detector import Detector
    det = Detector()
    out = det.export_mobile(ROOT / "android" / "app" / "src" / "main" / "assets" / "model.json")
    print("exported", out, f"{out.stat().st_size / 1e6:.1f} MB")
    rng = random.Random(1)
    sample = bisms_test.sample(150, random_state=1).text.tolist()
    sample += [obfuscate(t, rng.choice([2, 3, 4]), seed=i) for i, t in enumerate(sample[:100])]
    sample += pub_test.sample(50, random_state=1).text.tolist()
    probs = det.proba(sample)
    fixture = [{"text": t, "normalized": normalize(t), "probs": [round(float(v), 6) for v in p]} for t, p in zip(sample, probs)]
    fx = ROOT / "android" / "app" / "src" / "test" / "resources" / "parity.json"
    fx.parent.mkdir(parents=True, exist_ok=True)
    json.dump(fixture, open(fx, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("parity fixtures:", len(fixture))


if __name__ == "__main__":
    main()
