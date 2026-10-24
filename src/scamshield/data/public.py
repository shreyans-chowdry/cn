"""
Public SMS spam / smishing corpora (integrated by Ayushmaan Nayak), mapped onto the project schema:

    text, label3 (legit | promo | scam | spam), binary (1 = unwanted), source, group

  mishra_soni  Mishra & Soni SMS Phishing Dataset (Mendeley f45bkkt8pr), 5,971 English SMS with
               three labels: ham / spam / smishing  ->  legit / promo / scam  (the only public corpus
               that separates scams from ordinary promotions, so it is used for 3-class training)
  uci          UCI SMS Spam Collection (Almeida & Gomez Hidalgo), 5,574 English SMS, ham / spam.
               Its "spam" mixes premium-rate scams and adverts, so it is labelled `spam` (binary only)
  exais        ExAIS SMS (Onashoga et al.), 20 users' handset logs, English / Pidgin, ham / spam (binary only)
  hf_multi     UCI machine-translated into 21 languages (dbarbedillo/SMS_Spam_Multilingual_Collection);
               used only as an out-of-domain stress test (no code-mixed Indic text, noisy translations)

`group` keeps every copy / translation of the same message on one side of a split. Exact duplicates
are removed inside and across corpora (normalised text key), and texts with conflicting labels dropped.
"""
import csv
import glob
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PUB = ROOT / "data" / "public"


def _fix_mojibake(s):
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _key(t):
    return re.sub(r"[^a-z0-9]+", "", str(t).lower())


def _gid(t):
    return hashlib.md5(_key(t).encode()).hexdigest()[:12]


def load_mishra_soni():
    df = pd.read_csv(PUB / "Dataset_5971.csv", encoding="latin-1")
    lab = df.LABEL.str.strip().str.lower().map({"ham": "legit", "spam": "promo", "smishing": "scam"})
    out = pd.DataFrame({"text": df.TEXT.astype(str).map(_fix_mojibake), "label3": lab, "source": "mishra_soni"})
    return out.dropna()


def load_uci():
    df = pd.read_csv(PUB / "uci_sms_spam.tsv", sep="\t", header=None, names=["label", "text"],
                     quoting=csv.QUOTE_NONE, encoding="utf-8", on_bad_lines="skip")
    return pd.DataFrame({"text": df.text.astype(str), "label3": df.label.map({"ham": "legit", "spam": "spam"}),
                         "source": "uci"}).dropna()


def load_exais():
    rows = []
    for f in sorted(glob.glob(str(PUB / "exais" / "*.csv"))):
        with open(f, encoding="latin-1", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) < 8 or r[6].strip().upper() not in ("SPAM", "HAM") or r[1].strip().lower() != "receive":
                    continue
                text = ",".join(x for x in r[7:] if x.strip()).strip()
                rows.append((text, "spam" if r[6].strip().upper() == "SPAM" else "legit", "exais"))
    return pd.DataFrame(rows, columns=["text", "label3", "source"])


def load_hf_multi(max_per_lang=None):
    df = pd.read_csv(PUB / "hf_multilingual.csv")
    y = df["labels"].astype(str).str.lower().map({"spam": "spam", "ham": "legit"})
    gid = df["text"].astype(str).map(_gid)
    parts = []
    for c in [c for c in df.columns if c.startswith("text_")]:
        t = pd.DataFrame({"text": df[c], "label3": y, "group": gid, "source": "hf_multi", "lang": c[5:]})
        t = t[t.text.notna() & (t.text.astype(str).str.strip() != "")]
        parts.append(t.head(max_per_lang) if max_per_lang else t)
    return pd.concat(parts, ignore_index=True)


def load_public(include_hf=False):
    """All English public corpora, cleaned and de-duplicated across corpora (first source wins)."""
    df = pd.concat([load_mishra_soni(), load_uci(), load_exais()], ignore_index=True)
    df["text"] = df.text.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df.text.str.len() >= 8]
    df["key"] = df.text.map(_key)
    binary = df.label3.ne("legit")
    conflict = binary.groupby(df.key).nunique()
    df = df[~df.key.isin(conflict[conflict > 1].index)]
    df = df.drop_duplicates("key", keep="first").drop(columns="key")
    df["binary"] = df.label3.ne("legit").astype(int)
    df["group"] = df.text.map(_gid)
    df["lang"] = "en"
    if include_hf:
        hf = load_hf_multi()
        hf["binary"] = hf.label3.ne("legit").astype(int)
        df = pd.concat([df, hf], ignore_index=True)
    return df.reset_index(drop=True)


def grouped_split(df, test_frac=0.2, seed=0):
    """Hold out whole groups, stratified by the binary label."""
    rng = np.random.RandomState(seed)
    g = df.groupby("group").binary.max().reset_index()
    test = set()
    for y in (0, 1):
        ids = np.array(g[g.binary == y].group.tolist(), dtype=object)
        rng.shuffle(ids)
        test |= set(ids[: int(len(ids) * test_frac)])
    m = df.group.isin(test)
    return df[~m].reset_index(drop=True), df[m].reset_index(drop=True)


if __name__ == "__main__":
    d = load_public()
    print(d.groupby(["source", "label3"]).size().unstack(fill_value=0))
