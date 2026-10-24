"""
Reliable delivery over UDP: sliding-window ARQ (CN Module 3 flow control, Module 6 transport).

    ArqEndpoint(mode="saw" | "gbn" | "sr", window=W, congestion="fixed" | "aimd")

  saw   Stop-and-Wait            window 1
  gbn   Go-Back-N                cumulative ACKs, one timer, resend the whole window on timeout
  sr    Selective Repeat         per-frame ACKs and timers, receiver buffers out-of-order frames

Shared machinery
  * adaptive retransmission timeout (Jacobson/Karels): SRTT, RTTVAR, RTO = SRTT + 4*RTTVAR,
    Karn's rule (no RTT samples from retransmitted frames), exponential back-off on timeout
  * flow control: the receiver advertises its free buffer (WIN field); the sender never has
    more than min(window, cwnd, advertised window) frames outstanding
  * optional AIMD congestion control (TCP Tahoe style): slow start, congestion avoidance,
    cwnd -> 1 and ssthresh -> cwnd/2 on a timeout
  * CRC-32 on every frame; corrupted frames are dropped and recovered by retransmission

One endpoint is full duplex: it sends DATA frames and receives ACKs for them, and receives
DATA frames and sends ACKs for those. Delivered messages appear in order on `recv()`.
"""
import asyncio
import time
from dataclasses import dataclass, field

from . import protocol as P

MODES = ("saw", "gbn", "sr")


@dataclass
class ArqStats:
    data_sent: int = 0
    retransmissions: int = 0
    timeouts: int = 0
    acks_sent: int = 0
    acks_received: int = 0
    corrupted: int = 0
    duplicates: int = 0
    out_of_order_buffered: int = 0
    discarded_out_of_order: int = 0
    delivered: int = 0
    rtt_samples: list = field(default_factory=list)
    cwnd_trace: list = field(default_factory=list)


