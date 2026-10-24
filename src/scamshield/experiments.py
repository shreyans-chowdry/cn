"""
Experiment pipeline.

  python -m scamshield.experiments prepare      # dataset + cached obfuscated test suites
  python -m scamshield.experiments main         # E1 obfuscation robustness, E3 adversarial training, E5 normalisation defence
  python -m scamshield.experiments xling        # E2 cross-lingual transfer (single-source matrix)
  python -m scamshield.experiments latency      # E4 inference latency / model size
  python -m scamshield.experiments analyze      # tables, figures, hypothesis tests -> results/

Every run is cached under results/runs/, so the pipeline can be stopped and resumed.
"""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from .data.generator import generate
from .data.templates import LANGS
from .metrics import LABELS, all_metrics
from .obfuscation import obfuscate, normalize, edit_rate, LEVELS

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RES = ROOT / "results"
RUNS = RES / "runs"
ART = ROOT / "artifacts"
LAB = {l: i for i, l in enumerate(LABELS)}

CLASSICAL = ["word_nb", "word_rf", "word_lr", "word_svm", "char_lr", "char_svm"]
NEURAL = ["word_bigru", "char_cnn"]
TRANSFORMERS = ["distil_mbert", "xlmr", "canine", "muril"]
GRANULARITY = {"word_nb": "word", "word_rf": "word", "word_lr": "word", "word_svm": "word",
               "char_lr": "char", "char_svm": "char", "word_bigru": "word", "char_cnn": "char",
               "distil_mbert": "subword", "xlmr": "subword", "muril": "subword", "canine": "char"}
PRETTY = {"word_nb": "Word NB", "word_rf": "Word RF", "word_lr": "Word LR", "word_svm": "Word SVM",
          "char_lr": "Char LR", "char_svm": "Char SVM", "word_bigru": "Word BiGRU", "char_cnn": "Char CNN",
          "distil_mbert": "DistilmBERT", "xlmr": "XLM-R", "muril": "MuRIL", "canine": "CANINE-S"}
THREATS = ["targeted", "uniform"]
TRANSFORMER_TRAIN_FRAC = float(os.environ.get("TRANSFORMER_TRAIN_FRAC", "1.0"))
SAVE_FOR_APP ={"word_lr", "char_lr", "char_svm", "word_bigru", "char_cnn", "distil_mbert"}


# ------------------------------------------------------------------ helpers
def load_df():
    p = DATA / "upi_bisms.csv"
    if not p.exists():
        df = generate()
        df.to_csv(p, index=False)
    return pd.read_csv(p)


def make_model(name, seed=0):
    if name in CLASSICAL:
        from .models import classical
        return classical.make(name, seed)
    if name in NEURAL:
        from .models import neural
        return neural.make(name, seed)
    from .models import transformer
    return transformer.make(name, seed, epochs=1)


def cond_name(level, threat=None, seed=None):
    return "L0" if level == 0 else f"L{level}_{threat}_s{seed}"


def perturb(df, level, threat, seed):
    """Targeted threat: only scam messages are obfuscated (attacker controls scam text).
    Uniform: every message is obfuscated (noisy channel / class-agnostic stress test)."""
    out = []
    for i, (t, lab, lang) in enumerate(zip(df.text, df.label, df.lang)):
        if threat == "targeted" and lab != "scam":
            out.append(t)
        else:
            out.append(obfuscate(t, level, lang, seed=hash((seed, level, i)) & 0xFFFFFFFF))
    return out


def _code_mixing_stats(df):
    from .langid import identify
    out = {}
    for lang, g in df.groupby("lang"):
        ids = [identify(t) for t in g.text]
        out[lang] = {"mean_cmi": float(np.mean([i["cmi"] for i in ids])),
                     "tamil_token_share": float(np.mean([i["shares"]["ta"] + i["shares"]["ta-rom"] for i in ids])),
                     "english_token_share": float(np.mean([i["shares"]["en"] for i in ids])),
                     "detected_as": pd.Series([i["name"] for i in ids]).value_counts().to_dict()}
    return out


