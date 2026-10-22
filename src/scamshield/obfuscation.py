"""
Graded obfuscation scheme (L0 - L4) for code-mixed SMS, plus a canonicalising
normaliser used as a pre-processing defence.

Level  Name            word-prob  ops/word  Operations available
-----  --------------  ---------  --------  -----------------------------------------------
L0     clean           0          0         -
L1     light           0.15       1         vowel drop, char repeat, case flip, adjacent swap,
                                            phonetic respelling (ph->f, ee->i, w->v ...)
L2     moderate        0.30       1         L1 + leetspeak (a->@, o->0 ...), separator
                                            insertion (K.Y.C, P-I-N, l i n k)
L3     heavy           0.45       1-2       L2 + Unicode homoglyphs (Latin->Cyrillic/Greek),
                                            zero-width characters, random insert/delete
L4     cross-script    0.60       1-3       L3 + script mixing: salient words re-written
                                            phonetically in Devanagari/Tamil/Bengali/Telugu

Attacks are *keyword-targeted*: salient fraud words (KYC, PIN, refund, link ...)
are perturbed with twice the base probability, as real scammers obfuscate the
trigger words that filters look for. URLs, UPI IDs and numbers are left intact.
"""
import random
import re
import unicodedata

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
    "draw", "turant", "udane", "ekhuni", "ippude", "inaam", "parisu", "puroskar", "bahumati", "jeeta",
    "paise", "panam", "taka", "dabbulu", "registration", "processing", "sanction", "electricity",
    "connection", "contact", "immediately", "now", "abhi", "ippove",
}

# Phonetic native-script renderings of salient (mostly English) words, per script.
SCRIPT_LEX = {
    "deva": {"account": "अकाउंट", "kyc": "केवाईसी", "pin": "पिन", "otp": "ओटीपी", "link": "लिंक", "block": "ब्लॉक",
             "refund": "रिफंड", "cashback": "कैशबैक", "prize": "प्राइज़", "loan": "लोन", "bank": "बैंक",
             "click": "क्लिक", "update": "अपडेट", "upi": "यूपीआई", "card": "कार्ड", "call": "कॉल",
             "urgent": "अर्जेंट", "winner": "विनर", "free": "फ्री", "offer": "ऑफर", "parcel": "पार्सल",
             "fee": "फीस", "reward": "रिवॉर्ड", "claim": "क्लेम", "police": "पुलिस", "job": "जॉब",
             "bill": "बिल", "lucky": "लकी", "cash": "कैश", "request": "रिक्वेस्ट", "expire": "एक्सपायर",
             "transfer": "ट्रांसफर", "whatsapp": "व्हाट्सऐप", "points": "पॉइंट्स", "verify": "वेरिफाई"},
    "taml": {"account": "அக்கவுண்ட்", "kyc": "கேஒய்சி", "pin": "பின்", "otp": "ஓடிபி", "link": "லிங்க்",
             "block": "பிளாக்", "refund": "ரீஃபண்ட்", "cashback": "கேஷ்பேக்", "prize": "பிரைஸ்", "loan": "லோன்",
             "bank": "பேங்க்", "click": "கிளிக்", "update": "அப்டேட்", "upi": "யூபிஐ", "card": "கார்டு",
             "call": "கால்", "urgent": "அர்ஜென்ட்", "winner": "வின்னர்", "free": "ஃப்ரீ", "offer": "ஆஃபர்",
             "parcel": "பார்சல்", "fee": "ஃபீஸ்", "reward": "ரிவார்டு", "claim": "கிளெய்ம்", "police": "போலீஸ்",
             "job": "ஜாப்", "bill": "பில்", "lucky": "லக்கி", "cash": "கேஷ்", "request": "ரிக்வெஸ்ட்",
             "expire": "எக்ஸ்பையர்", "transfer": "டிரான்ஸ்ஃபர்", "whatsapp": "வாட்ஸ்அப்", "points": "பாயிண்ட்ஸ்",
             "verify": "வெரிஃபை"},
    "beng": {"account": "অ্যাকাউন্ট", "kyc": "কেওয়াইসি", "pin": "পিন", "otp": "ওটিপি", "link": "লিংক",
             "block": "ব্লক", "refund": "রিফান্ড", "cashback": "ক্যাশব্যাক", "prize": "প্রাইজ", "loan": "লোন",
             "bank": "ব্যাংক", "click": "ক্লিক", "update": "আপডেট", "upi": "ইউপিআই", "card": "কার্ড",
             "call": "কল", "urgent": "আর্জেন্ট", "winner": "উইনার", "free": "ফ্রি", "offer": "অফার",
             "parcel": "পার্সেল", "fee": "ফি", "reward": "রিওয়ার্ড", "claim": "ক্লেম", "police": "পুলিশ",
             "job": "জব", "bill": "বিল", "lucky": "লাকি", "cash": "ক্যাশ", "request": "রিকোয়েস্ট",
             "expire": "এক্সপায়ার", "transfer": "ট্রান্সফার", "whatsapp": "হোয়াটসঅ্যাপ", "points": "পয়েন্টস",
             "verify": "ভেরিফাই"},
    "telu": {"account": "అకౌంట్", "kyc": "కేవైసీ", "pin": "పిన్", "otp": "ఓటీపీ", "link": "లింక్",
             "block": "బ్లాక్", "refund": "రీఫండ్", "cashback": "క్యాష్‌బ్యాక్", "prize": "ప్రైజ్", "loan": "లోన్",
             "bank": "బ్యాంక్", "click": "క్లిక్", "update": "అప్‌డేట్", "upi": "యూపీఐ", "card": "కార్డ్",
             "call": "కాల్", "urgent": "అర్జెంట్", "winner": "విన్నర్", "free": "ఫ్రీ", "offer": "ఆఫర్",
             "parcel": "పార్సెల్", "fee": "ఫీజు", "reward": "రివార్డ్", "claim": "క్లెయిమ్", "police": "పోలీస్",
             "job": "జాబ్", "bill": "బిల్", "lucky": "లక్కీ", "cash": "క్యాష్", "request": "రిక్వెస్ట్",
             "expire": "ఎక్స్‌పైర్", "transfer": "ట్రాన్స్‌ఫర్", "whatsapp": "వాట్సాప్", "points": "పాయింట్స్",
             "verify": "వెరిఫై"},
}
LANG_SCRIPT = {"hi": "deva", "en": "deva", "ta": "taml", "bn": "beng", "te": "telu"}


