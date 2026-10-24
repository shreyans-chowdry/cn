"""
Tamil script utilities shared by the data generator, the obfuscator, the language
identifier and the canonicaliser.

  * TAMIL_LETTER / is_tamil(): Unicode block U+0B80-U+0BFF
  * EN2TA: phonetic Tamil-script spellings of English banking loanwords
           ("account" -> அக்கவுண்ட்), as Tamil users sometimes type them
  * to_latin(): rule-based Tamil -> Latin transliteration in the colloquial
                "Tanglish" style (உங்கள் -> ungal), used by the L4 attack
  * CONFUSABLE / VOWEL_LENGTH: letter pairs Tamil writers commonly mix up
  * DIGIT_HOMOGLYPHS: Tamil digits that look like Tamil letters (௧ ~ க)
"""
import re

TA_LO, TA_HI = 0x0B80, 0x0BFF


def is_tamil_char(ch):
    return TA_LO <= ord(ch) <= TA_HI


def tamil_share(token):
    letters = [c for c in token if c.isalpha() or is_tamil_char(c)]
    return sum(is_tamil_char(c) for c in letters) / len(letters) if letters else 0.0


# ---------------------------------------------------------------- loanwords
EN2TA = {
    "account": "அக்கவுண்ட்", "kyc": "கேஒய்சி", "pin": "பின்", "otp": "ஓடிபி", "link": "லிங்க்",
    "block": "பிளாக்", "refund": "ரீஃபண்ட்", "cashback": "கேஷ்பேக்", "prize": "பிரைஸ்", "loan": "லோன்",
    "bank": "பேங்க்", "click": "கிளிக்", "update": "அப்டேட்", "upi": "யூபிஐ", "card": "கார்டு",
    "call": "கால்", "urgent": "அர்ஜென்ட்", "winner": "வின்னர்", "free": "ஃப்ரீ", "offer": "ஆஃபர்",
    "parcel": "பார்சல்", "fee": "ஃபீஸ்", "reward": "ரிவார்டு", "claim": "கிளெய்ம்", "police": "போலீஸ்",
    "job": "ஜாப்", "bill": "பில்", "lucky": "லக்கி", "cash": "கேஷ்", "request": "ரிக்வெஸ்ட்",
    "expire": "எக்ஸ்பையர்", "transfer": "டிரான்ஸ்ஃபர்", "whatsapp": "வாட்ஸ்அப்", "points": "பாயிண்ட்ஸ்",
    "verify": "வெரிஃபை", "approve": "அப்ரூவ்", "scan": "ஸ்கேன்", "qr": "கியூஆர்", "payment": "பேமெண்ட்",
    "recharge": "ரீசார்ஜ்", "plan": "பிளான்", "data": "டேட்டா", "order": "ஆர்டர்", "sale": "சேல்",
    "app": "ஆப்", "wallet": "வாலட்", "transaction": "டிரான்சாக்ஷன்", "credit": "கிரெடிட்", "debit": "டெபிட்",
    "register": "ரெஜிஸ்டர்", "download": "டவுன்லோடு", "customer": "கஸ்டமர்", "care": "கேர்",
    "connection": "கனெக்ஷன்", "electricity": "எலக்ட்ரிசிட்டி", "officer": "ஆபீசர்", "salary": "சம்பளம்",
    "enter": "என்டர்", "suspend": "சஸ்பெண்ட்", "contest": "கான்டெஸ்ட்", "screenshot": "ஸ்கிரீன்ஷாட்",
}
TA2EN = {v: k for k, v in EN2TA.items() if k != "salary"}

# ---------------------------------------------------------------- register (formal <-> colloquial)
REGISTER_VARIANTS = {
    "செய்யவும்": ["செய்யவும்", "செய்யுங்கள்", "செய்யுங்க", "பண்ணுங்க"],
    "செய்யுங்கள்": ["செய்யுங்கள்", "செய்யவும்", "செய்யுங்க", "பண்ணுங்க"],
    "அனுப்பவும்": ["அனுப்பவும்", "அனுப்புங்கள்", "அனுப்புங்க"],
    "அனுப்புங்கள்": ["அனுப்புங்கள்", "அனுப்பவும்", "அனுப்புங்க"],
    "உள்ளது": ["உள்ளது", "இருக்கு", "இருக்கிறது"],
    "உடனே": ["உடனே", "உடனடியாக"],
    "இப்போதே": ["இப்போதே", "இப்பவே", "உடனே"],
    "தயவுசெய்து": ["தயவுசெய்து", "please", "pls"],
    "நன்றி": ["நன்றி", "Thanks", "நன்றி!"],
    "வேண்டாம்": ["வேண்டாம்", "வேணாம்"],
    "பாருங்கள்": ["பாருங்கள்", "பாருங்க"],
    "வாருங்கள்": ["வாருங்கள்", "வாங்க"],
    "அழைக்கவும்": ["அழைக்கவும்", "call செய்யவும்", "அழையுங்கள்"],
    "பயன்படுத்தவும்": ["பயன்படுத்தவும்", "use செய்யவும்", "பயன்படுத்துங்கள்"],
}