# ------------------------------------------------------------------ prepare
def prepare(obf_seeds=(0, 1, 2)):
    df = load_df()
    te = df[df.split == "test"].reset_index(drop=True)
    obf_dir = DATA / "obf"
    obf_dir.mkdir(parents=True, exist_ok=True)
    stats = []
    for lv in range(1, 5):
        for th in THREATS:
            for s in obf_seeds:
                p = obf_dir / f"{cond_name(lv, th, s)}.csv"
                if not p.exists():
                    pd.DataFrame({"id": te.id, "text": perturb(te, lv, th, s)}).to_csv(p, index=False)
        # perturbation statistics on scam messages (uniform, seed 0)
        rng = random.Random(lv)
        ops, er, er_norm, changed = Counter(), [], [], []
        for t, lang in zip(te.text[:1500], te.lang[:1500]):
            o, applied = obfuscate(t, lv, lang, rng=rng, return_ops=True)
            ops.update(applied)
            er.append(edit_rate(t, o))
            er_norm.append(edit_rate(normalize(t), normalize(o)))
            changed.append(sum(a != b for a, b in zip(t.split(), o.split())) / max(len(t.split()), 1))
        stats.append({"level": lv, "name": LEVELS[lv]["name"], "word_prob": LEVELS[lv]["p"],
                      "char_edit_rate": float(np.mean(er)), "char_edit_rate_after_norm": float(np.mean(er_norm)),
                      "words_changed": float(np.mean(changed)), "ops": dict(ops.most_common())})
    # adversarial-training set: 50% of training messages replaced by an L1-L3 obfuscated copy
    tr = df[df.split == "train"].reset_index(drop=True)
    rng = random.Random(99)
    adv = []
    for i, (t, lang) in enumerate(zip(tr.text, tr.lang)):
        adv.append(obfuscate(t, rng.choice([1, 2, 3]), lang, seed=10_000 + i) if rng.random() < 0.5 else t)
    tr_adv = tr.copy()
    tr_adv["text"] = adv
    tr_adv.to_csv(DATA / "train_adv.csv", index=False)
    RES.mkdir(exist_ok=True)
    json.dump(stats, open(RES / "perturbation_stats.json", "w"), indent=2, ensure_ascii=False)
    # dataset statistics
    ds = {"n_total": len(df), "by_split": df.split.value_counts().to_dict(),
          "by_label": df.label.value_counts().to_dict(),
          "by_lang_label": {f"{a}|{b}": int(v) for (a, b), v in df.groupby(["lang", "label"]).size().items()},
          "by_subtype": df.groupby(["label", "subtype"]).size().reset_index().values.tolist(),
          "code_mixing": _code_mixing_stats(df),
          "n_templates": int(df.template_id.nunique() * len(LANGS)),
          "mean_chars": float(df.text.str.len().mean()), "mean_words": float(df.text.str.split().str.len().mean())}
    json.dump(ds, open(RES / "dataset_stats.json", "w"), indent=2)
    print(json.dumps(stats, indent=1, ensure_ascii=False)[:1500])
    print(json.dumps(ds, indent=1)[:800])


def eval_suite(obf_seeds):
    df = load_df()
    te = df[df.split == "test"].reset_index(drop=True)
    suite = {"L0": te.text.tolist()}
    for lv in range(1, 5):
        for th in THREATS:
            for s in obf_seeds:
                c = cond_name(lv, th, s)
                suite[c] = pd.read_csv(DATA / "obf" / f"{c}.csv").text.fillna("").tolist()
    return te, suite


