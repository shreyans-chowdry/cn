"""
DNS client and server built directly on UDP sockets (RFC 1035) -- CN Module 7, Lab 9.

Client
  build_query / parse_message   wire format: header, question, resource records,
                                 name compression pointers (0xC0)
  Resolver.resolve(name, qtype) A / AAAA / CNAME / PTR / NS / TXT over UDP port 53,
                                 retransmission with timeout, transaction-ID check,
                                 TCP fallback when the TC (truncated) bit is set,
                                 TTL-aware positive and negative cache
  Resolver.reverse(ip)          PTR lookup via in-addr.arpa / ip6.arpa

Server
  DnsServer(zone)               authoritative answers for a small zone (A, AAAA, CNAME, PTR, TXT),
                                 NXDOMAIN otherwise, optional forwarding to an upstream resolver,
                                 serves UDP and TCP (2-byte length prefix), sets TC for big answers
"""
import asyncio
import random
import socket
import struct
import time

TYPES = {"A": 1, "NS": 2, "CNAME": 5, "PTR": 12, "TXT": 16, "AAAA": 28}
TYPE_NAMES = {v: k for k, v in TYPES.items()}
RCODES = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 4: "NOTIMP", 5: "REFUSED"}
HDR = struct.Struct("!HHHHHH")


# ---------------------------------------------------------------- wire format
def encode_name(name):
    out = bytearray()
    for label in name.rstrip(".").split("."):
        if label:
            b = label.encode("idna") if not label.isascii() else label.encode()
            if len(b) > 63:
                raise ValueError("label too long")
            out += bytes([len(b)]) + b
    return bytes(out + b"\x00")


def decode_name(msg, off):
    labels, jumped, end, hops = [], False, off, 0
    while True:
        n = msg[off]
        if n & 0xC0 == 0xC0:                            # compression pointer
            ptr = ((n & 0x3F) << 8) | msg[off + 1]
            if not jumped:
                end = off + 2
            off, jumped = ptr, True
            hops += 1
            if hops > 32:
                raise ValueError("compression loop")
            continue
        if n == 0:
            if not jumped:
                end = off + 1
            return ".".join(labels), end
        labels.append(msg[off + 1: off + 1 + n].decode("latin-1"))
        off += 1 + n


def build_query(name, qtype="A", tid=None, rd=True):
    tid = random.randrange(65536) if tid is None else tid
    flags = 0x0100 if rd else 0
    return tid, HDR.pack(tid, flags, 1, 0, 0, 0) + encode_name(name) + struct.pack("!HH", TYPES[qtype], 1)


def _rdata_to_text(rtype, msg, off, rdlen):
    rd = msg[off: off + rdlen]
    if rtype == 1:
        return socket.inet_ntop(socket.AF_INET, rd)
    if rtype == 28:
        return socket.inet_ntop(socket.AF_INET6, rd)
    if rtype in (2, 5, 12):
        return decode_name(msg, off)[0]
    if rtype == 16:
        out, i = [], 0
        while i < len(rd):
            n = rd[i]
            out.append(rd[i + 1: i + 1 + n].decode("utf-8", "replace"))
            i += 1 + n
        return "".join(out)
    return rd.hex()


def parse_message(msg):
    tid, flags, qd, an, ns, ar = HDR.unpack_from(msg)
    off = HDR.size
    questions = []
    for _ in range(qd):
        name, off = decode_name(msg, off)
        qtype, qclass = struct.unpack_from("!HH", msg, off)
        off += 4
        questions.append((name, TYPE_NAMES.get(qtype, qtype)))
    records = []
    for section, count in (("answer", an), ("authority", ns), ("additional", ar)):
        for _ in range(count):
            name, off = decode_name(msg, off)
            rtype, rclass, ttl, rdlen = struct.unpack_from("!HHIH", msg, off)
            off += 10
            records.append({"section": section, "name": name, "type": TYPE_NAMES.get(rtype, rtype),
                            "ttl": ttl, "data": _rdata_to_text(rtype, msg, off, rdlen)})
            off += rdlen
    return {"id": tid, "qr": bool(flags & 0x8000), "aa": bool(flags & 0x0400), "tc": bool(flags & 0x0200),
            "rd": bool(flags & 0x0100), "ra": bool(flags & 0x0080), "rcode": RCODES.get(flags & 0xF, flags & 0xF),
            "questions": questions, "records": records}


