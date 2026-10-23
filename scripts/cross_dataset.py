"""Cross-dataset generalisation: train on one corpus, test on another. Binary spam vs ham.
    PYTHONPATH=src python scripts/cross_dataset.py"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, recall_score, precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from scamshield.models import classical
from scamshield.obfuscation import normalize
import public_datasets as P

MODELS = ["word_nb", "word_lr", "word_svm", "char_lr", "char_svm"]


def binary_model(name):
    m = classical.make(name)
    return m


def metrics(y, p):
    pred = (p >= 0.5).astype(int)
    return dict(macro_f1=f1_score(y, pred, average="macro"), spam_recall=recall_score(y, pred),
                spam_precision=precision_score(y, pred, zero_division=0),
                ham_fpr=float(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)),
                auc=roc_auc_score(y, p), n=len(y), spam_rate=float(y.mean()))


def run(train, tests, norm):
    f = (lambda xs: [normalize(x) for x in xs]) if norm else (lambda xs: list(xs))
    rows = []
    for name in MODELS:
        m = binary_model(name).fit(f(train.text), train.label.values)
        for tname, te in tests.items():
            p = m.predict_proba(f(te.text))[:, 1]
            rows.append(dict(model=name, norm=norm, test=tname, **metrics(te.label.values, p)))
    return rows


def main():
    uci = P.load_uci()
    u_tr, u_te = P.grouped_split(uci, 0.2, seed=0)
    upi = P.load_upi(promo_as_spam=True)
    p_tr, p_te = upi[upi.split != "test"], upi[upi.split == "test"]
    print(f"UCI train {len(u_tr)} test {len(u_te)} | UPI train {len(p_tr)} test {len(p_te)}")
    tests = {"UCI(en)": u_te, "UPI-CMX": p_te}
    allrows = []
    for tname, tr in (("UCI", u_tr), ("UPI-CMX", p_tr), ("UCI+UPI-CMX", pd.concat([u_tr, p_tr]))):
        for norm in (False, True):
            t0 = time.time()
            rows = run(tr, tests, norm)
            for r in rows:
                r["train"] = tname
            allrows += rows
            print(f"train={tname} norm={norm} done {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(allrows)
    df.to_csv(ROOT / "results/public/cross_dataset.csv", index=False)
    pd.set_option("display.width", 200)
    print(df[df.norm == False].round(3)[["train", "test", "model", "macro_f1", "spam_recall", "ham_fpr", "auc"]].to_string(index=False))
    print("\nWITH normaliser")
    print(df[df.norm == True].round(3)[["train", "test", "model", "macro_f1", "spam_recall", "ham_fpr", "auc"]].to_string(index=False))


if __name__ == "__main__":
    main()
