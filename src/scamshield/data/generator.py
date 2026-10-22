"""
Build the multilingual code-mixed UPI SMS corpus (UPI-CMX).

Split protocol (template-disjoint): for every (label, subtype) one template index
is held out for TEST in *all* languages, so test messages are new phrasings of
intents the model saw only in other wordings. This prevents template memorisation
from inflating clean accuracy.
"""
import argparse
import random
import re
from pathlib import Path

import pandas as pd

from .templates import TEMPLATES, LANGS
from . import lexicon as L

CLASS_SHARE = {"scam": 0.35, "legit": 0.45, "promo": 0.20}


def _apply_natural_variation(rng, text, lang):
    variants = L.NATURAL_VARIANTS.get(lang, {})
    out = []
    for tok in text.split(" "):
        core = tok.strip(".,!?:;").lower()
        if core in variants and rng.random() < 0.35:
            rep = rng.choice(variants[core])
            if tok[:1].isupper():
                rep = rep[:1].upper() + rep[1:]
            tok = tok.lower().replace(core, rep) if tok.lower().startswith(core) else tok
        out.append(tok)
    text = " ".join(out)
    r = rng.random()
    if r < 0.12:
        text = text.lower()
    elif r < 0.16:
        text = text.upper()
    if rng.random() < 0.2:
        text = text.rstrip(".!")
    if rng.random() < 0.08:
        text = text.replace(". ", ".. ")
    return text


def _apply_native_script(rng, text, lang):
    lex = L.NATIVE_WORDS.get(lang)
    if not lex:
        return text, "roman"
    toks = text.split(" ")
    changed = False
    for i, t in enumerate(toks):
        core = t.strip(".,!?:;").lower()
        if core in lex and rng.random() < 0.7:
            toks[i] = t.lower().replace(core, lex[core])
            changed = True
    return " ".join(toks), ("mixed" if changed else "roman")


def generate(n_per_lang=2400, seed=13, native_script_rate=0.15):
    rng = random.Random(seed)
    rows = []
    for label, subtypes in TEMPLATES.items():
        sub_names = sorted(subtypes)
        held_out = {}
        for st in sub_names:
            k = len(subtypes[st]["en"])
            held_out[st] = rng.randrange(k)
        per_lang_label = int(n_per_lang * CLASS_SHARE[label])
        for lang in LANGS:
            for j in range(per_lang_label):
                st = sub_names[j % len(sub_names)]
                temps = subtypes[st][lang]
                ti = rng.randrange(len(temps))
                slots = L.fill_slots(rng, label)
                text = temps[ti].format(**slots)
                text = rng.choice(L.PREFIXES) + text + rng.choice(L.SUFFIXES)
                text = L.maybe_sender(rng, label) + text
                text = _apply_natural_variation(rng, text, lang)
                script = "roman"
                if rng.random() < native_script_rate:
                    text, script = _apply_native_script(rng, text, lang)
                text = re.sub(r"\s+", " ", text).strip()
                rows.append({
                    "text": text, "label": label, "subtype": st, "lang": lang,
                    "template_id": f"{label}/{st}/{ti}", "script": script,
                    "split": "test" if ti == held_out[st] else "train",
                })
    df = pd.DataFrame(rows).drop_duplicates("text").reset_index(drop=True)
    # carve validation out of the train-template pool
    tr_idx = df.index[df.split == "train"].tolist()
    rng.shuffle(tr_idx)
    df.loc[tr_idx[: int(0.15 * len(tr_idx))], "split"] = "val"
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df.insert(0, "id", [f"m{i:05d}" for i in range(len(df))])
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-lang", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", default="data/upi_cmx.csv")
    a = ap.parse_args()
    df = generate(a.n_per_lang, a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(df.groupby(["split", "label"]).size().unstack())
    print(df.groupby(["lang", "label"]).size().unstack())
    print("mixed-script share:", (df.script == "mixed").mean().round(3))


if __name__ == "__main__":
    main()