def reverse_name(ip):
    if ":" in ip:
        full = socket.inet_pton(socket.AF_INET6, ip).hex()
        return ".".join(reversed(full)) + ".ip6.arpa"
    return ".".join(reversed(ip.split("."))) + ".in-addr.arpa"


# ---------------------------------------------------------------- client
class DnsError(Exception):
    pass


class Resolver:
    def __init__(self, server=("8.8.8.8", 53), timeout=1.0, retries=2, use_cache=True):
        self.server, self.timeout, self.retries, self.use_cache = server, timeout, retries, use_cache
        self.cache = {}                       # (name, qtype) -> (expires_at, result)
        self.stats = {"queries": 0, "cache_hits": 0, "timeouts": 0, "tcp_fallbacks": 0}

    def _cache_get(self, key):
        hit = self.cache.get(key) if self.use_cache else None
        if hit and hit[0] > time.monotonic():
            self.stats["cache_hits"] += 1
            res = dict(hit[1])
            res["cached"] = True
            return res
        return None

    def _udp_exchange(self, query, tid):
        with socket.socket(socket.AF_INET6 if ":" in self.server[0] else socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(self.timeout)
            for attempt in range(self.retries + 1):
                s.sendto(query, self.server)
                try:
                    while True:
                        data, addr = s.recvfrom(4096)
                        if len(data) >= 2 and struct.unpack_from("!H", data)[0] == tid:
                            return data
                except socket.timeout:
                    self.stats["timeouts"] += 1
        raise DnsError(f"no answer from {self.server[0]}:{self.server[1]}")

    def _tcp_exchange(self, query):
        self.stats["tcp_fallbacks"] += 1
        with socket.create_connection(self.server, timeout=self.timeout * 2) as s:
            s.sendall(struct.pack("!H", len(query)) + query)
            n = struct.unpack("!H", _recv_exact(s, 2))[0]
            return _recv_exact(s, n)

    def resolve(self, name, qtype="A"):
        key = (name.lower().rstrip("."), qtype)
        cached = self._cache_get(key)
        if cached:
            return cached
        self.stats["queries"] += 1
        t0 = time.perf_counter()
        tid, q = build_query(name, qtype)
        data = self._udp_exchange(q, tid)
        msg = parse_message(data)
        udp_truncated = msg["tc"]
        if msg["tc"]:
            msg = parse_message(self._tcp_exchange(q))
        answers = [r for r in msg["records"] if r["section"] == "answer"]
        res = {"name": key[0], "type": qtype, "rcode": msg["rcode"], "authoritative": msg["aa"],
               "answers": answers, "addresses": [r["data"] for r in answers if r["type"] in ("A", "AAAA")],
               "cname_chain": [r["data"] for r in answers if r["type"] == "CNAME"],
               "min_ttl": min([r["ttl"] for r in answers], default=0),
               "elapsed_ms": round((time.perf_counter() - t0) * 1000, 3), "cached": False,
               "truncated_over_udp": udp_truncated}
        ttl = res["min_ttl"] if answers else 60                 # negative caching for NXDOMAIN
        if self.use_cache:
            self.cache[key] = (time.monotonic() + ttl, res)
        return res

    def reverse(self, ip):
        return self.resolve(reverse_name(ip), "PTR")


def _recv_exact(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise DnsError("connection closed")
        buf += chunk
    return buf


# ---------------------------------------------------------------- server
def _encode_rr(name, rtype, ttl, value):
    if rtype == "A":
        rd = socket.inet_pton(socket.AF_INET, value)
    elif rtype == "AAAA":
        rd = socket.inet_pton(socket.AF_INET6, value)
    elif rtype in ("CNAME", "PTR", "NS"):
        rd = encode_name(value)
    elif rtype == "TXT":
        b = value.encode()
        rd = b"".join(bytes([len(b[i:i + 255])]) + b[i:i + 255] for i in range(0, max(len(b), 1), 255))
    else:
        raise ValueError(rtype)
    return encode_name(name) + struct.pack("!HHIH", TYPES[rtype], 1, ttl, len(rd)) + rd


class DnsServer:
    """zone: {"name": [("A", "203.0.113.7", 300), ("CNAME", "other.name", 60), ...]}"""

    UDP_LIMIT = 512

    def __init__(self, zone, upstream=None, delay_ms=0.0):
        self.zone = {k.lower().rstrip("."): v for k, v in zone.items()}
        self.upstream = upstream
        self.delay_ms = delay_ms
        self.stats = {"queries": 0, "nxdomain": 0, "truncated": 0, "forwarded": 0, "tcp": 0}

    def _lookup(self, name, qtype, depth=0):
        recs = self.zone.get(name)
        if recs is None:
            return None
        out = [(name, t, v, ttl) for t, v, ttl in recs if t == qtype]
        if not out and depth < 8:
            for t, v, ttl in recs:
                if t == "CNAME":
                    tail = self._lookup(v.lower().rstrip("."), qtype, depth + 1) or []
                    return [(name, "CNAME", v, ttl)] + tail
        return out

    def answer(self, query, over_tcp=False):
        self.stats["queries"] += 1
        tid, flags, qd, *_ = HDR.unpack_from(query)
        name, off = decode_name(query, HDR.size)
        qtype_num, _ = struct.unpack_from("!HH", query, off)
        qsection = query[HDR.size: off + 4]
        qtype = TYPE_NAMES.get(qtype_num)
        key = name.lower().rstrip(".")
        recs = self._lookup(key, qtype) if qtype else None
        if recs is None and self.upstream:
            self.stats["forwarded"] += 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(2.0)
                    s.sendto(query, self.upstream)
                    return s.recvfrom(4096)[0]
            except OSError:
                pass
        rcode = 0 if recs is not None else 3
        self.stats["nxdomain"] += rcode == 3
        body = b"".join(_encode_rr(n, t, ttl, v) for n, t, v, ttl in (recs or []))
        rflags = 0x8000 | 0x0400 | (flags & 0x0100) | rcode
        resp = HDR.pack(tid, rflags, 1, len(recs or []), 0, 0) + qsection + body
        if not over_tcp and len(resp) > self.UDP_LIMIT:
            self.stats["truncated"] += 1
            resp = HDR.pack(tid, rflags | 0x0200, 1, 0, 0, 0) + qsection
        return resp

    async def start(self, host="127.0.0.1", port=0):
        loop = asyncio.get_running_loop()
        server = self

        class Udp(asyncio.DatagramProtocol):
            def connection_made(self, t):
                self.t = t

            def datagram_received(self, data, addr):
                try:
                    resp = server.answer(data)
                except Exception:
                    return
                if server.delay_ms:
                    loop.call_later(server.delay_ms / 1000, self.t.sendto, resp, addr)
                else:
                    self.t.sendto(resp, addr)

        self._udp, _ = await loop.create_datagram_endpoint(Udp, local_addr=(host, port))
        self.addr = self._udp.get_extra_info("sockname")[:2]

        async def tcp_handler(reader, writer):
            server.stats["tcp"] += 1
            try:
                n = struct.unpack("!H", await reader.readexactly(2))[0]
                resp = server.answer(await reader.readexactly(n), over_tcp=True)
                writer.write(struct.pack("!H", len(resp)) + resp)
                await writer.drain()
            finally:
                writer.close()

        self._tcp = await asyncio.start_server(tcp_handler, host, self.addr[1])
        return self.addr

    def close(self):
        self._udp.close()
        self._tcp.close()


def demo_zone():
    """A small zone used by the web demo, the tests and the experiments (documentation address
    ranges from RFC 5737 / RFC 3849, so nothing here points at a real host)."""
    return {
        "onlinesbi.sbi": [("A", "198.51.100.10", 3600), ("AAAA", "2001:db8::10", 3600)],
        "hdfcbank.com": [("A", "198.51.100.20", 3600)],
        "www.hdfcbank.com": [("CNAME", "hdfcbank.com", 3600)],
        "phon.pe": [("A", "198.51.100.30", 1800)],
        "sbi-kyc-update.xyz": [("A", "10.0.0.66", 60)],              # resolves into a private range
        "refundhdfc.click": [("A", "203.0.113.99", 30)],             # very short TTL
        "kyc.verify-hdfc.top": [("CNAME", "parking.example.net", 60)],
        "parking.example.net": [("A", "192.0.2.55", 60)],
        "10.100.51.198.in-addr.arpa": [("PTR", "onlinesbi.sbi", 3600)],
        "bigrecord.test": [("TXT", "v=spf1 " + "include:_spf.example.org " * 30, 300)],
    }
