"""Train a character n-gram spam/scam classifier on several public + project corpora and evaluate it
honestly. Run from the Project folder:   python scripts/train_public.py [--balance]
Sources used (whatever is present): hf_multi (22 languages, translated UCI), mishra_soni (if downloaded),
upi_cmx (code-mixed Indian scams). All translations of one message stay on the same side of the split."""
import sys, time
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from scamshield.obfuscation import normalize
import public_datasets as P


def prep(s):
    return normalize(s).lower()


def make_model():
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, max_features=400_000,
                          sublinear_tf=True, preprocessor=prep)
    return make_pipeline(vec, LogisticRegression(C=4.0, max_iter=300, class_weight="balanced", solver="liblinear"))


BALANCE = "--balance" in sys.argv


def fit_model(df):
    """--balance: weight each source by 1/sqrt(its size) so a huge source (translated UCI, 100k rows)
    does not drown out small ones (UPI-CMX, Mishra and Soni)."""
    m = make_model()
    if BALANCE:
        w = 1.0 / np.sqrt(df.groupby("source").text.transform("size").values.astype(float))
        w = w / w.mean()
        return m.fit(df.text, df.label.values, logisticregression__sample_weight=w)
    return m.fit(df.text, df.label.values)


def score(y, p):
    pred = (p >= 0.5).astype(int)
    return dict(n=len(y), spam_rate=round(float(y.mean()), 3), macro_f1=round(f1_score(y, pred, average="macro"), 3),
                spam_recall=round(recall_score(y, pred), 3),
                ham_fpr=round(float(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)), 3),
                auc=round(roc_auc_score(y, p), 3) if 0 < y.mean() < 1 else float("nan"))


def _key(t):
    import re
    return re.sub(r"[^a-z0-9]+", "", str(t).lower())


def drop_cross_source_overlap(srcs):
    """The English parts of the public corpora can share messages (Mishra & Soni vs UCI). Messages that appear in an
    earlier source are removed from later ones so that leave-one-source-out is not leaky."""
    seen = set()
    for name in ("hf_multi", "uci", "mishra_soni"):
        if name not in srcs:
            continue
        d = srcs[name]
        en = d[d.lang == "en"] if "lang" in d else d
        keys = en.text.map(_key)
        if seen:
            dup_keys = set(keys) & seen
            if dup_keys:
                before = d.group.nunique()
                bad_groups = set(en.group[keys.isin(dup_keys)])
                srcs[name] = d[~d.group.isin(bad_groups)].reset_index(drop=True)
                print(f"overlap: removed {len(bad_groups)} of {before} messages from {name} that also occur in an earlier source")
            else:
                print(f"overlap: none found between {name} and earlier sources")
        seen |= set(keys)
    return srcs


def load_sources():
    srcs = {}
    for name, fn in (("hf_multi", P.load_hf_multi), ("mishra_soni", P.load_mishra_soni)):
        try:
            srcs[name] = fn()
        except Exception as e:
            print(f"skipping {name}: {e}")
    if "hf_multi" not in srcs:
        srcs["uci"] = P.load_uci()
    upi = P.load_upi(promo_as_spam=True)
    srcs["upi_cmx"] = upi.drop(columns=["split"])
    return drop_cross_source_overlap(srcs)


def main():
    srcs = load_sources()
    splits = {k: P.grouped_split(v, 0.2, seed=0) for k, v in srcs.items()}
    rows = []

    # 1) one model trained on everything, tested on every source's held-out 20%
    train = pd.concat([tr for tr, _ in splits.values()], ignore_index=True)
    print(f"training on {len(train)} messages from {list(srcs)} ...", flush=True)
    t0 = time.time(); m = fit_model(train); print(f"fit {time.time()-t0:.0f}s")
    for k, (_, te) in splits.items():
        rows.append(dict(experiment="all_sources", test=k, **score(te.label.values, m.predict_proba(te.text)[:, 1])))
        if te.lang.nunique() > 1:
            for lg, g in te.groupby("lang"):
                rows.append(dict(experiment="all_sources_per_language", test=f"{k}:{lg}", **score(g.label.values, m.predict_proba(g.text)[:, 1])))
    ART = ROOT / "artifacts"; ART.mkdir(exist_ok=True)
    joblib.dump(m, ART / ("public_char_lr_balanced.joblib" if BALANCE else "public_char_lr.joblib"))

    # 2) leave-one-source-out: the honest "unseen dataset" test
    for held in srcs:
        others = pd.concat([tr for k, (tr, _) in splits.items() if k != held], ignore_index=True)
        if others.empty: continue
        mm = fit_model(others)
        te = splits[held][1]
        rows.append(dict(experiment="leave_source_out", test=held, **score(te.label.values, mm.predict_proba(te.text)[:, 1])))
        print("held out", held, "done", flush=True)

    out = pd.DataFrame(rows)
    (ROOT / "results/public").mkdir(parents=True, exist_ok=True)
    out.to_csv(ROOT / "results/public/train_public" f"{'_balanced' if BALANCE else ''}.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
