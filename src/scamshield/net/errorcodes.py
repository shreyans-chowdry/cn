"""
Error detection and correction codes used by the ScamShield protocol (CN Module 3, Lab 2).

  parity_bit       single even-parity bit over the whole frame
  inet_checksum    16-bit one's-complement Internet checksum (RFC 1071, used by IP/UDP/TCP)
  crc16_ccitt      CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF)
  crc32            CRC-32 as in IEEE 802.3 Ethernet (reflected poly 0xEDB88320) -- the SSP frame check
  hamming74_*      Hamming(7,4) single-error-correcting code

All implemented from first principles (table-driven CRCs); `crc32` is verified against zlib in the tests.
"""


def parity_bit(data: bytes) -> int:
    p = 0
    for b in data:
        p ^= b
    p ^= p >> 4
    p ^= p >> 2
    p ^= p >> 1
    return p & 1


def inet_checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) | data[i + 1]
        s = (s & 0xFFFF) + (s >> 16)          # end-around carry
    return ~s & 0xFFFF


def _crc16_table():
    t = []
    for n in range(256):
        c = n << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if c & 0x8000 else (c << 1)
        t.append(c & 0xFFFF)
    return t


def _crc32_table():
    t = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t


_T16, _T32 = _crc16_table(), _crc32_table()


def crc16_ccitt(data: bytes) -> int:
    c = 0xFFFF
    for b in data:
        c = ((c << 8) & 0xFFFF) ^ _T16[((c >> 8) ^ b) & 0xFF]
    return c


def crc32(data: bytes) -> int:
    c = 0xFFFFFFFF
    for b in data:
        c = (c >> 8) ^ _T32[(c ^ b) & 0xFF]
    return c ^ 0xFFFFFFFF


# ---------------------------------------------------------------- Hamming(7,4)
def hamming74_encode(nibble: int) -> int:
    """4 data bits d1..d4 -> 7-bit codeword laid out p1 p2 d1 p3 d2 d3 d4 (bit 6 = position 1)."""
    d = [(nibble >> (3 - i)) & 1 for i in range(4)]
    p1 = d[0] ^ d[1] ^ d[3]
    p2 = d[0] ^ d[2] ^ d[3]
    p3 = d[1] ^ d[2] ^ d[3]
    bits = [p1, p2, d[0], p3, d[1], d[2], d[3]]
    return sum(b << (6 - i) for i, b in enumerate(bits))


def hamming74_decode(code: int):
    """Returns (nibble, corrected_position or 0). Corrects any single-bit error."""
    bits = [(code >> (6 - i)) & 1 for i in range(7)]
    s1 = bits[0] ^ bits[2] ^ bits[4] ^ bits[6]
    s2 = bits[1] ^ bits[2] ^ bits[5] ^ bits[6]
    s3 = bits[3] ^ bits[4] ^ bits[5] ^ bits[6]
    pos = s1 + 2 * s2 + 4 * s3
    if pos:
        bits[pos - 1] ^= 1
    return (bits[2] << 3) | (bits[4] << 2) | (bits[5] << 1) | bits[6], pos


def hamming_encode_bytes(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        out.append(hamming74_encode(b >> 4))
        out.append(hamming74_encode(b & 0xF))
    return bytes(out)


def hamming_decode_bytes(code: bytes):
    out, fixed = bytearray(), 0
    for i in range(0, len(code) - 1, 2):
        hi, p1 = hamming74_decode(code[i] & 0x7F)
        lo, p2 = hamming74_decode(code[i + 1] & 0x7F)
        fixed += bool(p1) + bool(p2)
        out.append((hi << 4) | lo)
    return bytes(out), fixed


CHECKS = {
    "parity": (parity_bit, 1),
    "inet_checksum": (inet_checksum, 16),
    "crc16": (crc16_ccitt, 16),
    "crc32": (crc32, 32),
}
