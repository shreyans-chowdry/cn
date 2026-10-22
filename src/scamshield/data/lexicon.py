"""Slot vocabularies, natural spelling variation and native-script lexicons."""
import random
import string

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Bank", "PNB", "Bank of Baroda",
         "Canara Bank", "Indian Bank", "IOB", "Union Bank", "IDFC First", "Yes Bank", "Federal Bank"]
BANK_SLUG = {"SBI": "sbi", "HDFC Bank": "hdfc", "ICICI Bank": "icici", "Axis Bank": "axis",
             "Kotak Bank": "kotak", "PNB": "pnb", "Bank of Baroda": "bob", "Canara Bank": "canara",
             "Indian Bank": "indianbank", "IOB": "iob", "Union Bank": "unionbank",
             "IDFC First": "idfcfirst", "Yes Bank": "yesbank", "Federal Bank": "federal"}
APPS = ["PhonePe", "Google Pay", "GPay", "Paytm", "BHIM", "Amazon Pay", "CRED", "MobiKwik"]
UPI_HANDLES = ["ybl", "okaxis", "oksbi", "okhdfcbank", "paytm", "ibl", "axl", "upi", "apl"]
NAMES = ["Rahul", "Priya", "Karthik", "Anjali", "Suresh", "Divya", "Arjun", "Meena", "Sourav",
         "Ravi", "Lakshmi", "Vikram", "Pooja", "Arun", "Sneha", "Rohit", "Kavya", "Abhishek",
         "Deepa", "Sandeep", "Ananya", "Manoj", "Riya", "Ganesh", "Ishita", "Prakash", "Nandini",
         "Subhajit", "Tanmay", "Harsha", "Bhavana", "Imran", "Fatima", "Joseph", "Aditi"]
MERCHANTS = ["Swiggy", "Zomato", "BigBasket", "Reliance Digital", "Apollo Pharmacy", "Saravana Stores",
             "Flipkart", "Amazon", "Myntra", "Blinkit", "Zepto", "Croma", "DMart", "Nykaa",
             "Pothys", "Tanishq", "Ajio", "Meesho", "BookMyShow", "IRCTC"]
POWER_COS = ["TNEB", "TANGEDCO", "BESCOM", "Tata Power", "CESC", "TSSPDCL", "WBSEDCL", "MSEDCL",
             "BSES", "APSPDCL", "KSEB"]
TELCOS = ["Jio", "Airtel", "Vi", "BSNL"]
COURIERS = ["India Post", "BlueDart", "DTDC", "FedEx", "Delhivery", "Ekart"]
PRIZES = ["iPhone 16", "Rs.25,00,000", "Tata Nexon car", "Rs 10 lakh", "Royal Enfield bike",
          "Samsung Galaxy S25", "Rs.5,00,000 cash", "Maruti Swift"]
SHORTENERS = ["bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd", "t.ly"]
SCAM_TLDS = ["xyz", "top", "online", "info", "live", "site", "in.net", "co", "click", "support"]
SCAM_WORDS = ["kyc", "update", "verify", "reward", "secure", "help", "refund", "care", "login", "points"]
LEGIT_DOMAINS = ["onlinesbi.sbi", "hdfcbank.com/offers", "icicibank.com", "axisbank.com/offers",
                 "amzn.in/d", "fkrt.it", "myntr.it", "phon.pe", "paytm.me", "jio.com/r", "airtel.in/p",
                 "kotak.com/offers", "swiggy.onelink.me", "bankofbaroda.in"]


def _rand_code(rng, n=6):
    return "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(n))


def money(rng, lo=99, hi=99999):
    v = rng.randint(lo, hi)
    if rng.random() < 0.4:
        v = int(round(v, -2)) or v
    style = rng.random()
    if style < 0.3:
        return f"Rs.{v:,}"
    if style < 0.55:
        return f"Rs {v}"
    if style < 0.8:
        return f"₹{v:,}"
    if style < 0.9:
        return f"INR {v}.00"
    return f"Rs.{v}/-"


def phone(rng):
    num = str(rng.choice([6, 7, 8, 9])) + "".join(str(rng.randint(0, 9)) for _ in range(9))
    r = rng.random()
    if r < 0.3:
        return "+91" + num
    if r < 0.45:
        return "+91 " + num[:5] + " " + num[5:]
    return num


def helpline(rng):
    return rng.choice(["1800", "1860"]) + "-" + str(rng.randint(100, 999)) + "-" + str(rng.randint(1000, 9999))