# ----------------------------------------------------------------- operations
def op_vowel_drop(w, rng, lang):
    idx = [i for i, ch in enumerate(w) if ch in VOWELS and 0 < i < len(w) - 1]
    if not idx:
        return w
    drop = set(rng.sample(idx, max(1, len(idx) // 2)))
    return "".join(ch for i, ch in enumerate(w) if i not in drop)


def op_repeat(w, rng, lang):
    i = rng.randrange(len(w))
    return w[:i] + w[i] * rng.randint(2, 3) + w[i + 1:]


def op_case(w, rng, lang):
    return "".join(ch.upper() if rng.random() < 0.5 else ch.lower() for ch in w)


def op_swap(w, rng, lang):
    if len(w) < 4:
        return w
    i = rng.randrange(1, len(w) - 2)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:]


def op_phonetic(w, rng, lang):
    cands = [(a, b) for a, b in PHONETIC if a in w.lower()]
    if not cands:
        return op_vowel_drop(w, rng, lang)
    a, b = rng.choice(cands)
    return re.sub(a, b, w, count=1, flags=re.IGNORECASE)


def op_leet(w, rng, lang):
    chars = list(w)
    idx = [i for i, ch in enumerate(chars) if ch.lower() in LEET]
    if not idx:
        return w
    for i in rng.sample(idx, max(1, (len(idx) + 1) // 2)):
        chars[i] = rng.choice(LEET[chars[i].lower()])
    return "".join(chars)


def op_separator(w, rng, lang):
    if len(w) > 8:
        i = rng.randrange(1, len(w) - 1)
        return w[:i] + rng.choice(SEPARATORS) + w[i:]
    return rng.choice(SEPARATORS).join(w)


def op_homoglyph(w, rng, lang):
    chars = list(w)
    idx = [i for i, ch in enumerate(chars) if ch in HOMOGLYPHS]
    if not idx:
        return w
    for i in rng.sample(idx, max(1, int(len(idx) * rng.uniform(0.4, 1.0)))):
        chars[i] = HOMOGLYPHS[chars[i]]
    return "".join(chars)


def op_zero_width(w, rng, lang):
    chars = list(w)
    for _ in range(rng.randint(1, max(1, len(w) // 3))):
        chars.insert(rng.randrange(1, len(chars) + 1), rng.choice(ZERO_WIDTH))
    return "".join(chars)


def op_insert(w, rng, lang):
    i = rng.randrange(1, len(w) + 1)
    return w[:i] + rng.choice("abcdefghijklmnopqrstuvwxyz") + w[i:]


def op_delete(w, rng, lang):
    if len(w) < 4:
        return w
    i = rng.randrange(1, len(w) - 1)
    return w[:i] + w[i + 1:]


def op_script_mix(w, rng, lang):
    lex = SCRIPT_LEX[LANG_SCRIPT.get(lang, "deva")]
    key = w.lower()
    if key in lex:
        return lex[key]
    return op_homoglyph(w, rng, lang)


OPS = {
    "vowel_drop": op_vowel_drop, "repeat": op_repeat, "case": op_case, "swap": op_swap,
    "phonetic": op_phonetic, "leet": op_leet, "separator": op_separator, "homoglyph": op_homoglyph,
    "zero_width": op_zero_width, "insert": op_insert, "delete": op_delete, "script_mix": op_script_mix,
}

L1_OPS = ["vowel_drop", "repeat", "case", "swap", "phonetic"]
L2_OPS = L1_OPS + ["leet", "separator"]
L3_OPS = L2_OPS + ["homoglyph", "zero_width", "insert", "delete"]
L4_OPS = L3_OPS + ["script_mix"]

LEVELS = {
    0: {"name": "clean", "p": 0.0, "ops": [], "new": [], "max_ops": 0},
    1: {"name": "light", "p": 0.15, "ops": L1_OPS, "new": L1_OPS, "max_ops": 1},
    2: {"name": "moderate", "p": 0.30, "ops": L2_OPS, "new": ["leet", "separator"], "max_ops": 1},
    3: {"name": "heavy", "p": 0.45, "ops": L3_OPS, "new": ["homoglyph", "zero_width", "insert", "delete"], "max_ops": 2},
    4: {"name": "cross-script", "p": 0.60, "ops": L4_OPS, "new": ["script_mix"], "max_ops": 3},
}

_TOKEN_RE = re.compile(r"(\s+)")
_SKIP_RE = re.compile(r"(@|://|www\.|\.(com|in|xyz|top|ly|gd|me|it|co|info|live|site|net|click|support|online|sbi)\b|/)", re.I)
_WORD_RE = re.compile(r"^([^\w]*)(\w[\w'/]*\w|\w)([^\w]*)$", re.UNICODE)


def _skip(tok):
    if _SKIP_RE.search(tok):
        return True
    digits = sum(ch.isdigit() for ch in tok)
    return digits >= max(1, len(tok) // 2)


def obfuscate(text, level, lang="en", rng=None, seed=None, return_ops=False):
    """Obfuscate `text` at intensity `level` (0-4). Deterministic given `seed`."""
    if rng is None:
        rng = random.Random(seed)
    cfg = LEVELS[int(level)]
    if cfg["p"] == 0:
        return (text, []) if return_ops else text
    weights = [3.0 if o in cfg["new"] else 1.0 for o in cfg["ops"]]
    if level == 4:
        weights = [6.0 if o == "script_mix" else w for o, w in zip(cfg["ops"], weights)]
    parts = _TOKEN_RE.split(text)
    applied = []
    for k, tok in enumerate(parts):
        if not tok or tok.isspace() or _skip(tok):
            continue
        m = _WORD_RE.match(tok)
        if not m:
            continue
        pre, core, post = m.groups()
        if len(core) < 2 or not any(ch.isalpha() for ch in core):
            continue
        p = cfg["p"] * (2.0 if core.lower() in SALIENT else 1.0)
        if rng.random() >= min(p, 0.95):
            continue
        n_ops = rng.randint(1, cfg["max_ops"])
        new = core
        for _ in range(n_ops):
            op = rng.choices(cfg["ops"], weights=weights)[0]
            if op != "script_mix" and not new.isascii() and op not in ("zero_width",):
                continue
            new = OPS[op](new, rng, lang) or new
            applied.append(op)
        parts[k] = pre + new + post
    out = "".join(parts)
    return (out, applied) if return_ops else out


# ------------------------------------------------------------------ defence
_ZW_RE = re.compile("[​‌‍⁠﻿]")
_SPACED_RE = re.compile(r"\b(?:\w[\.\-_\* ]){2,}\w\b")
_INTRA_SEP_RE = re.compile(r"(?<=[A-Za-z])[\.\-_\*](?=[A-Za-z])")


def _deleet_token(tok):
    letters = sum(ch.isalpha() for ch in tok)
    subs = sum(ch in DELEET for ch in tok)
    if letters >= 2 and subs and letters >= subs and not tok.isdigit():
        return "".join(DELEET.get(ch, ch) for ch in tok)
    return tok


def normalize(text):
    """Generic canonicalisation defence (no knowledge of the attack lexicon):
    NFKC, strip zero-width chars, map homoglyphs back to Latin, collapse
    separators inside words, undo leetspeak in alphabetic tokens, squeeze
    character runs, lowercase."""
    t = unicodedata.normalize("NFKC", text)
    t = _ZW_RE.sub("", t)
    t = "".join(REVERSE_HOMOGLYPHS.get(ch, ch) for ch in t)
    t = _SPACED_RE.sub(lambda m: re.sub(r"[\.\-_\* ]", "", m.group(0)), t)
    toks = []
    for tok in t.split(" "):
        if _skip(tok):
            toks.append(tok)
            continue
        tok = _INTRA_SEP_RE.sub("", tok)
        toks.append(_deleet_token(tok))
    t = " ".join(toks)
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
    demo = [("Dear customer aapka SBI account aaj raat block ho jayega. KYC update karne ke liye turant link pe click karein bit.ly/x1", "hi"),
            ("Ungal refund Rs 4,999 pending-la irukku. Claim panna collect request approve panni PIN enter pannunga", "ta")]
    for txt, lg in demo:
        for lv in range(5):
            print(f"L{lv}:", obfuscate(txt, lv, lg, seed=7))
        print("norm(L3):", normalize(obfuscate(txt, 3, lg, seed=7)))
        print()
