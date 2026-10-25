"""
Devanagari (Hindi) script utilities. Same interface as tamil.py, so that every
script-aware component (generator, obfuscator, language identifier, canonicaliser)
handles a new script by registering one module in scripts.py.

  * is_char(): Unicode block U+0900-U+097F
  * EN2X / X2EN: Devanagari spellings of English banking loanwords (account -> अकाउंट)
  * to_latin(): rule-based Devanagari -> Latin romanisation in the colloquial "Hinglish"
                style with schwa deletion (तुरंत -> turant, आपका -> aapka), used by L4
  * CONFUSABLE / VOWEL_LENGTH: letter and sign pairs Hindi writers commonly mix up
  * VIRAMA: the halant (्)
  * LOOKALIKES: characters of another script that render almost identically to a
                Devanagari letter (Gujarati letters without the head-line, the digit २ for र)
"""
CODE = "hi"
NAME = "Hindi"
SCRIPT = "Devanagari"
LO, HI = 0x0900, 0x097F
RANGE_RE = "ऀ-ॿ"


def is_char(ch):
    return LO <= ord(ch) <= HI


def share(token):
    letters = [c for c in token if c.isalpha() or is_char(c)]
    return sum(is_char(c) for c in letters) / len(letters) if letters else 0.0


# ---------------------------------------------------------------- loanwords
EN2X = {
    "account": "अकाउंट", "kyc": "केवाईसी", "pin": "पिन", "otp": "ओटीपी", "link": "लिंक",
    "block": "ब्लॉक", "refund": "रिफंड", "cashback": "कैशबैक", "prize": "प्राइज़", "loan": "लोन",
    "bank": "बैंक", "click": "क्लिक", "update": "अपडेट", "upi": "यूपीआई", "card": "कार्ड",
    "call": "कॉल", "urgent": "अर्जेंट", "winner": "विनर", "free": "फ्री", "offer": "ऑफर",
    "parcel": "पार्सल", "fee": "फीस", "reward": "रिवॉर्ड", "claim": "क्लेम", "police": "पुलिस",
    "job": "जॉब", "bill": "बिल", "lucky": "लकी", "cash": "कैश", "request": "रिक्वेस्ट",
    "expire": "एक्सपायर", "transfer": "ट्रांसफर", "whatsapp": "व्हाट्सऐप", "points": "पॉइंट्स",
    "verify": "वेरिफाई", "approve": "अप्रूव", "scan": "स्कैन", "qr": "क्यूआर", "payment": "पेमेंट",
    "recharge": "रिचार्ज", "plan": "प्लान", "data": "डेटा", "order": "ऑर्डर", "sale": "सेल",
    "app": "ऐप", "wallet": "वॉलेट", "transaction": "ट्रांजैक्शन", "credit": "क्रेडिट", "debit": "डेबिट",
    "register": "रजिस्टर", "download": "डाउनलोड", "customer": "कस्टमर", "care": "केयर",
    "connection": "कनेक्शन", "electricity": "इलेक्ट्रिसिटी", "officer": "ऑफिसर", "enter": "एंटर",
    "suspend": "सस्पेंड", "contest": "कॉन्टेस्ट", "screenshot": "स्क्रीनशॉट", "salary": "सैलरी",
}
X2EN = {v: k for k, v in EN2X.items()}

# ---------------------------------------------------------------- register (formal <-> informal)
REGISTER_VARIANTS = {
    "करें": ["करें", "करो", "कीजिए", "कर दें"],
    "करें।": ["करें।", "करो।", "कीजिए।"],
    "भेजें": ["भेजें", "भेजो", "भेजिए"],
    "डालें": ["डालें", "डालो", "डालिए"],
    "तुरंत": ["तुरंत", "फ़ौरन", "जल्दी"],
    "कृपया": ["कृपया", "please", "pls"],
    "धन्यवाद": ["धन्यवाद", "Thanks", "शुक्रिया"],
    "आपका": ["आपका", "आपका", "तुम्हारा"],
    "आपके": ["आपके", "आपके", "तुम्हारे"],
    "पाएँ": ["पाएँ", "पाओ", "पाइए"],
    "जाएँ": ["जाएँ", "जाओ", "जाइए"],
}

# ---------------------------------------------------------------- orthographic confusions
CONFUSABLE = [("श", "ष"), ("श", "स"), ("ष", "स"), ("ब", "व"), ("न", "ण"), ("ड", "ढ")]
VOWEL_LENGTH = [("ि", "ी"), ("ु", "ू"), ("े", "ै"), ("ो", "ौ"), ("इ", "ई"), ("उ", "ऊ"), ("ए", "ऐ"),
                ("ओ", "औ"), ("ं", "ँ")]
