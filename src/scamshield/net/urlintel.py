"""
Link intelligence: look past the words of an SMS at where its links actually point.

For every URL / bare domain / IP literal in a message:
  lexical  : URL shortener, raw IP host, punycode or non-ASCII (IDN homograph) host, risky TLD,
             brand look-alike (bank or app name inside a domain that is not the official one),
             many hyphens / digits, deep subdomains, http instead of https
  network  : DNS resolution with our own resolver (NXDOMAIN, CNAME chain, very short TTL,
             IPv4 vs IPv6), and CIDR classification of every resolved address (private,
             loopback, link-local, CGNAT ... a public link should never resolve there)

The result is a link-risk score in [0, 1] plus human-readable reasons, which the detector
fuses with the text classifier.
"""
import re
import unicodedata

from . import cidr

SHORTENERS = {"bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd", "t.ly", "goo.gl", "ow.ly", "shorturl.at",
              "tiny.cc", "s.id", "rebrand.ly", "t.co"}
RISKY_TLDS = {"xyz", "top", "online", "info", "live", "site", "click", "support", "buzz", "icu", "rest", "monster",
              "cam", "work", "loan", "win", "bid", "vip", "shop", "cyou", "sbs", "fun"}
OFFICIAL = {
    "sbi": {"sbi", "onlinesbi.sbi", "sbi.co.in", "onlinesbi.com"}, "hdfc": {"hdfcbank.com"},
    "icici": {"icicibank.com"}, "axis": {"axisbank.com"}, "kotak": {"kotak.com"}, "pnb": {"pnbindia.in"},
    "bob": {"bankofbaroda.in"}, "canara": {"canarabank.com"}, "paytm": {"paytm.com", "paytm.me"},
    "phonepe": {"phonepe.com", "phon.pe"}, "gpay": {"pay.google.com"}, "amazon": {"amazon.in", "amzn.in"},
    "flipkart": {"flipkart.com", "fkrt.it"}, "jio": {"jio.com"}, "airtel": {"airtel.in"}, "npci": {"npci.org.in"},
    "indianbank": {"indianbank.in"}, "iob": {"iob.in"}, "unionbank": {"unionbankofindia.co.in"},
    "idfcfirst": {"idfcfirstbank.com"}, "yesbank": {"yesbank.in"}, "federal": {"federalbank.co.in"},
}
RISKY_SPECIAL = ("private", "loopback", "link-local", "carrier-grade", "unspecified", "this network",
                 "reserved", "multicast", "broadcast", "unique local")

_URL_RE = re.compile(
    r"(?:(?:https?://)|(?:www\.))?"
    r"(?:\[[0-9a-fA-F:]+\]|(?:\d{1,3}\.){3}\d{1,3}|(?:[\w\-]+\.)+[A-Za-z¡-￿]{2,}|xn--[\w\-]+(?:\.[\w\-]+)+)"
    r"(?::\d{2,5})?(?:/[^\s]*)?", re.UNICODE)


def extract_urls(text):
    out = []
    for m in _URL_RE.finditer(text):
        u = re.sub(r"-[\u0900-\u0DFF]+$", "", m.group(0)).rstrip(".,;:!?)'\"।")   # drop a native case suffix (link-ல்)
        if "@" in text[max(0, m.start() - 1): m.start()]:
            continue                                     # part of a UPI ID / e-mail
        host = re.sub(r"^https?://", "", u, flags=re.I).split("/")[0].split(":")[0].strip("[]").lower()
        if cidr.is_ip(host):
            out.append({"url": u, "host": host})
            continue
        if "." not in host or host.replace(".", "").isdigit():
            continue
        tld = host.rsplit(".", 1)[-1]
        if len(tld) < 2 or tld.isdigit():
            continue
        if re.fullmatch(r"(rs|inr|a/c|no|ref|avl|bal)", host.split(".")[0]):
            continue
        out.append({"url": u, "host": host})
    return out