# ------------------------------------------------------------------ core run
def run(exp, model_name, regime, train_df, val_df, suite, y_test, seed=0, save_model=False):
    tag = f"{model_name}__{regime}__seed{seed}"
    out_dir = RUNS / exp
    out_dir.mkdir(parents=True, exist_ok=True)
    jpath, npath = out_dir / f"{tag}.json", out_dir / f"{tag}.npz"
    if jpath.exists() and npath.exists():
        print(f"[skip] {exp}/{tag}")
        return json.load(open(jpath))
    if model_name in TRANSFORMERS and TRANSFORMER_TRAIN_FRAC < 1.0:
        # compute budget: fine-tune on a stratified subset (every template x language kept)
        train_df = (train_df.groupby(["template_id", "lang"], group_keys=False)
                    .apply(lambda g: g.sample(frac=TRANSFORMER_TRAIN_FRAC, random_state=seed)))
        val_df = val_df.sample(min(len(val_df), 600), random_state=seed)
    if model_name in TRANSFORMERS:
        # compute budget on CPU: transformers are evaluated on obfuscation seed 0 only
        suite = {k: v for k, v in suite.items() if k == "L0" or k.endswith("_s0") or not k.startswith("L")}
    print(f"[run] {exp}/{tag}  train={len(train_df)}", flush=True)
    norm = regime == "norm"
    prep = (lambda xs: [normalize(x) for x in xs]) if norm else (lambda xs: list(xs))
    m = make_model(model_name, seed)
    t0 = time.time()
    m.fit(prep(train_df.text), train_df.label.map(LAB).values,
          prep(val_df.text), val_df.label.map(LAB).values, seed=seed)
    train_s = time.time() - t0
    rec = {"exp": exp, "model": model_name, "regime": regime, "seed": seed, "train_seconds": train_s,
           "granularity": GRANULARITY[model_name], "n_train": len(train_df), "metrics": {}}
    arrays = {}
    for cname, texts in suite.items():
        t1 = time.time()
        probs = m.predict_proba(prep(texts))
        yt = y_test[cname] if isinstance(y_test, dict) else y_test
        mets = all_metrics(probs, yt)
        mets["seconds"] = time.time() - t1
        rec["metrics"][cname] = mets
        arrays[cname] = probs.astype(np.float16)
        print(f"   {cname:22s} F1={mets['macro_f1']:.4f} FNR={mets['fnr_scam']:.4f} ECE={mets['ece']:.4f}", flush=True)
    np.savez_compressed(npath, **arrays)
    json.dump(rec, open(jpath, "w"), indent=1)
    if save_model and model_name in SAVE_FOR_APP:
        ART.mkdir(exist_ok=True)
        ext = {"classical": ".joblib", "neural": ".pt", "transformer": ""}[m.family]
        m.save(str(ART / f"{model_name}__{regime}{ext}"))
    return rec


def stage_main(models, regimes, obf_seeds, neural_seeds):
    df = load_df()
    tr, va = df[df.split == "train"], df[df.split == "val"]
    tr_adv = pd.read_csv(DATA / "train_adv.csv")
    te, suite = eval_suite(obf_seeds)
    y = te.label.map(LAB).values
    for name in models:
        seeds = neural_seeds if name in NEURAL else [0]
        for regime in regimes:
            if regime == "norm" and name not in CLASSICAL + NEURAL:
                continue
            for s in seeds:
                run("main", name, regime, tr_adv if regime == "adv" else tr, va, suite, y, seed=s,
                    save_model=(s == seeds[0] and regime in ("clean", "adv")))


def stage_xling(models):
    """Single-source transfer: train on one language pair, test on every language pair (clean + L2 targeted)."""
    df = load_df()
    te = df[df.split == "test"].reset_index(drop=True)
    l2 = pd.read_csv(DATA / "obf" / f"{cond_name(2, 'targeted', 0)}.csv").text.tolist()
    suite, ys = {}, {}
    for tgt in LANGS:
        m = (te.lang == tgt).values
        suite[f"{tgt}_L0"] = te.text[m].tolist()
        suite[f"{tgt}_L2"] = [t for t, k in zip(l2, m) if k]
        ys[f"{tgt}_L0"] = ys[f"{tgt}_L2"] = te.label[m].map(LAB).values
    for name in models:
        for src in LANGS:
            tr = df[(df.split == "train") & (df.lang == src)]
            va = df[(df.split == "val") & (df.lang == src)]
            run("xling", name, f"src-{src}", tr, va, suite, ys, seed=0)


_CUE_PATTERNS = [
    (re.compile(r"(https?://|www\.)?[\w\-]+(\.[\w\-]+)*\.(com|in|xyz|top|online|info|live|site|net|co|click|support|ly|gd|me|it|sbi)(/[\w\-]*)?", re.I), " <url> "),
    (re.compile(r"[\w.\-]+@[a-z]+", re.I), " <upi> "),
    (re.compile(r"(\+91[\s\-]?)?\b[6-9]\d{4}\s?\d{5}\b|\b1[89]60?0?-\d{3}-\d{4}\b"), " <phone> "),
    (re.compile(r"(rs\.?|inr|\u20b9)\s?[\d,]+(\.\d+)?(/-)?", re.I), " <amt> "),
    (re.compile(r"\b[A-Z]{2}-[A-Z]{6}:\s?"), " "),
    (re.compile(r"\d+"), " <num> "),
]


def mask_cues(text):
    """Replace non-linguistic cues (URLs, UPI IDs, phone numbers, amounts, sender headers, numbers) by
    placeholders, so a model must rely on the message language itself."""
    for pat, rep in _CUE_PATTERNS:
        text = pat.sub(rep, text)
    return re.sub(r"\s+", " ", text).strip()


