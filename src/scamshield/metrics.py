"""Evaluation metrics: macro-F1, scam false-negative rate, calibration error, bootstrap CIs."""
import numpy as np
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

LABELS = ["legit", "promo", "scam"]
SCAM = LABELS.index("scam")


def ece(probs, y_true, n_bins=15):
    """Top-label Expected Calibration Error."""
    conf = probs.max(1)
    pred = probs.argmax(1)
    correct = (pred == y_true).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(e)


def scam_fnr(y_true, y_pred):
    pos = y_true == SCAM
    return float(((y_pred != SCAM) & pos).sum() / max(pos.sum(), 1))


def scam_fpr(y_true, y_pred):
    neg = y_true != SCAM
    return float(((y_pred == SCAM) & neg).sum() / max(neg.sum(), 1))


def all_metrics(probs, y_true):
    y_pred = probs.argmax(1)
    f1s = f1_score(y_true, y_pred, labels=[0, 1, 2], average=None, zero_division=0)
    return {
        "macro_f1": float(f1s.mean()),
        "f1_legit": float(f1s[0]), "f1_promo": float(f1s[1]), "f1_scam": float(f1s[2]),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "fnr_scam": scam_fnr(y_true, y_pred),
        "fpr_scam": scam_fpr(y_true, y_pred),
        "ece": ece(probs, y_true),
        "confusion": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
    }


def bootstrap_ci(y_true, y_pred, fn, n=1000, seed=0, alpha=0.05):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y_true))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        vals.append(fn(y_true[s], y_pred[s]))
    lo, hi = np.quantile(vals, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def macro_f1_fn(y, p):
    return f1_score(y, p, labels=[0, 1, 2], average="macro", zero_division=0)


def paired_bootstrap_delta(y, pa_clean, pa_adv, pb_clean, pb_adv, n=2000, seed=0):
    """Paired bootstrap on the *degradation* (clean F1 - attacked F1) of model A minus model B.
    Returns mean difference, 95% CI and one-sided p-value for H1: A degrades less than B."""
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    diffs = []
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        da = macro_f1_fn(y[s], pa_clean[s]) - macro_f1_fn(y[s], pa_adv[s])
        db = macro_f1_fn(y[s], pb_clean[s]) - macro_f1_fn(y[s], pb_adv[s])
        diffs.append(da - db)
    diffs = np.array(diffs)
    return {"delta_mean": float(diffs.mean()), "ci95": [float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))],
            "p_one_sided": float((diffs >= 0).mean())}


def mcnemar(y, pa, pb):
    """Exact McNemar test between two classifiers' correctness."""
    from scipy.stats import binomtest
    a_ok, b_ok = pa == y, pb == y
    b01 = int((a_ok & ~b_ok).sum())
    b10 = int((~a_ok & b_ok).sum())
    n = b01 + b10
    p = binomtest(b01, n, 0.5).pvalue if n else 1.0
    return {"a_only_correct": b01, "b_only_correct": b10, "p_value": float(p)}