class ArqEndpoint:
    def __init__(self, send_datagram, mode="sr", window=8, congestion="fixed", rto=0.2,
                 min_rto=0.02, max_rto=2.0, rcv_buffer=64, max_retries=15, on_dead=None):
        assert mode in MODES
        self._tx = send_datagram
        self.mode = mode
        self.window = 1 if mode == "saw" else window
        self.congestion = congestion
        self.stats = ArqStats()
        # sender
        self.base = 0
        self.next_seq = 0
        self.unacked = {}                 # seq -> [bytes, sent_time, retransmitted?]
        self.acked = set()                # SR: acked but not yet slid past
        self.send_q = asyncio.Queue()
        self.peer_window = rcv_buffer
        self.srtt, self.rttvar, self.rto = None, None, rto
        self.min_rto, self.max_rto = min_rto, max_rto
        self.max_retries = max_retries
        self.on_dead = on_dead
        self.dead = False
        self.last_activity = time.monotonic()
        self.cwnd = 1.0 if congestion == "aimd" else float(self.window)
        self.ssthresh = float(max(self.window, 2)) if congestion == "aimd" else float("inf")
        self._timers = {}
        self._space = asyncio.Event()
        self._space.set()
        self._all_acked = asyncio.Event()
        self._all_acked.set()
        self._pending = 0                 # accepted by send() but not yet transmitted
        self._recover = 0                 # AIMD: no further decrease until this seq is acked
        # receiver
        self.rcv_base = 0
        self.rcv_buf = {}
        self.rcv_buffer = rcv_buffer
        self.delivered = asyncio.Queue()
        self._pump = asyncio.ensure_future(self._sender_loop())

    # ---------------------------------------------------------------- sender side
    def _flags(self):
        return P.Flag.SR if self.mode == "sr" else P.Flag.GBN

    def _effective_window(self):
        return max(1, int(min(self.window, self.cwnd, max(1, self.peer_window))))

    async def send(self, payload):
        """Queue an application message (dict/str/bytes) for reliable delivery."""
        self._all_acked.clear()
        self._pending += 1
        await self.send_q.put(payload)

    async def _sender_loop(self):
        while True:
            payload = await self.send_q.get()
            while self.next_seq - self.base >= self._effective_window():
                self._space.clear()
                await self._space.wait()
            seq = self.next_seq
            self.next_seq += 1
            frame = P.encode(P.FrameType.DATA, payload, seq=seq, flags=self._flags(),
                             window=self.rcv_buffer - len(self.rcv_buf))
            self.unacked[seq] = [frame, time.perf_counter(), 0]
            self._tx(frame)
            self._pending -= 1
            self.stats.data_sent += 1
            if self.mode == "sr":
                self._arm(seq)
            elif len(self.unacked) == 1:
                self._arm("gbn")

    def _arm(self, key, backoff=0):
        old = self._timers.pop(key, None)
        if old:
            old.cancel()
        delay = min(self.max_rto, self.rto * (2 ** min(backoff, 3)))   # per-frame back-off, capped at x8
        self._timers[key] = asyncio.get_running_loop().call_later(delay, self._on_timeout, key)

    def _on_timeout(self, key):
        self._timers.pop(key, None)
        if not self.unacked or self.dead:
            return
        if max(e[2] for e in self.unacked.values()) >= self.max_retries:
            self._give_up()
            return
        self.stats.timeouts += 1
        first = key if self.mode == "sr" else min(self.unacked)
        if self.congestion == "aimd" and first >= self._recover:
            # one multiplicative decrease per window of data (NewReno-style recovery point)
            self.ssthresh = max(self.cwnd / 2, 2.0)
            self.cwnd = 1.0
            self._recover = self.next_seq
            self.stats.cwnd_trace.append((time.perf_counter(), self.cwnd))
        if self.mode == "sr":
            if key in self.unacked:
                self._retransmit(key)
                self._arm(key, backoff=self.unacked[key][2])  # per-frame exponential back-off
        else:                                                  # GBN / SAW: resend everything outstanding
            self.rto = min(self.max_rto, self.rto * 2)        # exponential back-off of the single timer
            for seq in sorted(self.unacked):
                self._retransmit(seq)
            self._arm("gbn")

    def _give_up(self):
        """Peer unreachable (too many retransmissions): stop, like a TCP connection abort."""
        self.dead = True
        self.close()
        if self.on_dead:
            self.on_dead(self)

    def _clear_backoff(self):
        """New data was acknowledged: drop the exponential back-off (as Linux TCP does)."""
        if self.srtt is not None:
            self.rto = min(self.max_rto, max(self.min_rto, self.srtt + 4 * self.rttvar))

    def _retransmit(self, seq):
        entry = self.unacked[seq]
        entry[2] += 1                     # retransmission count (Karn: no RTT sample from these)
        self._tx(entry[0])
        self.stats.retransmissions += 1

    def _rtt_sample(self, sent_at):
        r = time.perf_counter() - sent_at
        self.stats.rtt_samples.append(r)
        if self.srtt is None:
            self.srtt, self.rttvar = r, r / 2
        else:
            self.rttvar = 0.75 * self.rttvar + 0.25 * abs(self.srtt - r)
            self.srtt = 0.875 * self.srtt + 0.125 * r
        self.rto = min(self.max_rto, max(self.min_rto, self.srtt + 4 * self.rttvar))

    def _grow_cwnd(self, n_acked):
        if self.congestion != "aimd":
            return
        for _ in range(n_acked):
            self.cwnd += 1.0 if self.cwnd < self.ssthresh else 1.0 / self.cwnd
        self.cwnd = min(self.cwnd, float(self.window))
        self.stats.cwnd_trace.append((time.perf_counter(), self.cwnd))

    def _on_ack(self, f):
        self.stats.acks_received += 1
        self.peer_window = f.window or self.peer_window
        newly = 0
        if self.mode == "sr":
            seq = f.ack
            if seq in self.unacked:
                frame, sent, rtx = self.unacked.pop(seq)
                if not rtx:
                    self._rtt_sample(sent)
                t = self._timers.pop(seq, None)
                if t:
                    t.cancel()
                self.acked.add(seq)
                newly = 1
            while self.base in self.acked:
                self.acked.discard(self.base)
                self.base += 1
        else:
            ack = f.ack                                         # cumulative: next expected seq
            if ack > self.base:
                for seq in range(self.base, ack):
                    entry = self.unacked.pop(seq, None)
                    if entry and not entry[2]:
                        self._rtt_sample(entry[1])
                newly = ack - self.base
                self.base = ack
                if self.unacked:
                    self._arm("gbn")
                else:
                    t = self._timers.pop("gbn", None)
                    if t:
                        t.cancel()
        if newly:
            self._clear_backoff()
            self._grow_cwnd(newly)
            self._space.set()
        if not self.unacked and self._pending == 0:
            self._all_acked.set()

    async def drain(self, timeout=None):
        """Wait until every queued message has been acknowledged."""
        await asyncio.wait_for(self._all_acked.wait(), timeout)

    # ---------------------------------------------------------------- receiver side
    def _send_ack(self, ack):
        self._tx(P.encode(P.FrameType.ACK, b"", ack=ack, flags=self._flags(),
                          window=max(1, self.rcv_buffer - len(self.rcv_buf))))
        self.stats.acks_sent += 1

    def _deliver(self, payload):
        self.stats.delivered += 1
        self.delivered.put_nowait(payload)

    def _on_data(self, f):
        if self.mode == "sr":
            if self.rcv_base <= f.seq < self.rcv_base + self.rcv_buffer:
                if f.seq in self.rcv_buf or f.seq < self.rcv_base:
                    self.stats.duplicates += 1
                else:
                    if f.seq != self.rcv_base:
                        self.stats.out_of_order_buffered += 1
                    self.rcv_buf[f.seq] = f
                self._send_ack(f.seq)
                while self.rcv_base in self.rcv_buf:
                    self._deliver(self.rcv_buf.pop(self.rcv_base))
                    self.rcv_base += 1
            elif f.seq < self.rcv_base:
                self.stats.duplicates += 1
                self._send_ack(f.seq)                          # our earlier ACK was lost
        else:
            if f.seq == self.rcv_base:
                self._deliver(f)
                self.rcv_base += 1
            elif f.seq < self.rcv_base:
                self.stats.duplicates += 1
            else:
                self.stats.discarded_out_of_order += 1
            self._send_ack(self.rcv_base)                      # cumulative ACK

    # ---------------------------------------------------------------- input
    def datagram_received(self, data):
        self.last_activity = time.monotonic()
        try:
            f = P.decode(data)
        except P.FrameError:
            self.stats.corrupted += 1
            return
        if f.type == P.FrameType.ACK:
            self._on_ack(f)
        elif f.type == P.FrameType.DATA:
            self._on_data(f)

    async def recv(self):
        """Next in-order application message as a Frame (use .json() / .payload)."""
        return await self.delivered.get()

    def close(self):
        self._pump.cancel()
        for t in self._timers.values():
            t.cancel()
        self._timers.clear()
