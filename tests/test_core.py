"""Run with:  PYTHONPATH=src python -m pytest -q tests"""
import asyncio
import ipaddress
import random
import zlib

import numpy as np

from scamshield.data.generator import generate
from scamshield.data.templates import TEMPLATES, LANGS
from scamshield.langid import identify
from scamshield.metrics import all_metrics, ece, scam_fnr
from scamshield.net import cidr, errorcodes as E, protocol as P
from scamshield.net.urlintel import analyse as link_analyse
from scamshield.obfuscation import edit_rate, normalize, obfuscate
from scamshield import scripts as S
from scamshield.hindi import to_latin as hi_latin
from scamshield.tamil import to_latin


# ---------------------------------------------------------------- data
def test_templates_are_parallel_across_languages():
    assert LANGS[0] == "en" and set(LANGS[1:]) == set(S.SCRIPTS)
    for label, subs in TEMPLATES.items():
        for st, by_lang in subs.items():
            for lang in LANGS[1:]:
                assert len(by_lang["en"]) == len(by_lang[lang]), (label, st, lang)
                for t in by_lang[lang]:
                    assert S.dominant(t) == lang, f"{lang} template without its script: {t}"


def test_generator_is_deterministic_and_template_disjoint():
    a, b = generate(300, seed=1), generate(300, seed=1)
    assert a.text.tolist() == b.text.tolist()
    assert not set(a[a.split != "test"].template_id) & set(a[a.split == "test"].template_id)


def test_language_is_detected_automatically():
    assert identify("Your SBI account will be blocked today")["name"] == "English"
    assert identify("உங்கள் SBI account இன்று block செய்யப்படும்")["name"] == "Tamil–English"
    assert identify("Ungal account inniku block aagidum, udane pannunga")["lang"] == "ta-rom"
    assert identify("आपका SBI account आज block कर दिया जाएगा")["name"] == "Hindi–English"
    assert identify("aapka account aaj band ho jayega, turant karo")["lang"] == "hi-rom"


# ---------------------------------------------------------------- obfuscation + defence
def test_obfuscation_levels_are_graded_and_keep_links():
    t = "உங்கள் SBI account இன்று block செய்யப்படும். உடனே KYC update செய்ய sbi-kyc.xyz/aB3d click செய்யவும்"
    assert obfuscate(t, 0, seed=1) == t
    rates = [np.mean([edit_rate(t, obfuscate(t, lv, seed=s)) for s in range(40)]) for lv in range(5)]
    assert rates == sorted(rates), rates
    for s in range(40):
        assert "sbi-kyc.xyz/aB3d" in obfuscate(t, 4, seed=s)


def test_normalize_undoes_disguises():
    assert normalize("K​YС рin") == "kyc pin"
    assert normalize("K.Y.C") == "kyc"
    assert normalize("௨ங்கள்") == "உங்கள்"                     # Tamil digit two used as the letter உ
    assert normalize("அக்கவுண்ட்-ஐ") == "account-ஐ"            # English loanword written in Tamil script
    assert normalize("अकाउंट") == "account"                     # ... and in Devanagari
    assert normalize("તुरंત") == "तुरंत"                         # Gujarati look-alike letters folded back


def test_transliteration():
    assert to_latin("உங்கள்") == "ungal"
    assert to_latin("பணம்") == "panam"
    assert hi_latin("तुरंत") == "turant"
    assert hi_latin("आपका") == "aapka"


def test_metrics():
    y = np.array([0, 1, 2, 2])
    m = all_metrics(np.eye(3)[[0, 1, 2, 0]], y)
    assert abs(m["fnr_scam"] - 0.5) < 1e-9
    assert scam_fnr(y, np.array([0, 1, 2, 2])) == 0
    assert 0 <= ece(np.full((4, 3), 1 / 3), y) <= 1


# ---------------------------------------------------------------- networking
def test_crc32_matches_ethernet_and_codes_detect_errors():
    data = "உங்கள் KYC".encode()
    assert E.crc32(data) == zlib.crc32(data)
    assert E.crc16_ccitt(b"123456789") == 0x29B1            # standard check value
    assert E.inet_checksum(b"\x45\x00\x00\x1c") == (~(0x4500 + 0x001c) & 0xFFFF)


