"""Loaders that map public SMS-spam corpora onto one binary schema: text, label (1 = spam/scam/unwanted, 0 = ham), source.

Add a new corpus by writing a loader and registering it in LOADERS. Corpora that cannot be fetched automatically
(Kaggle / HuggingFace / Mendeley / IEEE DataPort) can be dropped into data/real/ as `<name>.csv` with columns
`text,label` (label: spam|ham or 1|0) and are picked up by `load_extra`.
"""
import csv
import glob
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "data" / "real"


def load_uci():
    """UCI SMS Spam Collection (Almeida & Gomez Hidalgo): English, UK/Singapore, 2000s-era."""
    df = pd.read_csv(REAL / "uci_sms_spam.tsv", sep="\t", header=None, names=["label", "text"],
                     quoting=csv.QUOTE_NONE, encoding="utf-8", on_bad_lines="skip")
    df["label"] = (df.label == "spam").astype(int)
    return df.assign(source="uci")[["text", "label", "source"]]


def load_exais():
    """ExAIS SMS Spam (Onashoga et al. 2015): 20 Nigerian users, English / Pidgin, 2014-2016, real handset logs."""
    rows = []
    for f in sorted(glob.glob(str(REAL / "exais" / "*.csv"))):
        with open(f, encoding="latin-1", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) < 8 or r[6].strip().upper() not in ("SPAM", "HAM"):
                    continue
                text = ",".join(x for x in r[7:] if x.strip()).strip()
                rows.append((text, int(r[6].strip().upper() == "SPAM"), "exais"))
    return pd.DataFrame(rows, columns=["text", "label", "source"])


def load_extra():
    out = []
    for f in sorted(glob.glob(str(REAL / "extra_*.csv"))):
        d = pd.read_csv(f)
        d["label"] = d.label.map(lambda v: int(str(v).strip().lower() in ("1", "spam", "smishing", "scam")))
        out.append(d.assign(source=Path(f).stem.replace("extra_", ""))[["text", "label", "source"]])
    return out


def load_upi_cmx():
    """Our synthetic UPI-CMX corpus; scam + promo are 'spam', legit is 'ham'. Keeps the original split."""
    d = pd.read_csv(ROOT / "data" / "upi_cmx.csv")
    d["label3"] = d.label
    d["label"] = (d.label != "legit").astype(int)
    return d.assign(source="upi_cmx")[["text", "label", "source", "label3", "lang", "split"]]


def clean(df):
    df = df.copy()
    df["text"] = df.text.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df.text.str.len() >= 10]
    df["key"] = df.text.str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)
    return df


def load_all(include_synthetic=True):
    parts = [load_uci(), load_exais()] + load_extra()
    real = clean(pd.concat(parts, ignore_index=True))
    n0 = len(real)
    # remove exact duplicates inside AND across corpora so cross-dataset tests cannot leak
    conflict = real.groupby("key").label.nunique()
    real = real[~real.key.isin(conflict[conflict > 1].index)]          # drop texts with contradictory labels
    real = real.drop_duplicates("key", keep="first").reset_index(drop=True)
    stats = {"raw_total": n0, "after_dedup": len(real)}
    if include_synthetic:
        syn = clean(load_upi_cmx())
        real = pd.concat([real, syn.drop(columns=["label3", "lang"])], ignore_index=True)
    return real, stats


class Norm:
    """sklearn-compatible text normaliser (canonicalisation defence); lives here so saved pipelines unpickle anywhere."""
    def fit(self, X, y=None): return self
    def transform(self, X):
        from .obfuscation import normalize
        return [normalize(x) for x in X]
    def get_params(self, deep=True): return {}
    def set_params(self, **k): return self
    def fit_transform(self, X, y=None): return self.transform(X)
