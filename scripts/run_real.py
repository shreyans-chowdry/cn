"""Train / evaluate on public SMS-spam corpora (+ UPI-CMX).  Run:  PYTHONPATH=src python scripts/run_real.py
Experiments: (A) in-corpus 5-fold CV, (B) leave-one-corpus-out transfer, (C) pooled model + per-corpus test,
(D) obfuscation robustness of the pooled model on REAL test messages, (E) calibration / threshold for the app model."""
import json, sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd, joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from scamshield.realdata import load_all, Norm
from scamshield.obfuscation import obfuscate, normalize

OUT = ROOT / "results" / "real"; OUT.mkdir(parents=True, exist_ok=True)
SEED = 0

def ece(p, y, bins=15):
    e = 0; n = len(y)
    for lo in np.linspace(0, 1, bins + 1)[:-1]:
        m = (p >= lo) & (p < lo + 1 / bins + (1e-9 if lo + 1 / bins >= 1 else 0))
        if m.any():
            conf = np.where(p[m] >= .5, p[m], 1 - p[m]).mean(); acc = ((p[m] >= .5) == y[m]).mean()
            e += m.sum() / n * abs(acc - conf)
    return float(e)

def metrics(p, y, thr=.5):
    pred = (p >= thr).astype(int)
    return dict(f1=f1_score(y, pred), prec=precision_score(y, pred, zero_division=0), rec=recall_score(y, pred),
                fpr=float(((pred == 1) & (y == 0)).sum() / max(1, (y == 0).sum())),
                auc=roc_auc_score(y, p) if len(set(y)) > 1 else np.nan, ap=average_precision_score(y, p), ece=ece(p, y))

def wvec(): return TfidfVectorizer(lowercase=True, token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
def cvec(): return TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True, max_features=300_000)
def lr(C=10): return LogisticRegression(C=C, max_iter=4000, class_weight="balanced")
def svm(C=.5): return CalibratedClassifierCV(LinearSVC(C=C, class_weight="balanced"), cv=3, method="sigmoid")

def build(name):
    n = name.endswith("+norm"); b = name.replace("+norm", "")
    vec = {"word_lr": wvec, "char_lr": cvec, "word_svm": wvec, "char_svm": cvec, "word_nb": None, "union_lr": None}[b]
    if b == "word_nb": steps = [("vec", CountVectorizer(lowercase=True, token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2), min_df=2)), ("clf", MultinomialNB(alpha=.3))]
    elif b == "union_lr": steps = [("vec", FeatureUnion([("w", wvec()), ("c", cvec())])), ("clf", lr(10))]
    elif b.endswith("svm"): steps = [("vec", vec()), ("clf", svm())]
    else: steps = [("vec", vec()), ("clf", lr(10))]
    if n: steps = [("norm", Norm())] + steps
    return Pipeline(steps)

def fitpred(name, tr, te):
    m = build(name); m.fit(tr.text.tolist(), tr.label.values); return m, m.predict_proba(te.text.tolist())[:, 1]

MODELS = ["word_nb", "word_lr", "word_svm", "char_lr", "char_svm", "char_lr+norm", "union_lr+norm"]
df, st = load_all(include_synthetic=True)
print(st); print(df.groupby("source").label.agg(["count", "mean"]))
df.groupby("source").label.agg(n="count", spam_rate="mean").to_csv(OUT / "corpora.csv")
json.dump(st, open(OUT / "dedup_stats.json", "w"))
SRC = ["uci", "exais", "upi_cmx"]; REALSRC = ["uci", "exais"]
res = {}

# (A) in-corpus 5-fold CV
rows = []
for s in SRC:
    d = df[df.source == s].reset_index(drop=True)
    for mn in MODELS:
        ms = []
        folds = [(np.where(d.split != "test")[0], np.where(d.split == "test")[0])] if s == "upi_cmx" else \
            list(StratifiedKFold(3, shuffle=True, random_state=SEED).split(d, d.label))
        for k, (a, b) in enumerate(folds):
            _, p = fitpred(mn, d.iloc[a], d.iloc[b]); ms.append(metrics(p, d.label.values[b]))
        r = pd.DataFrame(ms).mean().to_dict(); r.update(corpus=s, model=mn, f1_sd=pd.DataFrame(ms).f1.std()); rows.append(r)
    print("A", s, flush=True)
pd.DataFrame(rows).to_csv(OUT / "A_in_corpus_cv.csv", index=False)

# (B) leave-one-corpus-out
rows = []
for held in SRC:
    tr = df[df.source != held]; te = df[df.source == held]
    for mn in MODELS:
        _, p = fitpred(mn, tr, te); r = metrics(p, te.label.values); r.update(test=held, train="+".join(s for s in SRC if s != held), model=mn); rows.append(r)
    print("B", held, flush=True)
pd.DataFrame(rows).to_csv(OUT / "B_leave_one_corpus_out.csv", index=False)