# ---------------------------------------------------------------- orthographic confusions
CONFUSABLE = [("ல", "ள"), ("ள", "ழ"), ("ல", "ழ"), ("ண", "ன"), ("ந", "ன"), ("ண", "ந"), ("ர", "ற")]
VOWEL_LENGTH = [("ி", "ீ"), ("ு", "ூ"), ("ெ", "ே"), ("ொ", "ோ"), ("அ", "ஆ"), ("இ", "ஈ"), ("உ", "ஊ"), ("எ", "ஏ"), ("ஒ", "ஓ")]
PULLI = "்"
# Tamil digits that render almost identically to Tamil letters
DIGIT_HOMOGLYPHS = {"க": "௧", "உ": "௨", "எ": "௭", "அ": "௮", "ய": "௰"}
DIGIT_TO_LETTER = {v: k for k, v in DIGIT_HOMOGLYPHS.items()}

# ---------------------------------------------------------------- Tamil -> Latin transliteration
_VOWELS = {"அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo", "எ": "e", "ஏ": "e",
           "ஐ": "ai", "ஒ": "o", "ஓ": "o", "ஔ": "au", "ஃ": "h"}
_CONS = {"க": "k", "ங": "ng", "ச": "s", "ஞ": "nj", "ட": "d", "ண": "n", "த": "th", "ந": "n", "ப": "p",
         "ம": "m", "ய": "y", "ர": "r", "ல": "l", "வ": "v", "ழ": "zh", "ள": "l", "ற": "r", "ன": "n",
         "ஜ": "j", "ஷ": "sh", "ஸ": "s", "ஹ": "h"}
_SIGNS = {"ா": "aa", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo", "ெ": "e", "ே": "e", "ை": "ai",
          "ொ": "o", "ோ": "o", "ௌ": "au", PULLI: ""}
_FIX = [("ngk", "ng"), ("njs", "nj"), ("tth", "th"), ("dd", "tt"), ("rr", "tr"), ("ss", "ch"), ("nr", "ndr")]


def to_latin(word):
    """Colloquial romanisation of a Tamil-script word (உங்கள் -> ungal, பணம் -> panam)."""
    out, i = [], 0
    while i < len(word):
        ch = word[i]
        if ch in _CONS:
            nxt = word[i + 1] if i + 1 < len(word) else ""
            if nxt in _SIGNS:
                out.append(_CONS[ch] + _SIGNS[nxt])
                i += 2
                continue
            out.append(_CONS[ch] + "a")
        elif ch in _VOWELS:
            out.append(_VOWELS[ch])
        elif ch in _SIGNS:
            out.append(_SIGNS[ch])
        else:
            out.append(ch)
        i += 1
    s = "".join(out)
    for a, b in _FIX:
        s = s.replace(a, b)
    # word-final 'u' after a consonant cluster is how Tanglish writers spell the half-u (பணத்து -> panathu)
    return s


# Common romanised-Tamil words, used by the language identifier to recognise Tanglish
ROMAN_TAMIL = {
    "ungal", "unga", "ungaloda", "ungalukku", "naan", "nee", "neenga", "avar", "enna", "illa", "illai",
    "irukku", "iruku", "irukkum", "pannunga", "pannu", "panna", "seiyunga", "seyyavum", "udane", "ippove",
    "ippo", "inniku", "naalai", "panam", "kaasu", "anuppunga", "anuppu", "vandhu", "vanga", "ponga", "romba",
    "konjam", "mattum", "kitta", "kudunga", "solunga", "sollunga", "theriyuma", "aagidum", "aagiduchu",
    "vendaam", "venaam", "nandri", "vanakkam", "anna", "akka", "thambi", "da", "di", "machan", "dei",
    "seri", "sari", "paaru", "paarunga", "eppadi", "enga", "inga", "anga", "athu", "ithu", "intha", "antha",
}
