"""
Graded obfuscation scheme (L0-L4) for bilingual English / Tamil-English SMS, plus a
script-aware canonicaliser used as a pre-processing defence.

Every eligible token gets perturbed with probability p (2p for salient fraud words).
The operators depend on the token's script.

Level  Name          p     ops  Latin-script tokens                     Tamil-script tokens
-----  ------------  ----  ---  --------------------------------------  ------------------------------------
L0     clean         0     0    -                                       -
L1     light         0.15  1    vowel drop, letter repeat, case flip,   confusable letters (ல/ள/ழ, ண/ந/ன,
                                adjacent swap, phonetic respelling      ர/ற), vowel-length swaps (ி/ீ, ெ/ே),
                                                                        pulli (்) dropped or added
L2     moderate      0.30  1    + leetspeak (a->@, o->0),               + separators between graphemes
                                separators (K.Y.C, P-I-N)               (உ.ட.னே)
L3     heavy         0.45  1-2  + Latin->Cyrillic/Greek homoglyphs,     + Tamil-digit homoglyphs (க->௧, அ->௮),
                                zero-width chars, insert/delete         zero-width joiners, grapheme deletion
L4     cross-script  0.60  1-3  + English words written in Tamil        + Tamil words transliterated into
                                script (account -> அக்கவுண்ட்)          Latin script (உடனே -> udane)

L4 is the transliteration attack: the message keeps its meaning for a bilingual reader but
every token can switch script. Attacks are keyword-targeted (salient words perturbed with 2p).
URLs, UPI IDs, phone numbers and amounts are never touched.
"""
import random
import re
import unicodedata

from . import tamil as T

VOWELS = set("aeiouAEIOU")

HOMOGLYPHS = {
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х",
    "y": "у", "i": "і", "j": "ј", "s": "ѕ", "v": "ν", "h": "һ",
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "I": "І",
    "K": "К", "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х",
    "Y": "Υ", "N": "Ν", "Z": "Ζ", "S": "Ѕ", "J": "Ј",
}
REVERSE_HOMOGLYPHS = {v: k for k, v in HOMOGLYPHS.items()}

LEET = {"a": ["@", "4"], "e": ["3"], "i": ["1", "!"], "o": ["0"], "s": ["$", "5"], "t": ["7"],
        "l": ["1"], "g": ["9"], "b": ["8"]}
DELEET = {"@": "a", "4": "a", "3": "e", "1": "i", "!": "i", "0": "o", "$": "s", "5": "s", "7": "t",
          "9": "g", "8": "b"}
PHONETIC = [("ph", "f"), ("f", "ph"), ("ck", "k"), ("c", "k"), ("w", "v"), ("v", "w"), ("s", "z"),
            ("ee", "i"), ("oo", "u"), ("x", "ks"), ("qu", "kw"), ("th", "t"), ("ou", "u"),
            ("ai", "e"), ("aa", "a"), ("i", "ee"), ("u", "oo")]
ZERO_WIDTH = ["​", "‌", "‍", "⁠"]
SEPARATORS = [".", "-", " ", "_", "*"]

SALIENT = {
    "kyc", "pin", "otp", "upi", "account", "a/c", "block", "blocked", "link", "click", "refund", "cashback",
    "prize", "winner", "lucky", "loan", "card", "cvv", "update", "urgent", "verify", "reward", "points",
    "fee", "parcel", "customs", "police", "fir", "anydesk", "telegram", "whatsapp", "job", "task", "bill",
    "disconnect", "claim", "expire", "redeem", "approve", "request", "bank", "transfer", "return",
    "suspend", "suspended", "cash", "free", "offer", "win", "won", "money", "pay", "call", "contest",
    "draw", "registration", "processing", "sanction", "electricity", "connection", "contact",
    "immediately", "now", "scan", "qr", "enter",
    # Tamil-script salient words
    "உடனே", "உடனடியாக", "இப்போதே", "பணம்", "பணத்தைப்", "பரிசு", "வென்றுள்ளீர்கள்", "அனுப்பவும்",
    "அனுப்புங்கள்", "காலாவதியாகிறது", "காலாவதியாகிவிட்டது", "கடைசி", "துண்டிக்கப்படும்", "பறிமுதல்",
    "வாழ்த்துக்கள்", "உள்ளிடவும்", "பெற", "தவறுதலாக", "திருப்பி", "சம்பாதிக்கலாம்", "சந்தேகத்திற்குரிய",
}


# ------------------------------------------------------------------ helpers
def graphemes(word):
    """Split into user-perceived characters: a base char plus its combining marks (க + ு -> கு)."""
    out = []
    for ch in word:
        if out and unicodedata.category(ch).startswith("M"):
            out[-1] += ch
        else:
            out.append(ch)
    return out


