"""
Registry of the non-Latin scripts ScamShield understands.

The system is language-agnostic: the generator, obfuscator, language identifier,
canonicaliser, cue explainer and the phone app all iterate over this registry. Adding a
language means writing one module with the same interface as hindi.py / tamil.py, adding
its parallel templates, and registering it here.
"""
import re

from . import hindi, tamil

SCRIPTS = {m.CODE: m for m in (hindi, tamil)}          # code -> module
ALL_RANGES = "".join(m.RANGE_RE for m in SCRIPTS.values())
INDIC_CHAR_RE = re.compile("[" + ALL_RANGES + "]")


def script_char(ch):
    """Code of the registered script that contains `ch`, else None."""
    o = ord(ch)
    for code, m in SCRIPTS.items():
        if m.LO <= o <= m.HI:
            return code
    return None


def is_native(ch):
    return script_char(ch) is not None


def dominant(text):
    """Most frequent registered script in `text`, or None."""
    counts = {}
    for ch in text:
        c = script_char(ch)
        if c:
            counts[c] = counts.get(c, 0) + 1
    return max(counts, key=counts.get) if counts else None


def script_of(word):
    """'lat' or a registered script code, by majority of letters."""
    c = dominant(word)
    if c is None:
        return "lat"
    return c if SCRIPTS[c].share(word) >= 0.5 else "lat"


LOOKALIKE_TO_LETTER = {k: v for m in SCRIPTS.values() for k, v in m.LOOKALIKE_TO_LETTER.items()}
X2EN = {k: v for m in SCRIPTS.values() for k, v in m.X2EN.items()}
SALIENT = set().union(*(m.SALIENT for m in SCRIPTS.values()))
