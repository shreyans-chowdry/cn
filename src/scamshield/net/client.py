"""
Clients for the ScamShield services.

    python -m scamshield.net.client tcp  "message text"            [--host 127.0.0.1 --port 9099]
    python -m scamshield.net.client udp  "message text"            [--port 9098]
    python -m scamshield.net.client batch messages.txt --arq sr --window 8 [--port 9098]
    python -m scamshield.net.client ping --count 10                (RTT over TCP)
    python -m scamshield.net.client dns  sbi-kyc-update.xyz [--type A] [--server 127.0.0.1:5353]
"""
import argparse
import asyncio
import json
import socket
import statistics
import time

from . import protocol as P
from .arq import ArqEndpoint


class TcpClient:
    def __init__(self, host="127.0.0.1", port=9099, timeout=5.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.dec = P.StreamDecoder()
        self.seq = 0
        self.pending = []

    def _read_frame(self):
        while not self.pending:
            data = self.sock.recv(65536)
            if not data:
                raise ConnectionError("server closed the connection")
            self.pending.extend(self.dec.feed(data))
        return self.pending.pop(0)

    def classify(self, text, explain=False, dns=True):
        self.seq += 1
        self.sock.sendall(P.encode(P.FrameType.CLASSIFY_REQ, {"id": self.seq, "text": text, "explain": explain, "dns": dns},
                                   seq=self.seq))
        return self._read_frame().json()

    def classify_many(self, texts, dns=False):
        """Pipelined: write all requests, then read all responses (one TCP connection)."""
        frames = b"".join(P.encode(P.FrameType.CLASSIFY_REQ, {"id": i, "text": t, "dns": dns}, seq=i)
                          for i, t in enumerate(texts))
        self.sock.sendall(frames)
        return [self._read_frame().json() for _ in texts]

    def ping(self):
        self.seq += 1
        t0 = time.perf_counter()
        self.sock.sendall(P.encode(P.FrameType.PING, b"x", seq=self.seq))
        self._read_frame()
        return (time.perf_counter() - t0) * 1000

    def close(self):
        self.sock.close()


def udp_classify(text, host="127.0.0.1", port=9098, timeout=1.0, retries=3, dns=True):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        seq = int(time.time() * 1000) & 0xFFFFFFFF
        frame = P.encode(P.FrameType.CLASSIFY_REQ, {"id": seq, "text": text, "dns": dns}, seq=seq)
        for _ in range(retries + 1):
            s.sendto(frame, (host, port))
            try:
                while True:
                    data, _ = s.recvfrom(65536)
                    f = P.decode(data)
                    if f.seq == seq:
                        return f.json()
            except (socket.timeout, P.FrameError):
                continue
    raise TimeoutError("no response")


class ArqClient:
    """Reliable batch classification over UDP (Go-Back-N / Selective Repeat / Stop-and-Wait)."""

    def __init__(self, server, mode="sr", window=8, congestion="fixed", **kw):
        self.server, self.mode, self.window, self.congestion, self.kw = server, mode, window, congestion, kw

    async def run(self, texts, dns=False, timeout=600):
        loop = asyncio.get_running_loop()
        holder = {}

        class Proto(asyncio.DatagramProtocol):
            def datagram_received(self, data, addr):
                holder["ep"].datagram_received(data)

        transport, _ = await loop.create_datagram_endpoint(Proto, remote_addr=self.server)
        ep = ArqEndpoint(transport.sendto, mode=self.mode, window=self.window, congestion=self.congestion, **self.kw)
        holder["ep"] = ep
        t0 = time.perf_counter()
        results = {}

        async def receiver():
            while len(results) < len(texts):
                f = await ep.recv()
                r = f.json()
                results[r["id"]] = r

        rx = asyncio.ensure_future(receiver())
        for i, t in enumerate(texts):
            await ep.send({"id": i, "text": t, "dns": dns})
        try:
            await asyncio.wait_for(rx, timeout)
            await ep.drain(timeout=30)
        finally:
            elapsed = time.perf_counter() - t0
            ep.close()
            transport.close()
        return [results[i] for i in range(len(texts))], elapsed, ep.stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["tcp", "udp", "batch", "ping", "dns"])
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int)
    ap.add_argument("--arq", default="sr", choices=["saw", "gbn", "sr"])
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--type", default="A")
    ap.add_argument("--server", default="127.0.0.1:5353")
    a = ap.parse_args()
    if a.mode == "tcp":
        c = TcpClient(a.host, a.port or 9099)
        print(json.dumps(c.classify(a.arg, explain=True), ensure_ascii=False, indent=1))
    elif a.mode == "udp":
        print(json.dumps(udp_classify(a.arg, a.host, a.port or 9098), ensure_ascii=False, indent=1))
    elif a.mode == "ping":
        c = TcpClient(a.host, a.port or 9099)
        rtts = [c.ping() for _ in range(a.count)]
        print(f"rtt min/avg/max = {min(rtts):.3f}/{statistics.mean(rtts):.3f}/{max(rtts):.3f} ms")
    elif a.mode == "batch":
        texts = [l.strip() for l in open(a.arg, encoding="utf-8") if l.strip()]
        res, el, st = asyncio.run(ArqClient((a.host, a.port or 9098), a.arq, a.window).run(texts))
        for t, r in zip(texts, res):
            print(f"{r['label']:6s} {t[:80]}")
        print(f"{len(texts)} messages in {el:.2f}s, retransmissions={st.retransmissions}, timeouts={st.timeouts}")
    elif a.mode == "dns":
        from .dns import Resolver
        h, p = a.server.rsplit(":", 1)
        r = Resolver((h, int(p)))
        res = r.reverse(a.arg) if a.type == "PTR" else r.resolve(a.arg, a.type)
        print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