def script_of(word):
    return "ta" if T.tamil_share(word) >= 0.5 else "lat"


# ------------------------------------------------------------------ Latin operators
def op_vowel_drop(w, rng):
    idx = [i for i, ch in enumerate(w) if ch in VOWELS and 0 < i < len(w) - 1]
    if not idx:
        return w
    drop = set(rng.sample(idx, max(1, len(idx) // 2)))
    return "".join(ch for i, ch in enumerate(w) if i not in drop)


def op_repeat(w, rng):
    i = rng.randrange(len(w))
    return w[:i] + w[i] * rng.randint(2, 3) + w[i + 1:]


def op_case(w, rng):
    return "".join(ch.upper() if rng.random() < 0.5 else ch.lower() for ch in w)


def op_swap(w, rng):
    if len(w) < 4:
        return w
    i = rng.randrange(1, len(w) - 2)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:]


def op_phonetic(w, rng):
    cands = [(a, b) for a, b in PHONETIC if a in w.lower()]
    if not cands:
        return op_vowel_drop(w, rng)
    a, b = rng.choice(cands)
    return re.sub(a, b, w, count=1, flags=re.IGNORECASE)


def op_leet(w, rng):
    chars = list(w)
    idx = [i for i, ch in enumerate(chars) if ch.lower() in LEET]
    if not idx:
        return w
    for i in rng.sample(idx, max(1, (len(idx) + 1) // 2)):
        chars[i] = rng.choice(LEET[chars[i].lower()])
    return "".join(chars)


def op_separator(w, rng):
    g = graphemes(w)
    if len(g) > 8:
        i = rng.randrange(1, len(g) - 1)
        return "".join(g[:i]) + rng.choice(SEPARATORS) + "".join(g[i:])
    return rng.choice(SEPARATORS).join(g)


def op_homoglyph(w, rng):
    chars = list(w)
    idx = [i for i, ch in enumerate(chars) if ch in HOMOGLYPHS]
    if not idx:
        return w
    for i in rng.sample(idx, max(1, int(len(idx) * rng.uniform(0.4, 1.0)))):
        chars[i] = HOMOGLYPHS[chars[i]]
    return "".join(chars)


def op_zero_width(w, rng):
    g = graphemes(w)
    for _ in range(rng.randint(1, max(1, len(g) // 3))):
        g.insert(rng.randrange(1, len(g) + 1), rng.choice(ZERO_WIDTH))
    return "".join(g)


def op_insert(w, rng):
    i = rng.randrange(1, len(w) + 1)
    return w[:i] + rng.choice("abcdefghijklmnopqrstuvwxyz") + w[i:]


def op_delete(w, rng):
    if len(w) < 4:
        return w
    i = rng.randrange(1, len(w) - 1)
    return w[:i] + w[i + 1:]


def op_to_tamil(w, rng):
    """English loanword written phonetically in Tamil script (L4)."""
    key = w.lower()
    return T.EN2TA.get(key, op_homoglyph(w, rng))


# ------------------------------------------------------------------ Tamil operators
def op_ta_confusable(w, rng):
    pairs = [(a, b) for a, b in T.CONFUSABLE if a in w] + [(b, a) for a, b in T.CONFUSABLE if b in w]
    if not pairs:
        return op_ta_vowel_length(w, rng)
    a, b = rng.choice(pairs)
    idx = [i for i, ch in enumerate(w) if ch == a]
    i = rng.choice(idx)
    return w[:i] + b + w[i + 1:]


def op_ta_vowel_length(w, rng):
    pairs = [(a, b) for a, b in T.VOWEL_LENGTH if a in w] + [(b, a) for a, b in T.VOWEL_LENGTH if b in w]
    if not pairs:
        return op_ta_pulli(w, rng)
    a, b = rng.choice(pairs)
    return w.replace(a, b, 1)


def op_ta_pulli(w, rng):
    idx = [i for i, ch in enumerate(w) if ch == T.PULLI]
    if idx and rng.random() < 0.7:
        i = rng.choice(idx)
        return w[:i] + w[i + 1:]
    cons = [i for i, ch in enumerate(w[:-1]) if ch in T._CONS and not unicodedata.category(w[i + 1]).startswith("M")]
    if not cons:
        return w
    i = rng.choice(cons)
    return w[:i + 1] + T.PULLI + w[i + 1:]


def op_ta_digit(w, rng):
    idx = [i for i, ch in enumerate(w) if ch in T.DIGIT_HOMOGLYPHS]
    if not idx:
        return op_zero_width(w, rng)
    for i in rng.sample(idx, max(1, len(idx) // 2)):
        w = w[:i] + T.DIGIT_HOMOGLYPHS[w[i]] + w[i + 1:]
    return w


def op_ta_grapheme_delete(w, rng):
    g = graphemes(w)
    if len(g) < 3:
        return w
    del g[rng.randrange(1, len(g))]
    return "".join(g)


def op_translit(w, rng):
    """Tamil word written in Latin script, Tanglish style (L4)."""
    return T.to_latin(w)


OPS = {
    "vowel_drop": op_vowel_drop, "repeat": op_repeat, "case": op_case, "swap": op_swap,
    "phonetic": op_phonetic, "leet": op_leet, "separator": op_separator, "homoglyph": op_homoglyph,
    "zero_width": op_zero_width, "insert": op_insert, "delete": op_delete, "to_tamil": op_to_tamil,
    "ta_confusable": op_ta_confusable, "ta_vowel_length": op_ta_vowel_length, "ta_pulli": op_ta_pulli,
    "ta_digit": op_ta_digit, "ta_grapheme_delete": op_ta_grapheme_delete, "translit": op_translit,
}

_LAT = {1: ["vowel_drop", "repeat", "case", "swap", "phonetic"], 2: ["leet", "separator"],
        3: ["homoglyph", "zero_width", "insert", "delete"], 4: ["to_tamil"]}
_TA = {1: ["ta_confusable", "ta_vowel_length", "ta_pulli"], 2: ["separator"],
       3: ["ta_digit", "zero_width", "ta_grapheme_delete"], 4: ["translit"]}


def _level_ops(table, level):
    return [op for lv in range(1, level + 1) for op in table[lv]]


LEVELS = {
    0: {"name": "clean", "p": 0.0, "max_ops": 0},
    1: {"name": "light", "p": 0.15, "max_ops": 1},
    2: {"name": "moderate", "p": 0.30, "max_ops": 1},
    3: {"name": "heavy", "p": 0.45, "max_ops": 2},
    4: {"name": "cross-script", "p": 0.60, "max_ops": 3},
}
for _lv, _cfg in LEVELS.items():
    _cfg["ops"] = {"lat": _level_ops(_LAT, _lv) if _lv else [], "ta": _level_ops(_TA, _lv) if _lv else []}
    _cfg["new"] = set(_LAT.get(_lv, []) + _TA.get(_lv, []))

_TOKEN_RE = re.compile(r"(\s+)")
_SKIP_RE = re.compile(r"(@|://|www\.|\.(com|in|xyz|top|ly|gd|me|it|co|info|live|site|net|click|support|online|sbi)\b|/)", re.I)


def _is_wordchar(ch):
    return ch.isalnum() or unicodedata.category(ch).startswith("M")


def split_affixes(tok):
    """'(KYC-ஐ,' -> ('(', 'KYC-ஐ', ',')  -- keeps Tamil vowel signs inside the core."""
    i, j = 0, len(tok)
    while i < j and not _is_wordchar(tok[i]):
        i += 1
    while j > i and not _is_wordchar(tok[j - 1]):
        j -= 1
    return tok[:i], tok[i:j], tok[j:]


def _skip(tok):
    if _SKIP_RE.search(tok):
        return True
    digits = sum(ch.isdigit() for ch in tok)
    return digits >= max(1, len(tok) // 2)


def _perturb_core(core, ops, weights, n_ops, rng, applied):
    """A core like 'PIN-ஐ' has a Latin stem and a Tamil case suffix; perturb the stem only."""
    stem, sep, suffix = core.partition("-")
    target = stem if sep and stem else core
    script = script_of(target)
    new = target
    for _ in range(n_ops):
        cand = ops[script]
        if not cand:
            break
        op = rng.choices(cand, weights=weights[script])[0]
        new = OPS[op](new, rng) or new
        applied.append(op)
        if op in ("translit", "to_tamil"):
            break                       # script has changed; stop stacking operators
    return new + sep + suffix if sep and stem else new


def obfuscate(text, level, lang=None, rng=None, seed=None, return_ops=False):
    """Obfuscate `text` at intensity `level` (0-4). Deterministic given `seed`.
    `lang` is accepted for backwards compatibility; operators are chosen per token script."""
    if rng is None:
        rng = random.Random(seed)
    cfg = LEVELS[int(level)]
    if cfg["p"] == 0:
        return (text, []) if return_ops else text
    weights = {}
    for script, ops in cfg["ops"].items():
        w = [3.0 if o in cfg["new"] else 1.0 for o in ops]
        if level == 4:
            w = [6.0 if o in ("translit", "to_tamil") else x for o, x in zip(ops, w)]
        weights[script] = w
    parts = _TOKEN_RE.split(text)
    applied = []
    for k, tok in enumerate(parts):
        if not tok or tok.isspace() or _skip(tok):
            continue
        pre, core, post = split_affixes(tok)
        if len(core) < 2 or not any(ch.isalpha() for ch in core):
            continue
        key = core.lower().partition("-")[0]
        p = cfg["p"] * (2.0 if (key in SALIENT or core in SALIENT) else 1.0)
        if rng.random() >= min(p, 0.95):
            continue
        parts[k] = pre + _perturb_core(core, cfg["ops"], weights, rng.randint(1, cfg["max_ops"]), rng, applied) + post
    out = "".join(parts)
    return (out, applied) if return_ops else out


# ------------------------------------------------------------------ defence
_ZW_RE = re.compile("[​‌‍⁠﻿]")
_SEP_CLASS = r"[\.\-_\* ]"
_SPACED_LAT_RE = re.compile(r"\b(?:[A-Za-z]" + _SEP_CLASS + r"){2,}[A-Za-z]\b")
_INTRA_SEP_RE = re.compile(r"(?<=[A-Za-z])[\.\-_\*](?=[A-Za-z])")
_TA_CLUSTER = "[஀-௿]+"
_SPACED_TA_RE = re.compile(r"(?:" + _TA_CLUSTER + r"[\._\*]){2,}" + _TA_CLUSTER)
_TA_INTRA_SEP_RE = re.compile(r"(?<=[஀-௿])[\._\*](?=[஀-௿])")


def _deleet_token(tok):
    letters = sum(ch.isalpha() for ch in tok)
    subs = sum(ch in DELEET for ch in tok)
    if letters >= 2 and subs and letters >= subs and not tok.isdigit() and tok.isascii():
        return "".join(DELEET.get(ch, ch) for ch in tok)
    return tok


def _fold_token(tok):
    if _skip(tok):
        return tok
    pre, core, post = split_affixes(tok)
    stem, sep, suffix = core.partition("-")
    if sep and stem and suffix and script_of(stem) != script_of(suffix):
        # mixed token such as 'requ35t-ஐ': fold the stem and the case suffix separately
        return pre + _fold_token(stem) + sep + _fold_token(suffix) + post
    # Tamil-digit homoglyphs inside Tamil words -> letters
    if any(T.is_tamil_char(c) for c in tok):
        tok = "".join(T.DIGIT_TO_LETTER.get(c, c) for c in tok)
        tok = _TA_INTRA_SEP_RE.sub("", tok)
        pre, core, post = split_affixes(tok)
        stem, sep, suffix = core.partition("-")
        if stem in T.TA2EN:                       # அக்கவுண்ட் -> account
            return pre + T.TA2EN[stem] + sep + suffix + post
        if core in T.TA2EN:
            return pre + T.TA2EN[core] + post
        return tok
    tok = _INTRA_SEP_RE.sub("", tok)
    return _deleet_token(tok)


def normalize(text):
    """Script-aware canonicalisation defence (no access to the attack's random choices):
    NFKC, strip zero-width characters, fold Latin look-alikes (Cyrillic/Greek) back to Latin,
    fold Tamil-digit look-alikes back to Tamil letters, collapse separators inside words in both
    scripts, undo leetspeak in alphabetic Latin tokens, map Tamil-script spellings of English
    loanwords back to English, squeeze letter runs, lower-case."""
    t = unicodedata.normalize("NFKC", text)
    t = _ZW_RE.sub("", t)
    t = "".join(REVERSE_HOMOGLYPHS.get(ch, ch) for ch in t)
    t = _SPACED_LAT_RE.sub(lambda m: re.sub(_SEP_CLASS, "", m.group(0)), t)
    t = _SPACED_TA_RE.sub(lambda m: re.sub(r"[\._\*]", "", m.group(0)), t)
    t = " ".join(_fold_token(tok) for tok in t.split(" "))
    t = re.sub(r"([A-Za-z])\1{2,}", r"\1\1", t)
    return t.lower()


def edit_rate(a, b):
    """Normalised Levenshtein distance (character edits / max length)."""
    try:
        from rapidfuzz.distance import Levenshtein
        return Levenshtein.normalized_distance(a, b)
    except ImportError:  # pragma: no cover
        n, m = len(a), len(b)
        prev = list(range(m + 1))
        for i in range(1, n + 1):
            cur = [i] + [0] * m
            for j in range(1, m + 1):
                cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            prev = cur
        return prev[m] / max(n, m, 1)


if __name__ == "__main__":
    demo = ["Dear customer your SBI account will be blocked today. Update your KYC immediately by clicking sbi-kyc.xyz/aB3d",
            "உங்கள் refund ₹4,999 நிலுவையில் உள்ளது. பெற collect request-ஐ approve செய்து PIN enter செய்யவும்"]
    for txt in demo:
        for lv in range(5):
            print(f"L{lv}:", obfuscate(txt, lv, seed=7))
        print("norm(L3):", normalize(obfuscate(txt, 3, seed=7)))
        print()