def upi_id(rng):
    base = rng.choice(NAMES).lower()
    r = rng.random()
    if r < 0.4:
        base += str(rng.randint(1, 9999))
    elif r < 0.6:
        base = str(rng.randint(7000000000, 9999999999))
    elif r < 0.75:
        base += "." + rng.choice(NAMES).lower()
    return f"{base}@{rng.choice(UPI_HANDLES)}"


def scam_link(rng, bank):
    r = rng.random()
    if r < 0.35:
        return f"{rng.choice(['https://', 'http://', ''])}{rng.choice(SHORTENERS)}/{_rand_code(rng)}"
    slug = BANK_SLUG.get(bank, rng.choice(list(BANK_SLUG.values())))
    w = rng.choice(SCAM_WORDS)
    sep = rng.choice(["-", "", "."])
    host = f"{slug}{sep}{w}" if rng.random() < 0.6 else f"{w}{sep}{slug}"
    if rng.random() < 0.3:
        host += str(rng.randint(1, 99))
    return f"{rng.choice(['https://', 'http://', 'www.', ''])}{host}.{rng.choice(SCAM_TLDS)}" + (
        f"/{_rand_code(rng, 4)}" if rng.random() < 0.4 else "")


def legit_link(rng):
    if rng.random() < 0.25:
        return f"{rng.choice(['https://', ''])}{rng.choice(SHORTENERS)}/{_rand_code(rng)}"
    return f"{rng.choice(['https://', ''])}{rng.choice(LEGIT_DOMAINS)}/{_rand_code(rng, 5)}"


def date(rng):
    d, m = rng.randint(1, 28), rng.randint(1, 12)
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1]
    return rng.choice([f"{d:02d}-{m:02d}-26", f"{d:02d}{mon}26", f"{d} {mon}", f"{d:02d}/{m:02d}/2026"])


def fill_slots(rng, label):
    bank = rng.choice(BANKS)
    return {
        "amt": money(rng),
        "amt2": money(rng, 99, 4999),
        "bank": bank,
        "app": rng.choice(APPS),
        "upi": upi_id(rng),
        "acct": rng.choice(["XX", "XXXX", "**", "x"]) + str(rng.randint(1000, 9999)),
        "link": scam_link(rng, bank) if label == "scam" else legit_link(rng),
        "phone": phone(rng),
        "otp": str(rng.randint(100000, 999999)),
        "date": date(rng),
        "ref": str(rng.randint(10 ** 11, 10 ** 12 - 1)),
        "name": rng.choice(NAMES),
        "merchant": rng.choice(MERCHANTS),
        "company": rng.choice(POWER_COS),
        "company2": rng.choice(TELCOS),
        "job_amt": money(rng, 1500, 9000),
        "prize": rng.choice(PRIZES),
        "courier": rng.choice(COURIERS),
        "days": str(rng.choice([2, 3, 5, 7, 15, 28, 30])),
        "pct": str(rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 70])),
        "rate": rng.choice(["7.5", "8.25", "8.9", "9.5", "10.5"]),
        "bank_helpline": helpline(rng),
    }


