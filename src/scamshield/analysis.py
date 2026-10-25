"""Aggregate cached runs into tables, figures and hypothesis tests."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data.templates import LANGS, LANG_NAMES

NL = len(LANGS)
from .metrics import LABELS, all_metrics, paired_bootstrap_delta, mcnemar, bootstrap_ci, macro_f1_fn, scam_fnr

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
RUNS = RES / "runs"
FIG = RES / "figures"
TAB = RES / "tables"
LAB = {l: i for i, l in enumerate(LABELS)}

ORDER = ["word_nb", "word_rf", "word_lr", "word_svm", "word_bigru", "distil_mbert", "xlmr", "muril",
         "char_lr", "char_svm", "char_cnn", "canine"]
PRETTY = {"word_nb": "Word NB", "word_rf": "Word RF", "word_lr": "Word LR", "word_svm": "Word SVM",
          "char_lr": "Char LR", "char_svm": "Char SVM", "word_bigru": "Word BiGRU", "char_cnn": "Char CNN",
          "distil_mbert": "DistilmBERT", "xlmr": "XLM-R", "muril": "MuRIL", "canine": "CANINE-S"}
GRAN = {"word_nb": "word", "word_rf": "word", "word_lr": "word", "word_svm": "word", "word_bigru": "word",
        "char_lr": "char", "char_svm": "char", "char_cnn": "char", "canine": "char",
        "distil_mbert": "subword", "xlmr": "subword", "muril": "subword"}
# reference categorical palette, slots 1-3 (validated all-pairs)
GCOL = {"word": "#2a78d6", "char": "#eb6834", "subword": "#1baf7a"}
MARK = {"word_nb": "v", "word_rf": "P", "word_lr": "o", "word_svm": "s", "word_bigru": "D",
        "char_lr": "o", "char_svm": "s", "char_cnn": "D", "canine": "^",
        "distil_mbert": "o", "xlmr": "s", "muril": "D"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
PAIRS = [("char_lr", "word_lr"), ("char_svm", "word_svm"), ("char_cnn", "word_bigru"), ("canine", "muril"),
         ("canine", "distil_mbert"), ("canine", "xlmr"), ("char_lr", "xlmr"), ("char_lr", "muril"),
         ("char_lr", "distil_mbert")]


def _ensure_runs():
    """Raw runs ship as results/runs.zip; unpack on first use."""
    z = RES / "runs.zip"
    if not RUNS.exists() and z.exists():
        import zipfile
        zipfile.ZipFile(z).extractall(RES)


def _load(exp):
    _ensure_runs()
    recs = []
    for p in sorted((RUNS / exp).glob("*.json")):
        r = json.load(open(p))
        r["_npz"] = str(p.with_suffix(".npz"))
        recs.append(r)
    return recs


def _long(recs):
    rows = []
    for r in recs:
        for c, m in r["metrics"].items():
            lv, th, s = (0, "none", 0) if c == "L0" else (int(c[1]), c.split("_")[1], int(c.split("_s")[-1]))
            rows.append({"model": r["model"], "regime": r["regime"], "seed": r["seed"], "cond": c, "level": lv,
                         "threat": th, "obf_seed": s, **{k: v for k, v in m.items() if k != "confusion"}})
    return pd.DataFrame(rows)


def _fmt(m, s=None, d=3):
    return f"{m:.{d}f}" if s is None or np.isnan(s) or s == 0 else f"{m:.{d}f} ± {s:.{d}f}"


def _md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _curve(L, regime, threat, metric):
    """mean/std over obfuscation seeds and training seeds, per model x level."""
    d = L[(L.regime == regime) & ((L.threat == threat) | (L.level == 0))]
    g = d.groupby(["model", "level"])[metric].agg(["mean", "std"]).reset_index()
    return g


def _size(m, lat):
    if m not in lat or not lat[m].get("n_params"):
        return "-"
    n = lat[m]["n_params"]
    if m in ("word_nb", "word_rf", "word_lr", "word_svm", "char_lr", "char_svm"):
        return f"{n / 1e3:.1f}k features"
    return f"{n / 1e6:.1f}M params"


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8.5)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def analyze():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.labelcolor": INK2,
                         "axes.titlesize": 10, "axes.titlecolor": INK})
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "data" / "upi_mixsms.csv")
    te = df[df.split == "test"].reset_index(drop=True)
    y = te.label.map(LAB).values
    lang = te.lang.values

    recs = _load("main")
    L = _long(recs)
    models = [m for m in ORDER if m in set(L.model)]
    summary = {"models": models}
    md = ["# Results\n", "All numbers on the template-disjoint test set "
          f"(n = {len(te)}). Obfuscated conditions are averaged over obfuscation seeds; "
          "from-scratch neural models are additionally averaged over training seeds (mean ± std).\n"]
    lat = json.load(open(RES / "latency.json")) if (RES / "latency.json").exists() else {}
    pstats = json.load(open(RES / "perturbation_stats.json")) if (RES / "perturbation_stats.json").exists() else []

    # ---------------- Table 1: clean performance
    rows = []
    for m in models:
        d = L[(L.model == m) & (L.regime == "clean") & (L.level == 0)]
        r0 = [r for r in recs if r["model"] == m and r["regime"] == "clean"][0]
        p = np.load(r0["_npz"])["L0"].astype(np.float32).argmax(1)
        lo, hi = bootstrap_ci(y, p, macro_f1_fn, n=500)
        rows.append({"Model": PRETTY[m], "Repr.": GRAN[m],
                     "Macro-F1": _fmt(d.macro_f1.mean(), d.macro_f1.std()), "95% CI (seed 0)": f"[{lo:.3f}, {hi:.3f}]",
                     "Scam FNR": _fmt(d.fnr_scam.mean()), "Scam FPR": _fmt(d.fpr_scam.mean()),
                     "ECE": _fmt(d.ece.mean()),
                     "Latency ms (p50)": f"{lat[m]['median_ms']:.2f}" if m in lat else "-",
                     "Size": _size(m, lat)})
    t1 = pd.DataFrame(rows)
    t1.to_csv(TAB / "table1_clean.csv", index=False)
    md += ["## Table 1 — Clean test performance (no obfuscation)\n", _md(t1), ""]

    # ---------------- Table 2/3: robustness curves
    for metric, title, fname in [("macro_f1", "Macro-F1", "table2_f1_vs_level"),
                                 ("fnr_scam", "Scam false-negative rate", "table3_fnr_vs_level"),
                                 ("fpr_scam", "Scam false-positive rate (genuine/promo flagged as scam)", "table3b_fpr_vs_level"),
                                 ("ece", "Expected calibration error", "table4_ece_vs_level")]:
        # scam FNR is identical under both threats by construction (scam messages get the same perturbation)
        # FPR only moves under the uniform threat (genuine messages are untouched in the targeted one)
        for threat in {"fnr_scam": ["targeted"], "fpr_scam": ["uniform"]}.get(metric, ["targeted", "uniform"]):
            g = _curve(L, "clean", threat, metric)
            rows = []
            for m in models:
                gm = g[g.model == m].set_index("level")
                row = {"Model": PRETTY[m], "Repr.": GRAN[m]}
                for lv in range(5):
                    if lv in gm.index:
                        row[f"L{lv}"] = _fmt(gm.loc[lv, "mean"], gm.loc[lv, "std"] if lv else None)
                if metric == "macro_f1" and 0 in gm.index and 4 in gm.index:
                    row["Mean L0-L4"] = f"{gm['mean'].mean():.3f}"
                    row["Drop L0→L3"] = f"{gm.loc[0, 'mean'] - gm.loc[3, 'mean']:.3f}"
                    row["Drop L0→L4"] = f"{gm.loc[0, 'mean'] - gm.loc[4, 'mean']:.3f}"
                rows.append(row)
            t = pd.DataFrame(rows)
            t.to_csv(TAB / f"{fname}_{threat}.csv", index=False)
            md += [f"## {title} vs. obfuscation level — {threat} threat model (clean training)\n", _md(t), ""]

    # ---------------- Figure 1/2: F1 & FNR curves
    TITLE = {"targeted": "Targeted (scam-only) obfuscation", "uniform": "Uniform (all messages) obfuscation"}
    FIGS = [("fig1_f1_vs_obfuscation", [("targeted", "macro_f1", "Macro-F1"), ("uniform", "macro_f1", None)]),
            # scam FNR is identical under both threats, so the second panel shows the FPR under the uniform threat
            ("fig2_fnr_vs_obfuscation", [("targeted", "fnr_scam", "Scam false-negative rate"),
                                         ("uniform", "fpr_scam", "Scam false-positive rate")]),
            ("fig3_ece_vs_obfuscation", [("targeted", "ece", "Expected calibration error"), ("uniform", "ece", None)])]
    for fname, panels in FIGS:
        share = panels[1][2] is None
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), sharey=share)
        for ax, (threat, metric, ylab) in zip(axes, panels):
            g = _curve(L, "clean", threat, metric)
            for m in models:
                gm = g[g.model == m].sort_values("level")
                ax.plot(gm.level, gm["mean"], color=GCOL[GRAN[m]], marker=MARK[m], ms=6, lw=2,
                        ls="-" if GRAN[m] != "word" else (0, (4, 2)), label=PRETTY[m],
                        markeredgecolor="white", markeredgewidth=1)
            ax.set_xticks(range(5))
            ax.set_xticklabels(["L0\nclean", "L1\nlight", "L2\nmoderate", "L3\nheavy", "L4\ncross-script"])
            ax.set_title(TITLE[threat], loc="left")
            if ylab:
                ax.set_ylabel(ylab)
            _style(ax)
        h, l = axes[0].get_legend_handles_labels()
        fig.legend(h, l, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=8.5,
                   title="blue = word · orange = char · green = subword", title_fontsize=7.5)
        fig.tight_layout()
        fig.savefig(FIG / f"{fname}.png", dpi=200, bbox_inches="tight")
        fig.savefig(FIG / f"{fname}.pdf", bbox_inches="tight")
        plt.close(fig)

    # ---------------- Hypothesis tests: char vs word degradation (targeted & uniform, seed 0)
    tests = []
    for a, b in PAIRS:
        ra = [r for r in recs if r["model"] == a and r["regime"] == "clean" and r["seed"] == 0]
        rb = [r for r in recs if r["model"] == b and r["regime"] == "clean" and r["seed"] == 0]
        if not ra or not rb:
            continue
        za, zb = np.load(ra[0]["_npz"]), np.load(rb[0]["_npz"])
        pa0, pb0 = za["L0"].astype(np.float32).argmax(1), zb["L0"].astype(np.float32).argmax(1)
        for threat in ["targeted", "uniform"]:
            for lv in (3, 4):
                c = f"L{lv}_{threat}_s0"
                pa, pb = za[c].astype(np.float32).argmax(1), zb[c].astype(np.float32).argmax(1)
                res = paired_bootstrap_delta(y, pa0, pa, pb0, pb, n=1000)
                mc = mcnemar(y, pa, pb)
                tests.append({"A (char)": PRETTY[a], "B (word/subword)": PRETTY[b], "threat": threat, "level": f"L{lv}",
                              "drop A": round(macro_f1_fn(y, pa0) - macro_f1_fn(y, pa), 4),
                              "drop B": round(macro_f1_fn(y, pb0) - macro_f1_fn(y, pb), 4),
                              "Δdrop (A−B)": round(res["delta_mean"], 4),
                              "95% CI": f"[{res['ci95'][0]:.3f}, {res['ci95'][1]:.3f}]",
                              "p (A degrades less)": round(res["p_one_sided"], 4),
                              "McNemar p (attacked)": f"{mc['p_value']:.2e}"})
    tt = pd.DataFrame(tests)
    if len(tt):
        tt.to_csv(TAB / "table5_hypothesis_tests.csv", index=False)
        md += ["## Hypothesis test — do character-level models degrade less than word/subword models?\n",
               "Paired bootstrap (1000 resamples) over test messages on the *drop* in macro-F1 from L0 to the attacked "
               "condition. Negative Δdrop means the character model loses less. One-sided p-value for H1: A degrades less than B.\n",
               _md(tt), ""]
    summary["hypothesis_tests"] = tests

    # ---------------- Adversarial training
    rows, adv_gain = [], []
    for m in models:
        row = {"Model": PRETTY[m], "Repr.": GRAN[m]}
        for regime in ["clean", "adv"]:
            g = _curve(L, regime, "targeted", "macro_f1").query("model == @m").set_index("level")
            gf = _curve(L, regime, "targeted", "fnr_scam").query("model == @m").set_index("level")
            if g.empty:
                continue
            tag = "std" if regime == "clean" else "AT"
            for lv in (0, 3, 4):
                row[f"F1 L{lv} ({tag})"] = f"{g.loc[lv, 'mean']:.3f}"
            row[f"FNR L3 ({tag})"] = f"{gf.loc[3, 'mean']:.3f}"
        if any(k.endswith("(AT)") for k in row):
            rows.append(row)
            gc = _curve(L, "clean", "targeted", "macro_f1").query("model == @m").set_index("level")["mean"]
            ga = _curve(L, "adv", "targeted", "macro_f1").query("model == @m").set_index("level")["mean"]
            adv_gain.append((m, [ga.get(lv, np.nan) - gc.get(lv, np.nan) for lv in range(5)]))
    ta = pd.DataFrame(rows)
    ta.to_csv(TAB / "table6_adversarial_training.csv", index=False)
    md += ["## Adversarial training (train on 50% L1–L3 obfuscated copies; L4 cross-script transliteration never seen) — targeted threat\n",
           _md(ta), ""]
    if adv_gain:
        fig, ax = plt.subplots(figsize=(8.5, 3.6))
        w = 0.8 / 5
        x = np.arange(len(adv_gain))
        seq = ["#cde2fb", "#9ec5f4", "#6aa5ea", "#2a78d6", "#1a4f93"]
        for lv in range(5):
            vals = [g[1][lv] for g in adv_gain]
            ax.bar(x + (lv - 2) * w, vals, w * 0.92, color=seq[lv], label=f"L{lv}" + (" (unseen)" if lv == 4 else ""))
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([PRETTY[g[0]] for g in adv_gain], rotation=30, ha="right")
        ax.set_ylabel("Δ macro-F1 (AT − standard)")
        ax.set_title("Effect of adversarial training per obfuscation level (targeted threat)", loc="left")
        _style(ax)
        ax.legend(frameon=False, ncol=5, fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(FIG / "fig4_adversarial_training_gain.png", dpi=200, bbox_inches="tight")
        fig.savefig(FIG / "fig4_adversarial_training_gain.pdf", bbox_inches="tight")
        plt.close(fig)

    # ---------------- Normalisation defence
    rows = []
    for m in models:
        gn = _curve(L, "norm", "targeted", "macro_f1").query("model == @m").set_index("level")
        if gn.empty:
            continue
        gc = _curve(L, "clean", "targeted", "macro_f1").query("model == @m").set_index("level")
        ga = _curve(L, "adv", "targeted", "macro_f1").query("model == @m").set_index("level")
        row = {"Model": PRETTY[m]}
        for lv in range(5):
            row[f"L{lv} std"] = f"{gc.loc[lv, 'mean']:.3f}"
            row[f"L{lv} +norm"] = f"{gn.loc[lv, 'mean']:.3f}"
            if not ga.empty:
                row[f"L{lv} AT"] = f"{ga.loc[lv, 'mean']:.3f}"
        rows.append(row)
    if rows:
        tn = pd.DataFrame(rows)
        tn.to_csv(TAB / "table7_normalisation_defence.csv", index=False)
        md += ["## Script-aware canonicalisation defence (NFKC, homoglyph and native look-alike folding, zero-width stripping, de-leet, native-script loanwords to English) vs adversarial training — macro-F1, targeted\n",
               _md(tn), ""]

    # ---------------- Per-language robustness (clean training, targeted, seed-0 run)
    rows = []
    for m in models:
        r = [r for r in recs if r["model"] == m and r["regime"] == "clean" and r["seed"] == 0][0]
        z = np.load(r["_npz"])
        row = {"Model": PRETTY[m]}
        for lg in LANGS:
            k = lang == lg
            f0 = macro_f1_fn(y[k], z["L0"].astype(np.float32).argmax(1)[k])
            f3 = np.mean([macro_f1_fn(y[k], z[c].astype(np.float32).argmax(1)[k])
                          for c in z.files if c.startswith("L3_targeted")])
            row[f"{lg} L0"] = f"{f0:.3f}"
            row[f"{lg} L3"] = f"{f3:.3f}"
        rows.append(row)
    tl = pd.DataFrame(rows)
    tl.to_csv(TAB / "table8_per_language.csv", index=False)
    md += ["## Per-language macro-F1, clean (L0) vs heavy targeted obfuscation (L3)\n",
           "Languages: " + ", ".join(f"{k} = {v}" for k, v in LANG_NAMES.items()) + "\n", _md(tl), ""]

    # ---------------- Cross-lingual transfer
    xr = _load("xling")
    if xr:
        xmodels = [m for m in ORDER if m in {r["model"] for r in xr}]
        rows = []
        fig, axes = plt.subplots(1, len(xmodels), figsize=(2.6 * len(xmodels) + 0.6, 2.9), squeeze=False)
        for ax, m in zip(axes[0], xmodels):
            M = np.full((NL, NL), np.nan)
            M2 = np.full((NL, NL), np.nan)
            for r in xr:
                if r["model"] != m:
                    continue
                i = LANGS.index(r["regime"].split("-")[1])
                for j, tg in enumerate(LANGS):
                    M[i, j] = r["metrics"][f"{tg}_L0"]["macro_f1"]
                    M2[i, j] = r["metrics"][f"{tg}_L2"]["macro_f1"]
            diag = np.nanmean(np.diag(M))
            off = np.nanmean(M[~np.eye(NL, dtype=bool)])
            off2 = np.nanmean(M2[~np.eye(NL, dtype=bool)])
            rows.append({"Model": PRETTY[m], "Repr.": GRAN[m], "In-language F1": f"{diag:.3f}",
                         "Cross-language F1": f"{off:.3f}", "Transfer gap": f"{diag - off:.3f}",
                         "In-language F1 @L2": f"{np.nanmean(np.diag(M2)):.3f}",
                         "Cross-language F1 @L2": f"{off2:.3f}"})
            pd.DataFrame(M, index=LANGS, columns=LANGS).to_csv(TAB / f"xling_matrix_{m}.csv")
            im = ax.imshow(M, vmin=0.3, vmax=1.0, cmap="Blues")
            for i in range(NL):
                for j in range(NL):
                    if not np.isnan(M[i, j]):
                        ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=7,
                                color="white" if M[i, j] > 0.72 else INK)
            ax.set_xticks(range(NL)); ax.set_xticklabels(LANGS, fontsize=8)
            ax.set_yticks(range(NL)); ax.set_yticklabels(LANGS, fontsize=8)
            ax.set_title(PRETTY[m], loc="left")
            ax.set_xlabel("test language", fontsize=8)
            for s in ax.spines.values():
                s.set_visible(False)
        axes[0][0].set_ylabel("train language", fontsize=8)
        fig.colorbar(im, ax=axes[0].tolist(), fraction=0.02, pad=0.02, label="macro-F1")
        fig.savefig(FIG / "fig5_crosslingual_transfer.png", dpi=200, bbox_inches="tight")
        fig.savefig(FIG / "fig5_crosslingual_transfer.pdf", bbox_inches="tight")
        plt.close(fig)
        tx = pd.DataFrame(rows)
        tx.to_csv(TAB / "table9_crosslingual.csv", index=False)
        md += ["## Cross-language transfer (train on one language only, test on every language; clean and L2 targeted)\n",
               _md(tx), ""]

    # ---------------- Cue ablation
    cr = _load("cues")
    if cr:
        CL = _long(cr)
        rows = []
        for m in [m for m in ORDER if m in set(CL.model)]:
            gm = CL[CL.model == m].groupby("level")[["macro_f1", "fnr_scam"]].mean()
            g0 = _curve(L, "clean", "targeted", "macro_f1").query("model == @m").set_index("level")["mean"]
            row = {"Model": PRETTY[m], "Repr.": GRAN[m], "F1 L0 (full)": f"{g0.get(0, np.nan):.3f}",
                   "F1 L0 (cues masked)": f"{gm.loc[0, 'macro_f1']:.3f}",
                   "Δ L0": f"{gm.loc[0, 'macro_f1'] - g0.get(0, np.nan):+.3f}",
                   "F1 L3 (full)": f"{g0.get(3, np.nan):.3f}", "F1 L3 (masked)": f"{gm.loc[3, 'macro_f1']:.3f}",
                   "FNR L3 (masked)": f"{gm.loc[3, 'fnr_scam']:.3f}"}
            rows.append(row)
        tc = pd.DataFrame(rows)
        tc.to_csv(TAB / "table11_cue_ablation.csv", index=False)
        md += ["## Cue ablation — URLs, UPI IDs, phone numbers, amounts and numbers replaced by placeholders (train and test), targeted threat\n",
               "Shows how much each model relies on non-linguistic cues rather than the code-mixed text itself.\n",
               _md(tc), ""]

    # ---------------- Latency vs robustness scatter
    if lat:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        g = _curve(L, "clean", "targeted", "macro_f1")
        for m in models:
            if m not in lat:
                continue
            f4 = g[(g.model == m)].groupby("level")["mean"].first()
            ax.scatter(lat[m]["median_ms"], f4.mean(), s=60, color=GCOL[GRAN[m]], marker=MARK[m],
                       edgecolor="white", linewidth=1.5, zorder=3)
            off = {"xlmr": (-6, -12), "distil_mbert": (-20, 8)}.get(m, (5, 3))
            ax.annotate(PRETTY[m], (lat[m]["median_ms"], f4.mean()), xytext=off, textcoords="offset points",
                        ha="right" if m == "xlmr" else "left",
                        fontsize=7.5, color=INK2)
        ax.set_xscale("log")
        ax.set_xlabel("Single-message CPU latency, median (ms, log scale)")
        ax.set_ylabel("Mean macro-F1 across L0–L4")
        ax.set_title("Robustness vs. inference cost (targeted threat)", loc="left")
        _style(ax)
        fig.tight_layout()
        fig.savefig(FIG / "fig6_latency_vs_robustness.png", dpi=200, bbox_inches="tight")
        fig.savefig(FIG / "fig6_latency_vs_robustness.pdf", bbox_inches="tight")
        plt.close(fig)
        rows = [{"Model": PRETTY[m], "Repr.": GRAN[m], "p50 ms": f"{lat[m]['median_ms']:.2f}",
                 "p95 ms": f"{lat[m]['p95_ms']:.2f}", "Batch throughput (msg/s)": f"{lat[m]['throughput_msgs_per_s']:.0f}",
                 "Size": _size(m, lat)}
                for m in models if m in lat]
        tlat = pd.DataFrame(rows)
        tlat.to_csv(TAB / "table10_latency.csv", index=False)
        md += ["## Inference latency (CPU, 2 cores, batch size 1 unless stated)\n", _md(tlat), ""]

    # ---------------- Perturbation statistics
    if pstats:
        tp = pd.DataFrame([{"Level": f"L{p['level']} ({p['name']})", "Word perturb prob.": p["word_prob"],
                            "Words changed": f"{p['words_changed']:.3f}",
                            "Char edit rate": f"{p['char_edit_rate']:.3f}",
                            "Char edit rate after canonicalisation": f"{p['char_edit_rate_after_norm']:.3f}",
                            "Top ops": ", ".join(list(p["ops"])[:4])} for p in pstats])
        tp.to_csv(TAB / "table0_perturbation_stats.csv", index=False)
        md.insert(2, "## Obfuscation scheme statistics\n\n" + _md(tp) + "\n")

    (RES / "RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    json.dump(summary, open(RES / "summary.json", "w"), indent=1)
    print("\n".join(md)[:6000])


if __name__ == "__main__":
    analyze()
