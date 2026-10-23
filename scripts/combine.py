"""Combine the public-data model (P) with the original ScamShield model (O) and measure it honestly.

    python scripts/combine.py

P  = char n-gram LR trained on the train portions of hf_multi / mishra_soni / upi_cmx (sources weighted 1/sqrt(size)).
O  = your original models/char_lr__clean (trained on UPI-CMX train, 3 classes: legit / promo / scam).
D  = a "message type" detector (UPI/bank-style vs public-corpus style), trained on the train portions.
COMBINED = d*O + (1-d)*P : trust the original model on UPI/bank-style text, the public model elsewhere.
(A learned logistic-regression blend was also tried and was clearly worse: it flagged 50-60% of genuine UPI messages.)
Everything is reported on TEST data none of the models has seen.
UPI-CMX uses its official template-disjoint train/val/test split; public sources use grouped splits."""
import sys, time, warnings
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.metrics import f1_score, recall_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import public_datasets as P_
import train_public as T            # make_model, prep, load_sources, drop_cross_source_overlap
from scamshield.models import classical
from scamshield.metrics import LABELS

prep = T.prep                        # keep the same name: saved models refer to it as __main__.prep


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def o_probs(O, texts):
    pr = O.predict_proba(list(texts))
    return pd.DataFrame(pr, columns=LABELS)


def features(P, O, D, texts):
    ps = P.predict_proba(list(texts))[:, 1]
    os_ = 1 - o_probs(O, texts)["legit"].values
    d = D.predict_proba(list(texts))[:, 1]
    lp, lo = logit(ps), logit(os_)
    return ps, os_, d, np.c_[lp, lo, d, d * lp, d * lo]


def metrics(y, pred):
    y = np.asarray(y); pred = np.asarray(pred).astype(int)
    return dict(n=len(y), macro_f1=round(f1_score(y, pred, average="macro"), 3), spam_recall=round(recall_score(y, pred), 3),
                ham_fpr=round(float(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)), 3))


def main():
    srcs = T.load_sources()
    srcs["upi_cmx"] = P_.load_upi(True)                      # keep the official split column
    parts = {}
    for k, d in srcs.items():
        if k == "upi_cmx":
            parts[k] = (d[d.split == "train"], d[d.split == "val"], d[d.split == "test"])
        else:
            tr, te = P_.grouped_split(d, 0.2, 0)
            tr, va = P_.grouped_split(tr, 0.2, 1)
            parts[k] = (tr, va, te)
    print({k: tuple(len(x) for x in v) for k, v in parts.items()}, "(train, val, test)")

    train = pd.concat([v[0] for v in parts.values()], ignore_index=True)
    w = 1.0 / np.sqrt(train.groupby("source").text.transform("size").values.astype(float)); w /= w.mean()
    t0 = time.time()
    P = T.make_model().fit(train.text, train.label.values, logisticregression__sample_weight=w)
    print(f"public model fitted on {len(train)} messages in {time.time()-t0:.0f}s")
    D = T.make_model().fit(train.text, (train.source == "upi_cmx").astype(int).values)
    O = classical.make("char_lr").load(str(ROOT / "artifacts" / "char_lr__clean.joblib"))

    rows = []
    for k, (_, _, te) in parts.items():
        groups = [(k, te)] + ([(f"{k}:{lg}", g) for lg, g in te.groupby("lang")] if k == "upi_cmx" else [])
        for name, g in groups:
            ps, os_, d, X = features(P, O, D, g.text)
            preds = {"public model alone": ps >= 0.5, "original model alone": os_ >= 0.5,
                     "either says spam": (ps >= 0.5) | (os_ >= 0.5),
                     "COMBINED (gated)": (d * os_ + (1 - d) * ps) >= 0.5}
            for m, pr in preds.items():
                rows.append(dict(test=name, method=m, **metrics(g.label.values, pr)))
    res = pd.DataFrame(rows)
    (ROOT / "results/public").mkdir(parents=True, exist_ok=True)
    res.to_csv(ROOT / "results/public/combined.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.to_string(index=False))
    joblib.dump({"public": P, "domain": D}, ROOT / "artifacts" / "combined.joblib")
    print("saved artifacts/combined.joblib")


if __name__ == "__main__":
    main()
