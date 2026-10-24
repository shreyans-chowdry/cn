"""
Build UPI-BiSMS, the bilingual (English / Tamil-English) UPI SMS corpus.

Split protocol (template-disjoint): for every (label, subtype) one template index is held
out for TEST in both languages, so test messages are new phrasings of intents the model saw
only in other wordings. This prevents template memorisation from inflating accuracy.

Natural variation applied to clean messages (how people really type, not an attack):
  English : informal spellings (ur, pls, u), random casing, punctuation drift
  Tamil   : formal <-> colloquial register (செய்யவும் / செய்யுங்க / பண்ணுங்க), English loanwords
            occasionally typed in Tamil script (account -> அக்கவுண்ட்), English words in
            random case
  both    : shared prefixes/suffixes and spoofable DLT sender headers (VM-ABCDEF:)
"""
import argparse
import random
import re
from pathlib import Path

import pandas as pd

from .templates import TEMPLATES, LANGS
from . import lexicon as L
from .. import tamil as T

CLASS_SHARE = {"scam": 0.36, "legit": 0.44, "promo": 0.20}
TA_LOANWORD_RATE = 0.08      # natural rate of English loanwords typed in Tamil script
TA_REGISTER_RATE = 0.5


def _natural_en(rng, text):
    variants = L.NATURAL_VARIANTS["en"]
    out = []
    for tok in text.split(" "):
        core = tok.strip(".,!?:;").lower()
        if core in variants and rng.random() < 0.35 and tok.lower().startswith(core):
            rep = rng.choice(variants[core])
            if tok[:1].isupper():
                rep = rep[:1].upper() + rep[1:]
            tok = rep + tok[len(core):]
        out.append(tok)
    return " ".join(out)


def _natural_ta(rng, text):
    out = []
    for tok in text.split(" "):
        core = tok.strip(".,!?:;")
        low = core.lower()
        if core in T.REGISTER_VARIANTS and rng.random() < TA_REGISTER_RATE:
            tok = tok.replace(core, rng.choice(T.REGISTER_VARIANTS[core]), 1)
        elif low in T.EN2TA and rng.random() < TA_LOANWORD_RATE:
            tok = tok.replace(core, T.EN2TA[low], 1)
        out.append(tok)
    return " ".join(out)


def _surface(rng, text, lang):
    text = _natural_en(rng, text) if lang == "en" else _natural_ta(rng, text)
    r = rng.random()
    if r < 0.12:
        text = text.lower()          # no effect on Tamil letters, lower-cases the English words
    elif r < 0.16:
        text = text.upper()
    if rng.random() < 0.2:
        text = text.rstrip(".!")
    if rng.random() < 0.08:
        text = text.replace(". ", ".. ")
    return text


def generate(n_per_lang=5000, seed=13):
    rng = random.Random(seed)
    rows = []
    for label, subtypes in TEMPLATES.items():
        sub_names = sorted(subtypes)
        held_out = {st: rng.randrange(len(subtypes[st]["en"])) for st in sub_names}
        per_lang_label = int(n_per_lang * CLASS_SHARE[label])
        for lang in LANGS:
            for j in range(per_lang_label):
                st = sub_names[j % len(sub_names)]
                temps = subtypes[st][lang]
                ti = rng.randrange(len(temps))
                text = temps[ti].format(**L.fill_slots(rng, label))
                text = rng.choice(L.PREFIXES) + text + rng.choice(L.SUFFIXES)
                text = L.maybe_sender(rng, label) + text
                text = re.sub(r"\s+", " ", _surface(rng, text, lang)).strip()
                rows.append({"text": text, "label": label, "subtype": st, "lang": lang,
                             "template_id": f"{label}/{st}/{ti}",
                             "split": "test" if ti == held_out[st] else "train"})
    df = pd.DataFrame(rows).drop_duplicates("text").reset_index(drop=True)
    tr_idx = df.index[df.split == "train"].tolist()
    rng.shuffle(tr_idx)
    df.loc[tr_idx[: int(0.15 * len(tr_idx))], "split"] = "val"
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df.insert(0, "id", [f"m{i:05d}" for i in range(len(df))])
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-lang", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", default="data/upi_bisms.csv")
    a = ap.parse_args()
    df = generate(a.n_per_lang, a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(df.groupby(["split", "label"]).size().unstack())
    print(df.groupby(["lang", "label"]).size().unstack())


if __name__ == "__main__":
    main()