def _registered_domain(host):
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "org", "net", "gov", "ac") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def lexical_features(url, host):
    reasons, score = [], 0.0
    reg = _registered_domain(host)
    tld = host.rsplit(".", 1)[-1]
    if cidr.is_ip(host):
        reasons.append("link uses a raw IP address instead of a domain name")
        score += 0.45
        info = cidr.classify_ip(host)
        if info["special"] and any(k in info["special"] for k in RISKY_SPECIAL):
            reasons.append(f"IP is in a {info['special']} range ({info['matched_prefix']})")
            score += 0.3
    if reg in SHORTENERS:
        reasons.append(f"URL shortener ({reg}) hides the real destination")
        score += 0.25
    if host.startswith("xn--") or ".xn--" in host or not host.isascii():
        reasons.append("internationalised (punycode) domain, possible look-alike letters")
        score += 0.35
    if tld in RISKY_TLDS:
        reasons.append(f".{tld} is a top-level domain heavily used for throwaway scam sites")
        score += 0.3
    compact = re.sub(r"[^a-z]", "", host)
    for brand, official in OFFICIAL.items():
        if brand in compact and reg not in official and host not in official:
            reasons.append(f"mentions '{brand}' but is not an official {brand} domain")
            score += 0.45
            break
    if host.count("-") >= 2 or sum(c.isdigit() for c in reg) >= 3:
        reasons.append("many hyphens or digits in the domain")
        score += 0.1
    if host.count(".") >= 3 and not cidr.is_ip(host):
        reasons.append("deeply nested subdomain")
        score += 0.1
    if url.lower().startswith("http://"):
        reasons.append("plain http (no TLS)")
        score += 0.05
    return min(score, 1.0), reasons


def network_features(host, resolver):
    """DNS + CIDR checks. Returns (score, reasons, dns_info) -- never raises."""
    if resolver is None or cidr.is_ip(host):
        return 0.0, [], None
    reasons, score = [], 0.0
    try:
        a = resolver.resolve(host, "A")
    except Exception as e:                       # resolver unreachable: no evidence either way
        return 0.0, [], {"error": str(e)}
    info = {"rcode": a["rcode"], "addresses": a["addresses"], "cname_chain": a["cname_chain"],
            "min_ttl": a["min_ttl"], "elapsed_ms": a["elapsed_ms"], "cached": a["cached"]}
    if a["rcode"] == "NXDOMAIN":
        reasons.append("domain does not exist in DNS (NXDOMAIN): taken down or never registered")
        score += 0.35
    if a["addresses"] and 0 < a["min_ttl"] < 120:
        reasons.append(f"very short DNS TTL ({a['min_ttl']} s), typical of fast-flux hosting")
        score += 0.15
    if len(a["cname_chain"]) >= 1 and a["addresses"]:
        info["final_host"] = a["cname_chain"][-1]
    for ip in a["addresses"]:
        c = cidr.classify_ip(ip)
        if c["special"] and any(k in c["special"] for k in RISKY_SPECIAL):
            reasons.append(f"resolves to {ip}, a {c['special']} address ({c['matched_prefix']})")
            score += 0.4
            break
    try:
        aaaa = resolver.resolve(host, "AAAA")
        info["ipv6"] = aaaa["addresses"]
    except Exception:
        info["ipv6"] = []
    return min(score, 1.0), reasons, info


def analyse(text, resolver=None):
    links = []
    for u in extract_urls(text):
        s_lex, r_lex = lexical_features(u["url"], u["host"])
        s_net, r_net, dns_info = network_features(u["host"], resolver)
        links.append({"url": u["url"], "host": u["host"], "risk": round(min(1.0, s_lex + s_net), 3),
                      "reasons": r_lex + r_net, "dns": dns_info})
    return {"links": links, "risk": max((l["risk"] for l in links), default=0.0)}


def has_homoglyph_host(host):
    return any(unicodedata.name(c, "").startswith(("CYRILLIC", "GREEK")) for c in host)
