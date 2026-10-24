"""
Automatic language identification for multilingual code-mixed SMS.

No language has to be selected by the user: every token is tagged by script and lexicon,
and the message label is derived from the token mix. Every native script registered in
scripts.py is handled the same way, so a new language needs no change here.

Token tags (<x> is a registered script code, e.g. hi, ta)
  <x>       native script (or a mixed token whose stem is native)
  en        Latin-script English
  <x>-rom   Latin-script romanised native words (e.g. Hinglish aapka, Tanglish ungal)
  mix       one token mixing scripts: an English stem with a native case suffix (Swiggy-ல்);
            counted as evidence for both languages (intra-word code-mixing)
  univ      language-independent: numbers, amounts, URLs, UPI IDs, phone numbers, punctuation
  other     an unregistered script

Message labels: en, <x> (monolingual native), <x>-en (code-mixed), <x>-rom (romanised), other.
The Code-Mixing Index (Das & Gambäck, 2014) is reported as well:
  CMI = 100 * (1 - max_lang_tokens / (n - u))   where u = language-independent tokens.
"""
import re
import unicodedata

from . import scripts as S
from .obfuscation import REVERSE_HOMOGLYPHS, split_affixes, _skip


def _english_vocab():
    from .data.templates import TEMPLATES
    vocab = set()
    for subs in TEMPLATES.values():
        for by_lang in subs.values():
            for t in by_lang["en"]:
                vocab.update(w.lower() for w in re.findall(r"[A-Za-z]+", re.sub(r"\{\w+\}", " ", t)))
    vocab.update("the a an and or of to in on at for from with is are was be your you my i we it this that by "
                 "please pls ur u ok sir madam dear hi hello thanks team regards".split())
    return vocab


EN_VOCAB = _english_vocab()
_ROMAN_RES = {code: re.compile(m.ROMAN_RE) for code, m in S.SCRIPTS.items()}


def roman_script(w):
    """Registered script whose romanised form `w` looks like, else None."""
    w = w.lower()
    for code, m in S.SCRIPTS.items():
        if w in m.ROMAN:
            return code
    if w in EN_VOCAB or len(w) <= 3:
        return None
    for code, rx in _ROMAN_RES.items():
        if rx.search(w):
            return code
    return None


def label_name(lang):
    if lang == "en":
        return "English"
    if lang == "other":
        return "Other"
    code, _, kind = lang.partition("-")
    name = S.SCRIPTS[code].NAME
    return {"": name, "en": f"{name}–English", "rom": f"{name} (romanised)"}[kind]


def tag_token(tok):
    if not tok or _skip(tok):
        return "univ"
    pre, core, post = split_affixes(tok)
    if not core or not any(ch.isalpha() for ch in core):
        return "univ"
    core = "".join(S.LOOKALIKE_TO_LETTER.get(c, REVERSE_HOMOGLYPHS.get(c, c)) for c in core)
    nat = S.dominant(core)
    n_nat = sum(S.is_native(c) for c in core)
    lat = sum(c.isascii() and c.isalpha() for c in core)
    letters = sum(c.isalpha() for c in core)
    if n_nat and lat:
        stem, _, suffix = core.partition("-")
        if suffix and any(S.is_native(c) for c in suffix) and not any(S.is_native(c) for c in stem):
            return "mix"
    if n_nat and n_nat >= lat:
        return nat
    if lat and lat >= letters * 0.6:
        r = roman_script(core.lower().partition("-")[0])
        return f"{r}-rom" if r else "en"
    if n_nat:
        return nat
    return "other"


def identify(text):
    """Return {'lang', 'name', 'tokens': [(token, tag)], 'shares', 'cmi'}."""
    toks = [t for t in re.split(r"\s+", unicodedata.normalize("NFKC", text)) if t]
    tags = [tag_token(t) for t in toks]
    keys = ["en", "other"] + [c for c in S.SCRIPTS] + [f"{c}-rom" for c in S.SCRIPTS]
    counts = {k: tags.count(k) for k in keys}
    mix_target = S.dominant(text)
    counts["en"] += tags.count("mix")
    if mix_target:
        counts[mix_target] += tags.count("mix")
    n_lang = sum(counts.values())
    shares = {k: (v / n_lang if n_lang else 0.0) for k, v in counts.items() if v}
    native_total = {c: counts[c] + counts[f"{c}-rom"] for c in S.SCRIPTS}
    best = max(native_total, key=native_total.get) if native_total else None
    if n_lang == 0:
        lang = "en"
    elif counts["other"] > n_lang / 2:
        lang = "other"
    elif not best or native_total[best] == 0:
        lang = "en"
    elif counts[best] == 0 and counts[f"{best}-rom"] / n_lang < 0.25:
        lang = "en"                     # a stray romanised-looking word (a brand name) in English text
    elif counts["en"] == 0 or counts["en"] / n_lang < 0.08:
        lang = best if counts[best] >= counts[f"{best}-rom"] else f"{best}-rom"
    elif counts[f"{best}-rom"] > counts[best]:
        lang = f"{best}-rom"
    else:
        lang = f"{best}-en"
    biggest = max([counts["en"], counts["other"]] + list(native_total.values()))
    cmi = 0.0 if n_lang == 0 else 100.0 * (1 - biggest / n_lang)
    return {"lang": lang, "name": label_name(lang), "tokens": list(zip(toks, tags)),
            "shares": shares, "cmi": round(cmi, 1)}


def corpus_lang(text):
    """Collapse to the dataset's settings: 'en' or the code of the dominant native language."""
    lang = identify(text)["lang"]
    return "en" if lang in ("en", "other") else lang.partition("-")[0]