def test_hamming_corrects_every_single_bit_error():
    for nib in range(16):
        code = E.hamming74_encode(nib)
        for bit in range(7):
            decoded, pos = E.hamming74_decode(code ^ (1 << bit))
            assert decoded == nib and pos == 7 - bit


def test_ssp_frame_roundtrip_crc_and_stream_reassembly():
    f = P.encode(P.FrameType.CLASSIFY_REQ, {"text": "உங்கள் KYC"}, seq=7)
    g = P.decode(f)
    assert g.seq == 7 and g.json()["text"] == "உங்கள் KYC"
    bad = bytearray(f)
    bad[20] ^= 0x10
    try:
        P.decode(bytes(bad))
        assert False, "corruption not detected"
    except P.CorruptFrame:
        pass
    two = f + P.encode(P.FrameType.PING, b"x", seq=8)
    dec = P.StreamDecoder()
    frames = dec.feed(two[:5]) + dec.feed(two[5:30]) + dec.feed(two[30:])   # TCP may split anywhere
    assert [x.seq for x in frames] == [7, 8]


def test_cidr_agrees_with_ipaddress_module():
    rng = random.Random(0)
    for _ in range(300):
        prefix = rng.randint(8, 30)
        ip = ".".join(str(rng.randint(0, 255)) for _ in range(4))
        ours = cidr.Network(f"{ip}/{prefix}")
        ref = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
        assert str(ours) == str(ref) and ours.num_addresses == ref.num_addresses
        assert cidr.int_to_ip(4, ours.broadcast) == str(ref.broadcast_address)
    assert cidr.classify_ip("10.1.2.3")["special"].startswith("private")
    assert cidr.classify_ip("fe80::1")["special"] == "link-local"
    assert cidr.classify_ip("8.8.8.8")["public"]
    assert str(cidr.Network("2001:db8:abcd::/48")) == "2001:db8:abcd::/48"


def test_dns_client_and_server():
    from scamshield.net.dns import DnsServer, Resolver, demo_zone

    async def run():
        srv = DnsServer(demo_zone())
        addr = await srv.start()
        r = Resolver(addr, timeout=0.5)
        loop = asyncio.get_running_loop()
        a = await loop.run_in_executor(None, r.resolve, "www.hdfcbank.com", "A")
        nx = await loop.run_in_executor(None, r.resolve, "nope.example", "A")
        big = await loop.run_in_executor(None, r.resolve, "bigrecord.test", "TXT")
        ptr = await loop.run_in_executor(None, r.reverse, "198.51.100.10")
        again = await loop.run_in_executor(None, r.resolve, "www.hdfcbank.com", "A")
        srv.close()
        return a, nx, big, ptr, again

    a, nx, big, ptr, again = asyncio.run(run())
    assert a["addresses"] == ["198.51.100.20"] and a["cname_chain"] == ["hdfcbank.com"]
    assert nx["rcode"] == "NXDOMAIN"
    assert big["truncated_over_udp"] and big["answers"]            # TC bit -> retried over TCP
    assert ptr["answers"][0]["data"] == "onlinesbi.sbi"
    assert again["cached"]


def test_arq_delivers_everything_in_order_over_a_lossy_link():
    from scamshield.net import service as S
    from scamshield.net.channel import LinkConfig, LossyUDPProxy
    from scamshield.net.client import ArqClient

    async def run(mode):
        t, proto, _ = await S.start_udp(S.Handler(stub=True), "127.0.0.1", 0, rto=0.05)
        px = LossyUDPProxy(t.get_extra_info("sockname")[:2], LinkConfig(loss=0.15, ber=1e-4, delay_ms=2, seed=3))
        addr = await px.start()
        res, _, st = await ArqClient(addr, mode=mode, window=8, rto=0.05).run([f"m{i}" for i in range(60)], timeout=60)
        px.close(); proto.close_all(); t.close()
        return res, st

    for mode in ("saw", "gbn", "sr"):
        res, st = asyncio.run(run(mode))
        assert [r["id"] for r in res] == list(range(60)), mode
        assert st.retransmissions > 0


def test_link_intelligence():
    bad = link_analyse("Update KYC at http://sbi-kyc-update.xyz/a1 now")
    good = link_analyse("Offer details at https://onlinesbi.sbi/x9")
    raw = link_analyse("login at 192.168.1.5/login")
    assert bad["risk"] > 0.6 and good["risk"] == 0 and raw["risk"] > 0.6
