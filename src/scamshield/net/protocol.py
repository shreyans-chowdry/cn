"""
SSP -- the ScamShield Protocol. Application-layer framing shared by the TCP service, the
UDP service, the Android app and the experiments.

Frame layout (big-endian, 16-byte header + payload + 4-byte trailer):

     0       2     3     4     5     6               10              14      16
    +-------+-----+-----+-----+-----+---------------+---------------+-------+--------------+---------+
    | MAGIC | VER | TYP | FLG | WIN |      SEQ      |      ACK      |  LEN  |  PAYLOAD ... |  CRC-32 |
    | 'SS'  |  1  |     |     |     |   uint32      |    uint32     | uint16|  LEN bytes   | uint32  |
    +-------+-----+-----+-----+-----+---------------+---------------+-------+--------------+---------+

  MAGIC  0x5353 ("SS")        VER  protocol version (1)
  TYP    frame type (FrameType)
  FLG    bit0 = GBN receiver, bit1 = SR receiver, bit2 = last frame of a batch, bit3 = payload is UTF-8 JSON
  WIN    advertised receive window (flow control), in frames
  SEQ    sequence number of this frame       ACK  cumulative / selective acknowledgement number
  LEN    payload length                       CRC  CRC-32 (IEEE 802.3) over header + payload

On TCP the frames are sent back to back on the byte stream (LEN delimits them). On UDP one
datagram carries exactly one frame. A frame whose CRC does not match is discarded (counted
as corrupted); the ARQ layer then recovers it by retransmission.
"""
import enum
import json
import struct

from .errorcodes import crc32

MAGIC = 0x5353
VERSION = 1
HEADER = struct.Struct("!HBBBBIIH")          # 16 bytes
TRAILER = struct.Struct("!I")
HEADER_LEN, TRAILER_LEN = HEADER.size, TRAILER.size
MAX_PAYLOAD = 65535


class FrameType(enum.IntEnum):
    CLASSIFY_REQ = 1      # payload: {"text": ..., "id": ...}
    CLASSIFY_RESP = 2     # payload: verdict JSON
    ACK = 3               # ack-only frame (ARQ)
    NAK = 4
    PING = 5
    PONG = 6
    ERROR = 7
    DATA = 8              # generic ARQ data frame carrying an application message
    FIN = 9


class Flag(enum.IntFlag):
    NONE = 0
    GBN = 1
    SR = 2
    LAST = 4
    JSON = 8


class FrameError(ValueError):
    pass


class CorruptFrame(FrameError):
    pass


def encode(ftype, payload=b"", seq=0, ack=0, flags=Flag.NONE, window=0):
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        flags |= Flag.JSON
    elif isinstance(payload, str):
        payload = payload.encode("utf-8")
    if len(payload) > MAX_PAYLOAD:
        raise FrameError(f"payload too large ({len(payload)} bytes)")
    head = HEADER.pack(MAGIC, VERSION, int(ftype), int(flags), min(int(window), 255),
                       seq & 0xFFFFFFFF, ack & 0xFFFFFFFF, len(payload))
    return head + payload + TRAILER.pack(crc32(head + payload))


class Frame:
    __slots__ = ("type", "flags", "window", "seq", "ack", "payload")

    def __init__(self, ftype, flags, window, seq, ack, payload):
        self.type, self.flags, self.window, self.seq, self.ack, self.payload = ftype, flags, window, seq, ack, payload

    def json(self):
        return json.loads(self.payload.decode("utf-8")) if self.payload else {}

    def __repr__(self):
        return (f"Frame({FrameType(self.type).name}, seq={self.seq}, ack={self.ack}, win={self.window}, "
                f"flags={Flag(self.flags)!r}, len={len(self.payload)})")


def decode(buf: bytes) -> Frame:
    """Decode exactly one complete frame; raises CorruptFrame on a CRC mismatch."""
    if len(buf) < HEADER_LEN + TRAILER_LEN:
        raise FrameError("short frame")
    magic, ver, ftype, flags, win, seq, ack, n = HEADER.unpack_from(buf)
    if magic != MAGIC:
        raise CorruptFrame("bad magic")
    if ver != VERSION:
        raise FrameError(f"unsupported version {ver}")
    end = HEADER_LEN + n
    if len(buf) < end + TRAILER_LEN:
        raise CorruptFrame("length field exceeds datagram")
    (crc,) = TRAILER.unpack_from(buf, end)
    if crc32(buf[:end]) != crc:
        raise CorruptFrame("CRC mismatch")
    return Frame(ftype, flags, win, seq, ack, bytes(buf[HEADER_LEN:end]))


def frame_length(buf: bytes):
    """Total length of the frame at the start of a TCP stream buffer, or None if the header is incomplete."""
    if len(buf) < HEADER_LEN:
        return None
    return HEADER_LEN + HEADER.unpack_from(buf)[7] + TRAILER_LEN


class StreamDecoder:
    """Re-assembles frames from a TCP byte stream (frames can be split or coalesced by TCP)."""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, data: bytes):
        self.buf.extend(data)
        frames = []
        while True:
            n = frame_length(self.buf)
            if n is None or len(self.buf) < n:
                break
            chunk, self.buf = bytes(self.buf[:n]), self.buf[n:]
            frames.append(decode(chunk))
        return frames