# --- Natural spelling variation (part of *clean* data: how people really type) ---
NATURAL_VARIANTS = {
    "en": {"your": ["ur", "your"], "please": ["pls", "plz", "please"], "you": ["u", "you"],
           "immediately": ["immediately", "immediatly"], "now": ["now", "nw"], "money": ["money", "amt"],
           "message": ["msg"], "account": ["account", "a/c", "acc"], "number": ["no.", "number"]},
    "hi": {"hai": ["hai", "h", "he"], "nahi": ["nahi", "nhi", "nai"], "karein": ["karein", "karen", "kare", "kre"],
           "aapka": ["aapka", "apka"], "aapke": ["aapke", "apke"], "aapko": ["aapko", "apko"],
           "turant": ["turant", "turnt"], "paise": ["paise", "paisa", "pese"], "abhi": ["abhi", "abi"],
           "kar": ["kar", "kr"], "ke": ["ke", "k"], "liye": ["liye", "liya", "lie"], "bhej": ["bhej", "bej"],
           "please": ["pls", "plz", "please"], "hu": ["hu", "hoon", "hun"], "raha": ["raha", "rha"]},
    "ta": {"ungal": ["ungal", "unga", "ungaloda"], "pannunga": ["pannunga", "pannungo", "panunga"],
           "udane": ["udane", "udanae", "udanee"], "irukku": ["irukku", "iruku"], "illa": ["illa", "ila"],
           "inniku": ["inniku", "ennaiku", "inaiku"], "anuppunga": ["anuppunga", "anupunga"],
           "panam": ["panam", "panamu"], "please": ["pls", "plz", "please"], "romba": ["romba", "rmba"]},
    "bn": {"apnar": ["apnar", "aapnar"], "korun": ["korun", "koren", "korun"], "ekhuni": ["ekhuni", "ekhoni", "akhuni"],
           "taka": ["taka", "tk"], "hoyeche": ["hoyeche", "hoyechhe", "hoise"], "jonno": ["jonno", "jnno", "jonne"],
           "please": ["pls", "plz", "please"], "theke": ["theke", "thke"], "ache": ["ache", "achhe"]},
    "te": {"mee": ["mee", "mi"], "cheyandi": ["cheyandi", "cheyyandi", "cheyndi"], "ippude": ["ippude", "ipude"],
           "undi": ["undi", "undhi"], "ayyindi": ["ayyindi", "aindi", "ayindi"], "dabbulu": ["dabbulu", "dabbul"],
           "please": ["pls", "plz", "please"], "nunchi": ["nunchi", "nunci", "nundi"], "meeku": ["meeku", "miku"]},
}

# --- Native-script substitution for "mixed-script" natural messages ---
NATIVE_WORDS = {
    "hi": {"aapka": "आपका", "aapke": "आपके", "hai": "है", "karein": "करें", "turant": "तुरंत", "abhi": "अभी",
           "paise": "पैसे", "bhejein": "भेजें", "aaj": "आज", "raat": "रात", "ke": "के", "liye": "लिए",
           "nahi": "नहीं", "dhanyavaad": "धन्यवाद", "kisi": "किसी", "saath": "साथ", "me": "में", "ho": "हो",
           "gaye": "गए", "jayega": "जाएगा", "sirf": "सिर्फ", "din": "दिन", "se": "से", "ko": "को"},
    "ta": {"ungal": "உங்கள்", "udane": "உடனே", "pannunga": "பண்ணுங்க", "inniku": "இன்னிக்கு",
           "panam": "பணம்", "nandri": "நன்றி", "irukku": "இருக்கு", "illa": "இல்ல", "mattum": "மட்டும்",
           "anuppunga": "அனுப்புங்க", "aagiduchu": "ஆகிடுச்சு", "kitta": "கிட்ட", "naal": "நாள்",
           "ippove": "இப்போவே", "ungalukku": "உங்களுக்கு"},
    "bn": {"apnar": "আপনার", "korun": "করুন", "ekhuni": "এখুনি", "taka": "টাকা", "aaj": "আজ",
           "hoyeche": "হয়েছে", "dhonnobad": "ধন্যবাদ", "theke": "থেকে", "jonno": "জন্য", "shudhu": "শুধু",
           "pathan": "পাঠান", "ache": "আছে", "din": "দিন", "apni": "আপনি", "ei": "এই"},
    "te": {"mee": "మీ", "cheyandi": "చేయండి", "ippude": "ఇప్పుడే", "dabbulu": "డబ్బులు", "ayyindi": "అయ్యింది",
           "roju": "రోజు", "nunchi": "నుంచి", "kosam": "కోసం", "dhanyavadalu": "ధన్యవాదాలు",
           "matrame": "మాత్రమే", "undi": "ఉంది", "ki": "కి", "meeku": "మీకు", "lo": "లో"},
}

# Generic noise prefixes/suffixes shared across classes (prevents trivially separable sender cues)
PREFIXES = ["", "", "", "", "Dear user, ", "Hi, ", "Alert: ", "Info: ", "Imp: ", "Hello, "]
SUFFIXES = ["", "", "", "", " -Team", " Thanks.", " T&C", " Regards", " :)", " ."]
SENDER_IDS = ["AX-", "VM-", "JD-", "BZ-", "TM-", "AD-", "VK-", "CP-"]


def maybe_sender(rng, label):
    """Indian DLT sender headers (e.g. 'VM-SBIINB:'). Scammers frequently spoof them too."""
    if rng.random() < 0.25:
        hdr = rng.choice(SENDER_IDS) + "".join(rng.choice(string.ascii_uppercase) for _ in range(6))
        return hdr + ": "
    return ""