# (C) pooled: 60/20/20 per corpus; model selection on val, report on test
tr_l, va_l, te_l = [], [], []
for s in SRC:
    d = df[df.source == s]
    if s == "upi_cmx":
        a, v, t = d[d.split == "train"], d[d.split == "val"], d[d.split == "test"]
    else:
        a, t = train_test_split(d, test_size=.2, stratify=d.label, random_state=SEED)
        a, v = train_test_split(a, test_size=.25, stratify=a.label, random_state=SEED)
    tr_l.append(a); va_l.append(v); te_l.append(t)
tr, va, te = pd.concat(tr_l), pd.concat(va_l), pd.concat(te_l)
rows = []; probs = {}; fitted = {}
for mn in MODELS:
    m, pv = fitpred(mn, tr, va); fitted[mn] = m
    pt = m.predict_proba(te.text.tolist())[:, 1]; probs[mn] = (pv, pt)
    for s in SRC + ["REAL", "ALL"]:
        mk = te.source.isin(REALSRC).values if s == "REAL" else ((te.source == s).values if s != "ALL" else np.ones(len(te), bool))
        r = metrics(pt[mk], te.label.values[mk]); r.update(corpus=s, model=mn, val_f1_real=metrics(pv[va.source.isin(REALSRC).values], va.label.values[va.source.isin(REALSRC).values])["f1"]); rows.append(r)
    print("C", mn, flush=True)
C = pd.DataFrame(rows); C.to_csv(OUT / "C_pooled.csv", index=False)

# soft-vote ensemble of the best-by-validation models
RV = va.source.isin(REALSRC).values
vf = {mn: metrics(probs[mn][0][RV], va.label.values[RV])["f1"] for mn in MODELS}
top = sorted(vf, key=vf.get, reverse=True)[:3]
pv_e = np.mean([probs[m][0] for m in top], 0); pt_e = np.mean([probs[m][1] for m in top], 0)
rows = []
for s in SRC + ["REAL", "ALL"]:
    mk = te.source.isin(REALSRC).values if s == "REAL" else ((te.source == s).values if s != "ALL" else np.ones(len(te), bool))
    r = metrics(pt_e[mk], te.label.values[mk]); r.update(corpus=s, model="ensemble(" + ",".join(top) + ")"); rows.append(r)
pd.DataFrame(rows).to_csv(OUT / "C_ensemble.csv", index=False)

# (E) operating threshold: lowest FPR-constrained threshold on validation (FPR<=1% on REAL ham), applied to test
best = top[0]; pv, pt = probs[best]
mv = va.source.isin(REALSRC).values; yv = va.label.values
ths = np.linspace(.05, .95, 91)
def fpr_at(p, y, t): return ((p >= t) & (y == 0)).sum() / max(1, (y == 0).sum())
ok = [t for t in ths if fpr_at(pv[mv], yv[mv], t) <= .01]
thr = float(min(ok)) if ok else .5
mk = te.source.isin(REALSRC).values
rows = [dict(thr=t, **metrics(pt[mk], te.label.values[mk], t)) for t in (.5, thr)]
pd.DataFrame(rows).to_csv(OUT / "E_threshold.csv", index=False); json.dump({"model": best, "thr": thr, "ensemble_top": top}, open(OUT / "app_model.json", "w"))

# (D) obfuscation robustness on REAL test messages (targeted: spam only is obfuscated; 3 seeds)
rows = []
tr_ = te[te.source.isin(REALSRC)].reset_index(drop=True)
for mn in ["word_lr", "char_lr", "char_lr+norm", "union_lr+norm"]:
    for lv in range(5):
        for sd in range(3 if lv else 1):
            X = [obfuscate(t, lv, "en", seed=sd * 100003 + i) if (l == 1 and lv) else t for i, (t, l) in enumerate(zip(tr_.text, tr_.label))]
            p = fitted[mn].predict_proba(X)[:, 1]; r = metrics(p, tr_.label.values); r.update(model=mn, level=lv, seed=sd); rows.append(r)
    print("D", mn, flush=True)
pd.DataFrame(rows).groupby(["model", "level"]).mean(numeric_only=True).reset_index().drop(columns="seed").to_csv(OUT / "D_obfuscation_real.csv", index=False)

# per-corpus error examples (for the paper's error analysis)
pe = pt_e; te2 = te.assign(p=pe)
fp = te2[(te2.label == 0) & (te2.p > .5) & te2.source.isin(REALSRC)].sort_values("p", ascending=False).head(8)
fn = te2[(te2.label == 1) & (te2.p < .5) & te2.source.isin(REALSRC)].sort_values("p").head(8)
pd.concat([fp.assign(kind="false_positive"), fn.assign(kind="false_negative")])[["kind", "source", "p", "text"]].to_csv(OUT / "errors.csv", index=False)

# final app model = best pooled recipe retrained on ALL data (train+val+test) for shipping
full = df
final = build(best).fit(full.text.tolist(), full.label.values)
(ROOT / "artifacts").mkdir(exist_ok=True); joblib.dump(final, ROOT / "artifacts" / "spam_final.joblib")
print("done", top, thr)
