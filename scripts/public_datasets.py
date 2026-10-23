"""
Loaders for public SMS spam / smishing corpora, normalised to columns:
    text, label (1 = spam/scam/smishing, 0 = ham), source, lang, group

`group` is the unit that must never be split across train/test. For translated corpora the
same source message appears in several languages, so a random row split leaks it; we split by group.

Status in this project:
  uci            WORKS (downloaded + tested)   English, 5,574 msgs
  hf_multi       UNTESTED (host blocked in the build sandbox; run on your machine)
                 dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset, machine-translated UCI, 21 languages
  mishra_soni    MANUAL download (Mendeley f45bkkt8pr), place CSV in data/public/
  upi_cmx        WORKS (this project, synthetic, code-mixed)
"""
import hashlib
import re
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data" / "public"
HF_URL = ("https://huggingface.co/datasets/dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset/"
          "resolve/main/data-augmented.csv")


def _gid(s):
    return hashlib.md5(re.sub(r"\s+", " ", s.lower().strip()).encode()).hexdigest()[:12]


def load_uci():
    df = pd.read_csv(PUB / "uci_sms_spam.tsv", sep="\t", header=None, names=["label", "text"], quoting=3)
    df["label"] = (df.label == "spam").astype(int)
    df["source"], df["lang"] = "uci", "en"
    df["group"] = df.text.map(_gid)
    return df.drop_duplicates("group").reset_index(drop=True)


def load_upi(promo_as_spam=True):
    df = pd.read_csv(ROOT / "data" / "upi_cmx.csv")
    if not promo_as_spam:
        df = df[df.label != "promo"]
    out = pd.DataFrame({"text": df.text, "label": (df.label.isin(["scam", "promo"] if promo_as_spam else ["scam"])).astype(int),
                        "source": "upi_cmx", "lang": df.lang, "group": df.template_id, "split": df.split})
    return out.reset_index(drop=True)


def load_hf_multi():
    """Wide file (one row per original message, columns text, text_hi, text_de, ...) -> long format.
    group = hash of the ENGLISH text, so every translation of a message (and exact-duplicate English
    messages) stays on the same side of any split. Note: the English column is the UCI collection,
    so do not also load UCI as a separate source when using this one."""
    p = PUB / "hf_multilingual.csv"
    if not p.exists():
        urllib.request.urlretrieve(HF_URL, p)
    df = pd.read_csv(p)
    print("hf_multi columns:", list(df.columns))
    low = {c.lower(): c for c in df.columns}
    lab = next((low[k] for k in ("labels", "label", "class") if k in low), None)
    if lab is None or "text" not in df.columns:
        raise ValueError(f"cannot find label/text columns in {list(df.columns)}")
    y = df[lab].astype(str).str.lower().isin(["spam", "1"]).astype(int)
    gid = df["text"].astype(str).map(_gid)
    parts = []
    for c in ["text"] + [c for c in df.columns if c.startswith("text_")]:
        lang = "en" if c == "text" else c[5:]
        t = pd.DataFrame({"text": df[c], "label": y, "group": gid, "lang": lang})
        parts.append(t[t.text.notna() & (t.text.astype(str).str.strip() != "")])
    out = pd.concat(parts, ignore_index=True)
    out["text"] = out.text.astype(str)
    out["source"] = "hf_multi"
    out = out.drop_duplicates(["group", "lang"]).reset_index(drop=True)
    print(f"hf_multi: {out.group.nunique()} unique source messages x {out.lang.nunique()} languages")
    return out


def load_mishra_soni():
    p = next(iter(PUB.glob("*5971*.csv")), None) or next(iter(PUB.glob("*mishra*.csv")), None)
    if p is None:
        raise FileNotFoundError("download Mendeley f45bkkt8pr CSV into data/public/")
    df = pd.read_csv(p, encoding="latin-1")
    cols = {c.lower(): c for c in df.columns}
    y = df[cols["label"]].astype(str).str.lower().isin(["spam", "smishing"]).astype(int)
    out = pd.DataFrame({"text": df[cols["text"]].astype(str), "label": y, "source": "mishra_soni", "lang": "en"})
    out["group"] = out.text.map(_gid)
    return out.drop_duplicates("group").reset_index(drop=True)


def grouped_split(df, test_frac=0.2, seed=0):
    """Hold out whole groups (stratification is approximate)."""
    import numpy as np
    rng = np.random.RandomState(seed)
    g = df.groupby("group").label.max().reset_index()
    test_groups = set()
    for y in (0, 1):
        ids = g[g.label == y].group.values.copy()
        rng.shuffle(ids)
        test_groups |= set(ids[: int(len(ids) * test_frac)])
    te = df.group.isin(test_groups)
    return df[~te].reset_index(drop=True), df[te].reset_index(drop=True)


if __name__ == "__main__":
    # python scripts/public_datasets.py   -> downloads/loads every source and prints a summary
    for name, fn in (("uci", load_uci), ("upi_cmx", load_upi), ("hf_multi", load_hf_multi),
                     ("mishra_soni", load_mishra_soni)):
        try:
            d = fn()
            print(f"\n[{name}] OK rows={len(d)} spam_rate={d.label.mean():.3f} langs={d.lang.nunique()} groups={d.group.nunique()}")
            print(d.lang.value_counts().head(8).to_string())
        except Exception as e:
            print(f"\n[{name}] FAILED: {type(e).__name__}: {e}")