VIRAMA = "्"
# look-alike characters from another block that render like a Devanagari letter
LOOKALIKES = {"क": "ક", "ग": "ગ", "ज": "જ", "त": "ત", "न": "ન", "प": "પ", "म": "મ", "ल": "લ",
              "व": "વ", "स": "સ", "र": "२"}
LOOKALIKE_TO_LETTER = {v: k for k, v in LOOKALIKES.items()}

# ---------------------------------------------------------------- Devanagari -> Latin
_VOWELS = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri", "ए": "e",
           "ऐ": "ai", "ओ": "o", "औ": "au"}
_CONS = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j",
         "झ": "jh", "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t",
         "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh",
         "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h"}
_SIGNS = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri", "े": "e", "ै": "ai",
          "ो": "o", "ौ": "au"}
_NASAL = {"ं": "n", "ँ": "n", "ः": "h"}
_NUKTA = "़"
_NUKTA_CONS = {"ड": "r", "ढ": "rh", "ज": "z", "फ": "f", "क": "q", "ख": "kh", "ग": "g"}
CONS = set(_CONS)


def _units(word):
    """Split into (consonant-or-vowel, vowel, explicit) units; explicit=False marks an inherent schwa."""
    units, i, n = [], 0, len(word)
    while i < n:
        ch = word[i]
        if ch in _CONS:
            c = _CONS[ch]
            if i + 1 < n and word[i + 1] == _NUKTA:
                c = _NUKTA_CONS.get(ch, c)
                i += 1
            nxt = word[i + 1] if i + 1 < n else ""
            if nxt == VIRAMA:
                units.append([c, "", True]); i += 2; continue
            if nxt in _SIGNS:
                units.append([c, _SIGNS[nxt], True]); i += 2; continue
            units.append([c, "a", False]); i += 1; continue
        if ch in _VOWELS:
            units.append(["", _VOWELS[ch], True])
        elif ch in _NASAL:
            if units:
                units[-1][1] += _NASAL[ch]
            else:
                units.append(["", _NASAL[ch], True])
        elif ch in _SIGNS:
            units.append(["", _SIGNS[ch], True])
        else:
            units.append([ch, "", True])
        i += 1
    return units


def to_latin(word):
    """Colloquial romanisation with schwa deletion (तुरंत -> turant, आपका -> aapka, करें -> karen)."""
    u = _units(word)
    for k, (c, v, explicit) in enumerate(u):
        if explicit or not c:
            continue
        last = k == len(u) - 1
        # inherent 'a' is dropped word-finally, and medially when the neighbours carry vowels
        if last and len(u) > 1:
            u[k][1] = ""
        elif 0 < k < len(u) - 1 and u[k - 1][1] and u[k + 1][0] and u[k + 1][1] and u[k + 1][2]:
            u[k][1] = ""
    s = "".join(c + v for c, v, _ in u)
    if s.endswith("aa") and len(s) > 3:
        s = s[:-1]                    # आपका -> aapka, the usual Hinglish spelling
    if s.endswith("ee") and len(s) > 3:
        s = s[:-2] + "i"              # गलती -> galti
    return s.replace("aai", "ai")     # बधाई -> badhai


# Common romanised-Hindi words, used by the language identifier to recognise Hinglish
ROMAN = {
    "aap", "aapka", "aapke", "aapki", "apna", "apne", "karo", "karein", "karen", "kare", "kijiye", "kar",
    "bhejo", "bhejein", "bhejen", "turant", "abhi", "paise", "paisa", "hai", "hain", "ho", "nahi", "nahin",
    "kya", "kyun", "mera", "meri", "mere", "tum", "tumhara", "hum", "yeh", "ye", "woh", "wo", "se", "ko",
    "ka", "ki", "ke", "mein", "par", "aur", "lekin", "jaldi", "bhai", "didi", "haan", "theek", "accha",
    "kal", "aaj", "raat", "din", "diya", "gaya", "hoga", "jayega", "jaega", "milega", "dhanyavaad",
    "shukriya", "kripya", "inaam", "badhai", "galti", "wapas", "vapas", "khata", "band", "jeete",
    "jeeta", "daalein", "daalen", "dalo", "liye", "sirf", "bas", "yahan", "wahan", "kaise", "kab",
}
ROMAN_RE = r"(iye$|ein$|enge$|ega$|egi$|jaye|unga$|wala$|wali$|chh|aap|kr$|bhej|kar[eo]$)"

SALIENT = {
    "तुरंत", "अभी", "पैसे", "पैसा", "इनाम", "जीते", "भेजें", "भेजो", "बधाई", "आखिरी", "काट", "ज़ब्त",
    "डालें", "पाने", "गलती", "वापस", "कमाएँ", "संदिग्ध", "बकाया", "भरें", "जाएगा", "दर्ज",
}
