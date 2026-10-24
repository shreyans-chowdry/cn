"""
Automatic language identification for bilingual English / Tamil-English SMS.

No language has to be selected by the user: every token is tagged by script and lexicon,
and the message label is derived from the token mix.

Token tags
  ta      Tamil script (or a mixed token whose stem is Tamil)
  en      Latin-script English
  ta-rom  Latin-script romanised Tamil ("Tanglish", e.g. ungal, pannunga)
  mix     one token mixing both scripts: an English stem with a Tamil case suffix (Swiggy-ல்);
          counted as evidence for both languages (intra-word code-mixing)
  univ    language-independent: numbers, amounts, URLs, UPI IDs, phone numbers, punctuation
  other   another script (Devanagari, Cyrillic look-alikes are folded first, ...)

Message labels: English, Tamil, Tamil–English (code-mixed), Tamil (romanised), Other.
The Code-Mixing Index (Das & Gambäck, 2014) is reported as well:
  CMI = 100 * (1 - max_lang_tokens / (n - u))   where u = language-independent tokens.
"""
import re
import unicodedata

from . import tamil as T
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
_ROMAN_TA_RE = re.compile(r"(zh|ngal|nga$|kku|ttu|ppu|chu|ndr|idum$|aagi|aaga|unga|thu$|kal$|aam$|aar$|iyil$|ukku$|ai$|um$)")


def _looks_roman_tamil(w):
    w = w.lower()
    return w in T.ROMAN_TAMIL or (w not in EN_VOCAB and len(w) > 3 and bool(_ROMAN_TA_RE.search(w)))


LABEL_NAMES = {"en": "English", "ta": "Tamil", "mixed": "Tamil–English", "ta-rom": "Tamil (romanised)",
               "other": "Other"}


def tag_token(tok):
    if not tok or _skip(tok):
        return "univ"
    pre, core, post = split_affixes(tok)
    if not core or not any(ch.isalpha() for ch in core):
        return "univ"
    core = "".join(REVERSE_HOMOGLYPHS.get(c, c) for c in core)
    ta = sum(T.is_tamil_char(c) for c in core)
    lat = sum(c.isascii() and c.isalpha() for c in core)
    letters = sum(c.isalpha() for c in core)
    if ta and lat:
        stem, _, suffix = core.partition("-")
        if suffix and any(T.is_tamil_char(c) for c in suffix) and not any(T.is_tamil_char(c) for c in stem):
            return "mix"
    if ta and ta >= lat:
        return "ta"
    if lat and lat >= letters * 0.6:
        stem = core.lower().partition("-")[0]
        return "ta-rom" if _looks_roman_tamil(stem) else "en"
    if ta:
        return "ta"
    return "other"


def identify(text):
    """Return {'lang', 'name', 'tokens': [(token, tag)], 'shares', 'cmi'}."""
    toks = [t for t in re.split(r"\s+", unicodedata.normalize("NFKC", text)) if t]
    tags = [tag_token(t) for t in toks]
    counts = {k: tags.count(k) for k in ("en", "ta", "ta-rom", "other")}
    counts["en"] += tags.count("mix")
    counts["ta"] += tags.count("mix")
    n_lang = sum(counts.values())
    shares = {k: (v / n_lang if n_lang else 0.0) for k, v in counts.items()}
    tamil_total = counts["ta"] + counts["ta-rom"]
    if n_lang == 0:
        lang = "en"
    elif counts["other"] > n_lang / 2:
        lang = "other"
    elif tamil_total == 0:
        lang = "en"
    elif counts["en"] == 0 or counts["en"] / n_lang < 0.08:
        lang = "ta" if counts["ta"] >= counts["ta-rom"] else "ta-rom"
    elif counts["ta-rom"] > counts["ta"]:
        lang = "ta-rom"
    else:
        lang = "mixed"
    cmi = 0.0 if n_lang == 0 else 100.0 * (1 - max(counts["en"], tamil_total, counts["other"]) / n_lang)
    return {"lang": lang, "name": LABEL_NAMES[lang], "tokens": list(zip(toks, tags)),
            "shares": shares, "cmi": round(cmi, 1)}


def corpus_lang(text):
    """Collapse to the dataset's two settings: 'en' or 'ta' (anything containing Tamil)."""
    return "en" if identify(text)["lang"] in ("en", "other") else "ta"
