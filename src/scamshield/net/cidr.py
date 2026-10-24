"""
IPv4 / IPv6 addressing from first principles (CN Module 4, Lab 4): parsing, classful class,
classless (CIDR) prefix matching, subnet arithmetic and the special-purpose address registry
used to judge where a link in an SMS really points to.
"""


def ip_to_int(ip):
    """Return (version, integer). Accepts dotted-quad IPv4 and RFC 4291 IPv6 text (with ::)."""
    if ":" in ip:
        ip = ip.split("%")[0]
        if "." in ip:                                     # ::ffff:1.2.3.4
            head, v4 = ip.rsplit(":", 1)
            v = ip_to_int(v4)[1]
            ip = f"{head}:{v >> 16:x}:{v & 0xFFFF:x}"
        if ip.count("::") > 1:
            raise ValueError("bad IPv6")
        if "::" in ip:
            left, right = ip.split("::")
            lp = [p for p in left.split(":") if p]
            rp = [p for p in right.split(":") if p]
            parts = lp + ["0"] * (8 - len(lp) - len(rp)) + rp
        else:
            parts = ip.split(":")
        if len(parts) != 8:
            raise ValueError("bad IPv6")
        n = 0
        for p in parts:
            v = int(p, 16)
            if not 0 <= v <= 0xFFFF:
                raise ValueError("bad IPv6 group")
            n = (n << 16) | v
        return 6, n
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError("bad IPv4")
    n = 0
    for p in parts:
        if not p.isdigit() or int(p) > 255:
            raise ValueError("bad IPv4 octet")
        n = (n << 8) | int(p)
    return 4, n


def int_to_ip(version, n):
    if version == 4:
        return ".".join(str((n >> s) & 0xFF) for s in (24, 16, 8, 0))
    groups = [(n >> s) & 0xFFFF for s in range(112, -1, -16)]
    # compress the longest run of zero groups
    best, cur = (0, 0), (0, 0)
    for i, g in enumerate(groups + [1]):
        if g == 0 and i < 8:
            cur = (cur[0], cur[1] + 1) if cur[1] else (i, 1)
        else:
            if cur[1] > best[1]:
                best = cur
            cur = (0, 0)
    if best[1] > 1:
        left = ":".join(f"{g:x}" for g in groups[:best[0]])
        right = ":".join(f"{g:x}" for g in groups[best[0] + best[1]:])
        return f"{left}::{right}"
    return ":".join(f"{g:x}" for g in groups)


def is_ip(s):
    try:
        ip_to_int(s)
        return True
    except (ValueError, IndexError):
        return False


class Network:
    def __init__(self, cidr):
        addr, _, plen = cidr.partition("/")
        self.version, n = ip_to_int(addr)
        self.bits = 32 if self.version == 4 else 128
        self.prefix = int(plen) if plen else self.bits
        if not 0 <= self.prefix <= self.bits:
            raise ValueError("bad prefix length")
        self.mask = ((1 << self.prefix) - 1) << (self.bits - self.prefix)
        self.network = n & self.mask

    def __contains__(self, ip):
        v, n = ip_to_int(ip) if isinstance(ip, str) else ip
        return v == self.version and (n & self.mask) == self.network

    @property
    def broadcast(self):
        return self.network | (~self.mask & ((1 << self.bits) - 1))

    @property
    def num_addresses(self):
        return 1 << (self.bits - self.prefix)

    def usable_hosts(self):
        if self.version == 6:
            return self.num_addresses
        return max(self.num_addresses - 2, 0) if self.prefix < 31 else self.num_addresses

    def subnets(self, new_prefix):
        step = 1 << (self.bits - new_prefix)
        return [Network(f"{int_to_ip(self.version, self.network + i * step)}/{new_prefix}")
                for i in range(1 << (new_prefix - self.prefix))]

    def __str__(self):
        return f"{int_to_ip(self.version, self.network)}/{self.prefix}"

    def describe(self):
        d = {"cidr": str(self), "network": int_to_ip(self.version, self.network),
             "prefix": self.prefix, "addresses": self.num_addresses, "usable_hosts": self.usable_hosts()}
        if self.version == 4:
            d["netmask"] = int_to_ip(4, self.mask)
            d["broadcast"] = int_to_ip(4, self.broadcast)
        return d


def ipv4_class(ip):
    first = ip_to_int(ip)[1] >> 24
    return "A" if first < 128 else "B" if first < 192 else "C" if first < 224 else "D (multicast)" if first < 240 else "E (reserved)"


# Special-purpose ranges (RFC 6890 and friends). A link whose host resolves into one of these
# is not a normal public web server.
SPECIAL = [
    ("0.0.0.0/8", "this network"), ("10.0.0.0/8", "private (RFC 1918)"), ("100.64.0.0/10", "carrier-grade NAT"),
    ("127.0.0.0/8", "loopback"), ("169.254.0.0/16", "link-local"), ("172.16.0.0/12", "private (RFC 1918)"),
    ("192.0.0.0/24", "IETF protocol assignments"), ("192.0.2.0/24", "documentation (TEST-NET-1)"),
    ("192.168.0.0/16", "private (RFC 1918)"), ("198.18.0.0/15", "benchmarking"),
    ("198.51.100.0/24", "documentation (TEST-NET-2)"), ("203.0.113.0/24", "documentation (TEST-NET-3)"),
    ("224.0.0.0/4", "multicast"), ("240.0.0.0/4", "reserved"), ("255.255.255.255/32", "broadcast"),
    ("::1/128", "loopback"), ("::/128", "unspecified"), ("::ffff:0:0/96", "IPv4-mapped"),
    ("64:ff9b::/96", "NAT64"), ("fc00::/7", "unique local (private)"), ("fe80::/10", "link-local"),
    ("2001:db8::/32", "documentation"), ("ff00::/8", "multicast"),
]
_SPECIAL = [(Network(c), why) for c, why in SPECIAL]


def classify_ip(ip):
    """Longest-prefix match against the special-purpose registry."""
    v, n = ip_to_int(ip)
    best = None
    for net, why in _SPECIAL:
        if (v, n) in net and (best is None or net.prefix > best[0].prefix):
            best = (net, why)
    return {"ip": ip, "version": v, "special": best[1] if best else None,
            "matched_prefix": str(best[0]) if best else None, "public": best is None,
            "class": ipv4_class(ip) if v == 4 else None}
