"""
Impaired-link emulator: a UDP proxy placed between a client and a server.

It reproduces the transmission impairments of CN Module 2 / Module 6 on real sockets:
  * random loss (Bernoulli) and bursty loss (Gilbert-Elliott two-state model)
  * bit errors at a given bit-error rate (frames arrive corrupted; the CRC must catch them)
  * propagation delay + jitter (which also produces reordering)
  * a bottleneck link: service rate in datagrams/s with a finite drop-tail queue (congestion loss)

    client  <->  LossyUDPProxy(listen_port)  <->  server(server_addr)

Deterministic for a given seed, so experiments are repeatable.
"""
import asyncio
import random
from dataclasses import dataclass, field


@dataclass
class LinkConfig:
    loss: float = 0.0                 # Bernoulli loss probability per datagram
    ge_p_gb: float = 0.0              # Gilbert-Elliott: P(good -> bad) per datagram (0 disables)
    ge_p_bg: float = 0.3              # P(bad -> good)
    ge_loss_bad: float = 0.5          # loss probability while in the bad state
    ber: float = 0.0                  # bit error rate
    delay_ms: float = 0.0             # one-way propagation delay
    jitter_ms: float = 0.0            # uniform +/- jitter
    rate_pps: float = 0.0             # bottleneck service rate (datagrams/s), 0 = infinite
    queue: int = 64                   # bottleneck buffer (datagrams)
    reorder: bool = False             # allow jitter to reorder datagrams (False = FIFO, like one physical path)
    seed: int = 0


@dataclass
class LinkStats:
    forwarded: int = 0
    dropped_loss: int = 0
    dropped_queue: int = 0
    corrupted: int = 0
    bytes: int = 0
    by_dir: dict = field(default_factory=lambda: {"up": 0, "down": 0})


class _Direction:
    """One direction of the link with its own bottleneck queue."""

    def __init__(self, proxy, name):
        self.p, self.name = proxy, name
        self.queue_len = 0
        self.next_free = 0.0
        self.last_delivery = 0.0
        self.bad = False

    def _lost(self):
        c, rng = self.p.cfg, self.p.rng
        if c.ge_p_gb > 0:
            self.bad = (rng.random() >= c.ge_p_bg) if self.bad else (rng.random() < c.ge_p_gb)
            if self.bad and rng.random() < c.ge_loss_bad:
                return True
        return rng.random() < c.loss

    def _corrupt(self, data):
        c, rng = self.p.cfg, self.p.rng
        if c.ber <= 0:
            return data, False
        n_bits = len(data) * 8
        # number of flipped bits ~ Binomial(n_bits, ber); sample positions directly
        flips = [i for i in range(n_bits) if rng.random() < c.ber] if c.ber > 1e-3 else \
            [rng.randrange(n_bits) for _ in range(_poisson(rng, n_bits * c.ber))]
        if not flips:
            return data, False
        b = bytearray(data)
        for i in flips:
            b[i // 8] ^= 1 << (i % 8)
        return bytes(b), True

    def submit(self, data, deliver):
        c, loop, st = self.p.cfg, asyncio.get_running_loop(), self.p.stats
        if self._lost():
            st.dropped_loss += 1
            return
        now = loop.time()
        wait = 0.0
        if c.rate_pps > 0:
            if self.queue_len >= c.queue:
                st.dropped_queue += 1
                return
            start = max(now, self.next_free)
            self.next_free = start + 1.0 / c.rate_pps
            wait = self.next_free - now
            self.queue_len += 1
        data, bad = self._corrupt(data)
        st.corrupted += bad
        delay = wait + max(0.0, c.delay_ms + self.p.rng.uniform(-c.jitter_ms, c.jitter_ms)) / 1000.0
        deadline = now + delay
        if not c.reorder:                                   # keep FIFO order: never overtake the previous datagram
            deadline = max(deadline, self.last_delivery + 1e-6)
            self.last_delivery = deadline

        def _go():
            if c.rate_pps > 0:
                self.queue_len -= 1
            st.forwarded += 1
            st.bytes += len(data)
            st.by_dir[self.name] += 1
            deliver(data)

        loop.call_at(deadline, _go)               # absolute time, so FIFO order is exact


def _poisson(rng, lam):
    import math
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


class LossyUDPProxy:
    def __init__(self, server_addr, cfg: LinkConfig = None):
        self.server_addr = server_addr
        self.cfg = cfg or LinkConfig()
        self.rng = random.Random(self.cfg.seed)
        self.stats = LinkStats()
        self.up, self.down = _Direction(self, "up"), _Direction(self, "down")
        self._client_side = None
        self._server_side = {}

    async def start(self, host="127.0.0.1", port=0):
        loop = asyncio.get_running_loop()
        proxy = self

        class ClientFacing(asyncio.DatagramProtocol):
            def connection_made(self, transport):
                proxy._client_side = transport

            def datagram_received(self, data, addr):
                proxy._from_client(data, addr)

        await loop.create_datagram_endpoint(ClientFacing, local_addr=(host, port))
        self.addr = self._client_side.get_extra_info("sockname")[:2]
        return self.addr

    def _from_client(self, data, client_addr):
        loop = asyncio.get_running_loop()
        if client_addr not in self._server_side:
            proxy = self

            class ServerFacing(asyncio.DatagramProtocol):
                def datagram_received(self, d, addr):
                    proxy.down.submit(d, lambda x: proxy._client_side.is_closing() or proxy._client_side.sendto(x, client_addr))

            fut = loop.create_datagram_endpoint(ServerFacing, remote_addr=self.server_addr)
            self._server_side[client_addr] = asyncio.ensure_future(fut)
        task = self._server_side[client_addr]

        def _send(x):
            async def _do():
                transport, _ = await task
                if not transport.is_closing():
                    transport.sendto(x)
            asyncio.ensure_future(_do())

        self.up.submit(data, _send)

    def close(self):
        if self._client_side:
            self._client_side.close()
        for t in self._server_side.values():
            if t.done() and not t.exception():
                t.result()[0].close()