def stage_cues(models, obf_seeds):
    """Cue ablation: train and test with URLs / phone numbers / UPI IDs / amounts masked."""
    df = load_df()
    tr, va = df[df.split == "train"].copy(), df[df.split == "val"].copy()
    tr["text"] = tr.text.map(mask_cues)
    va["text"] = va.text.map(mask_cues)
    te, suite = eval_suite(obf_seeds[:1])
    suite = {k: [mask_cues(t) for t in v] for k, v in suite.items() if k == "L0" or "targeted" in k}
    y = te.label.map(LAB).values
    for name in models:
        run("cues", name, "masked", tr, va, suite, y, seed=0)


def stage_external():
    """External validity with real public corpora (Ayushmaan's datasets) and the link-intelligence ablation.

    Three training recipes, all with the production model family (char 2-5-gram LR on canonicalised text):
      bisms_only   UPI-BiSMS train+val
      public_only  Mishra & Soni (3-class) + UCI/ExAIS genuine messages, train portions
      joint        both
    Tested on the UPI-BiSMS test set (3-class, per language) and on held-out public messages
    (binary: genuine vs unwanted), plus the machine-translated multilingual UCI as a stress test."""
    import sys as _s
    _s.path.insert(0, str(ROOT / "scripts"))
    from train_production import build_pipeline
    from .data import public as PUB
    from .net import urlintel
    out_dir = RES / "external"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_df()
    btr, bte = df[df.split != "test"], df[df.split == "test"]
    pub = PUB.load_public()
    ptr, pte = PUB.grouped_split(pub, 0.2, seed=0)
    ptr3 = ptr[ptr.label3.isin(LABELS)]
    hf = PUB.load_hf_multi()
    hf = hf[hf.group.isin(set(pte.group))]          # only translations of held-out messages (no leakage)
    hf = pd.concat([g.sample(min(len(g), 600), random_state=0) for _, g in hf.groupby("lang")], ignore_index=True)
    hf["binary"] = hf.label3.ne("legit").astype(int)
    recipes = {"bisms_only": (list(btr.text), list(btr.label)),
               "public_only": (list(ptr3.text), list(ptr3.label3)),
               "joint": (list(btr.text) + list(ptr3.text), list(btr.label) + list(ptr3.label3))}
    rows, fusion_rows = [], []
    for name, (X, y) in recipes.items():
        print(f"[external] {name}: {len(X)} training messages", flush=True)
        pipe = build_pipeline().fit(X, y)
        order = [list(pipe.classes_).index(c) for c in LABELS]
        for lang in LANGS:
            g = bte[bte.lang == lang]
            m = all_metrics(pipe.predict_proba(g.text.tolist())[:, order], g.label.map(LAB).values)
            rows.append({"train": name, "test": f"UPI-BiSMS ({lang})", "n": len(g), "macro_f1": m["macro_f1"],
                         "scam_fnr": m["fnr_scam"], "scam_fpr": m["fpr_scam"], "ece": m["ece"]})
        tests = [(f"{s} (held out)", g) for s, g in pte.groupby("source")] + \
                [(f"hf_multi:{lg}", g) for lg, g in hf.groupby("lang")]
        for tname, g in tests:
            p = pipe.predict_proba(g.text.tolist())[:, order]
            pred = (p[:, LAB["legit"]] < 0.5).astype(int)
            yb = g.binary.values
            row = {"train": name, "test": tname, "n": len(g),
                   "binary_macro_f1": f1_score(yb, pred, average="macro"),
                   "unwanted_recall": float(pred[yb == 1].mean()) if (yb == 1).any() else np.nan,
                   "genuine_fpr": float(pred[yb == 0].mean()) if (yb == 0).any() else np.nan}
            if g.label3.isin(LABELS).all():
                m = all_metrics(p, g.label3.map(LAB).values)
                row.update({"macro_f1": m["macro_f1"], "scam_fnr": m["fnr_scam"], "scam_fpr": m["fpr_scam"], "ece": m["ece"]})
            rows.append(row)
        if name == "joint":
            # link-intelligence ablation (lexical URL features only: synthetic and 2010s domains do not resolve today)
            for tname, g, ycol in [("UPI-BiSMS test", bte, "label"), ("mishra_soni (held out)", pte[pte.source == "mishra_soni"], "label3")]:
                p = pipe.predict_proba(g.text.tolist())[:, order]
                risk = np.array([urlintel.analyse(t)["risk"] for t in g.text])
                y3 = g[ycol].map(LAB).values
                for variant, pp in (("text only", p), ("text + link intelligence", _fuse(p, risk))):
                    m = all_metrics(pp, y3)
                    fusion_rows.append({"test": tname, "variant": variant, "n": len(g), "with_link": int((risk > 0).sum()),
                                        "macro_f1": m["macro_f1"], "scam_fnr": m["fnr_scam"], "scam_fpr": m["fpr_scam"]})
    pd.DataFrame(rows).to_csv(TAB_DIR() / "table13_external.csv", index=False)
    pd.DataFrame(fusion_rows).to_csv(TAB_DIR() / "table14_link_fusion.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print(pd.DataFrame(fusion_rows).round(3).to_string(index=False))


def _fuse(p, risk, w=0.6):
    """Same fusion rule as scamshield.detector, vectorised. p columns follow LABELS."""
    p = p.copy()
    si = LAB["scam"]
    ps = 1 - (1 - p[:, si]) * (1 - w * risk)
    rest = np.clip(1 - p[:, si], 1e-9, None)
    for c in (LAB["legit"], LAB["promo"]):
        p[:, c] = p[:, c] * (1 - ps) / rest
    p[:, si] = ps
    return p


def TAB_DIR():
    d = RES / "tables"
    d.mkdir(parents=True, exist_ok=True)
    return d


def stage_network():
    from .net.experiments import run_all
    run_all(RES)


def stage_latency(models, n=200):
    df = load_df()
    te = df[df.split == "test"].sample(n, random_state=0).text.tolist()
    tr, va = df[df.split == "train"], df[df.split == "val"]
    out = {}
    p = RES / "latency.json"
    if p.exists():
        out = json.load(open(p))
    for name in models:
        if name in out:
            continue
        m = make_model(name)
        art = ART / f"{name}__clean"
        if name in CLASSICAL and art.with_suffix(".joblib").exists():
            m.load(str(art.with_suffix(".joblib")))
        elif name in NEURAL and art.with_suffix(".pt").exists():
            m.load(str(art.with_suffix(".pt")))
        elif name in TRANSFORMERS:
            from transformers import AutoModelForSequenceClassification
            m.net = AutoModelForSequenceClassification.from_pretrained(m.hf_id, num_labels=3).to(m.device).eval()
        else:
            m.fit(tr.text, tr.label.map(LAB).values, va.text, va.label.map(LAB).values)
        for t in te[:10]:
            m.predict_proba([t])
        single = []
        for t in te:
            t0 = time.perf_counter()
            m.predict_proba([t])
            single.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        m.predict_proba(te)
        batch_tp = n / (time.perf_counter() - t0)
        size = None
        try:
            size = int(m.n_params())
        except Exception:
            pass
        out[name] = {"median_ms": float(np.median(single)), "p95_ms": float(np.percentile(single, 95)),
                     "throughput_msgs_per_s": float(batch_tp), "n_params": size}
        print(name, out[name], flush=True)
        json.dump(out, open(p, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["prepare", "main", "xling", "cues", "external", "network", "latency", "analyze", "all"])
    ap.add_argument("--models", default=",".join(CLASSICAL + NEURAL + TRANSFORMERS))
    ap.add_argument("--regimes", default="clean,adv,norm")
    ap.add_argument("--obf-seeds", default="0,1,2")
    ap.add_argument("--neural-seeds", default="0,1,2")
    a = ap.parse_args()
    models = [m for m in a.models.split(",") if m]
    obf_seeds = [int(s) for s in a.obf_seeds.split(",")]
    if a.stage in ("prepare", "all"):
        prepare(tuple(obf_seeds))
    if a.stage in ("main", "all"):
        stage_main(models, a.regimes.split(","), obf_seeds, [int(s) for s in a.neural_seeds.split(",")])
    if a.stage in ("xling", "all"):
        stage_xling(models)
    if a.stage in ("cues", "all"):
        stage_cues(models, obf_seeds)
    if a.stage in ("external", "all"):
        stage_external()
    if a.stage in ("network", "all"):
        stage_network()
    if a.stage in ("latency", "all"):
        stage_latency(models)
    if a.stage in ("analyze", "all"):
        from .analysis import analyze
        analyze()


if __name__ == "__main__":
    main()
