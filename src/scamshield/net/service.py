"""
ScamShield network services: the detector exposed over the transport layer.

    python -m scamshield.net.service --tcp 9099 --udp 9098 --dns 5353

  TCP 9099   SSP frames on a byte stream: CLASSIFY_REQ -> CLASSIFY_RESP, PING -> PONG.
             Requests can be pipelined; StreamDecoder re-assembles frames TCP splits or merges.
             This is the port the Android app's "server mode" connects to.
  UDP 9098   two modes, chosen per datagram:
               * plain request/response: one CLASSIFY_REQ datagram -> one CLASSIFY_RESP datagram
                 (client retries on timeout, like DNS)
               * reliable batches: DATA frames carrying requests, delivered by the ARQ layer
                 (Go-Back-N or Selective Repeat, chosen by the client's flag bits); each request's
                 verdict is sent back as a DATA frame on the reverse ARQ channel
  UDP/TCP 5353  the demo DNS server (authoritative for scamshield.demo_zone) used for link checks

Every frame carries a CRC-32; corrupted frames are counted and dropped.
"""
import argparse
import asyncio
import json
import time

from . import protocol as P
from .arq import ArqEndpoint


class Handler:
    """Turns a request dict into a response dict using a detector (or a stub for transport experiments)."""

    def __init__(self, detector=None, stub=False):
        self.detector = detector
        self.stub = stub
        self.served = 0

    def __call__(self, req):
        self.served += 1
        text = req.get("text", "")
        if self.stub or self.detector is None:
            return {"id": req.get("id"), "label": "legit", "probs": {}, "stub": True}
        r = self.detector.analyse(text, use_dns=req.get("dns", True), explain=req.get("explain", False))
        r["id"] = req.get("id")
        r.pop("normalized", None)
        if not req.get("explain", False):
            r["language"] = {k: v for k, v in r["language"].items() if k != "tokens"}
        return r


class Stats:
    def __init__(self):
        self.tcp_conn = self.tcp_frames = self.udp_frames = self.corrupted = self.arq_peers = 0
        self.started = time.time()

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items()}


async def start_tcp(handler, host="0.0.0.0", port=9099, stats=None):
    stats = stats or Stats()

    async def client(reader, writer):
        stats.tcp_conn += 1
        dec = P.StreamDecoder()
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                try:
                    frames = dec.feed(data)
                except P.FrameError:
                    stats.corrupted += 1
                    writer.write(P.encode(P.FrameType.ERROR, {"error": "corrupt frame"}))
                    dec = P.StreamDecoder()
                    continue
                for f in frames:
                    stats.tcp_frames += 1
                    if f.type == P.FrameType.PING:
                        writer.write(P.encode(P.FrameType.PONG, f.payload, seq=f.seq))
                    elif f.type == P.FrameType.CLASSIFY_REQ:
                        resp = await asyncio.get_running_loop().run_in_executor(None, handler, f.json())
                        writer.write(P.encode(P.FrameType.CLASSIFY_RESP, resp, seq=f.seq, ack=f.seq))
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()

    server = await asyncio.start_server(client, host, port)
    return server, stats


class _UdpService(asyncio.DatagramProtocol):
    def __init__(self, handler, stats, arq_kwargs):
        self.handler, self.stats, self.arq_kwargs = handler, stats, arq_kwargs
        self.peers = {}

    def connection_made(self, transport):
        self.t = transport

    def _endpoint(self, addr, flags):
        ep = self.peers.get(addr)
        if ep is None:
            mode = "sr" if flags & P.Flag.SR else "gbn"
            ep = ArqEndpoint(lambda d, a=addr: self.t.is_closing() or self.t.sendto(d, a), mode=mode,
                             on_dead=lambda e, a=addr: self._drop(a), **self.arq_kwargs)
            self.peers[addr] = ep
            self.stats.arq_peers += 1
            ep.app_task = asyncio.ensure_future(self._serve_arq(ep))
        return ep

    def _drop(self, addr):
        ep = self.peers.pop(addr, None)
        if ep:
            ep.close()
            task = getattr(ep, "app_task", None)
            if task:
                task.cancel()

    def close_all(self):
        for addr in list(self.peers):
            self._drop(addr)

    def _reap_idle(self, idle_s=10.0):
        now = time.monotonic()
        for addr, ep in list(self.peers.items()):
            if not ep.unacked and now - ep.last_activity > idle_s:
                self._drop(addr)

    async def _serve_arq(self, ep):
        while True:
            f = await ep.recv()
            req = f.json()
            resp = self.handler(req)
            await ep.send(resp)

    def datagram_received(self, data, addr):
        self.stats.udp_frames += 1
        if self.stats.udp_frames % 500 == 0:
            self._reap_idle()
        try:
            f = P.decode(data)
        except P.FrameError:
            self.stats.corrupted += 1
            return
        if f.type in (P.FrameType.DATA, P.FrameType.ACK):
            self._endpoint(addr, f.flags).datagram_received(data)
        elif f.type == P.FrameType.CLASSIFY_REQ:
            resp = self.handler(f.json())
            self.t.sendto(P.encode(P.FrameType.CLASSIFY_RESP, resp, seq=f.seq, ack=f.seq), addr)
        elif f.type == P.FrameType.PING:
            self.t.sendto(P.encode(P.FrameType.PONG, f.payload, seq=f.seq), addr)


async def start_udp(handler, host="0.0.0.0", port=9098, stats=None, **arq_kwargs):
    stats = stats or Stats()
    loop = asyncio.get_running_loop()
    transport, proto = await loop.create_datagram_endpoint(lambda: _UdpService(handler, stats, arq_kwargs),
                                                           local_addr=(host, port))
    return transport, proto, stats


async def serve(tcp_port, udp_port, dns_port, host, stub):
    from .dns import DnsServer, Resolver, demo_zone
    resolver = None
    if dns_port:
        dns = DnsServer(demo_zone())
        await dns.start(host, dns_port)
        resolver = Resolver(("127.0.0.1", dns_port), timeout=0.5, retries=1)
        print(f"[ScamShield] DNS server (demo zone) on udp/tcp {dns_port}")
    detector = None
    if not stub:
        from ..detector import Detector
        detector = Detector(resolver=resolver)
    handler = Handler(detector, stub=stub)
    stats = Stats()
    tcp, _ = await start_tcp(handler, host, tcp_port, stats)
    await start_udp(handler, host, udp_port, stats)
    print(f"[ScamShield] SSP over TCP on {host}:{tcp_port}, over UDP on {host}:{udp_port}")
    async with tcp:
        await tcp.serve_forever()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--tcp", type=int, default=9099)
    ap.add_argument("--udp", type=int, default=9098)
    ap.add_argument("--dns", type=int, default=5353, help="0 disables the demo DNS server")
    ap.add_argument("--stub", action="store_true", help="answer without the model (transport testing)")
    a = ap.parse_args()
    try:
        asyncio.run(serve(a.tcp, a.udp, a.dns, a.host, a.stub))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
