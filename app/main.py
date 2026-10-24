"""
ScamShield web app and network services, started together:

    ./run_demo.sh          (or: PYTHONPATH=src uvicorn app.main:app --host 0.0.0.0 --port 8000)

  http://localhost:8000   web UI
  TCP 9099                ScamShield protocol (SSP) -- the Android app's server mode connects here
  UDP 9098                SSP over UDP (plain request/response, Go-Back-N and Selective Repeat batches)
  UDP/TCP 5353            demo DNS server used for link checks

JSON API
  POST /api/analyze        {text, dns?}                  production detector: verdict, reasons, language, links
  POST /api/compare        {text}                        every research model's probabilities
  POST /api/obfuscate      {text, level, seed?}          obfuscated text + operators applied + canonicalised text
  POST /api/stress         {text, seed?}                 scam probability of each model at L0..L4
  GET  /api/samples        ?lang=en|ta&label=scam|legit|promo
  POST /api/net/frame      {text, flip_bit?}             SSP frame fields + hex; optional bit flip shows the CRC catch it
  POST /api/net/dns        {name, type}                  query the DNS server, with the raw wire bytes
  POST /api/net/cidr       {value}                       subnet calculator / IP classification
  GET  /api/net/status     service ports, counters, this machine's IP addresses
  GET  /api/results        experiment tables and figure names
"""
import asyncio
import json
import os
import random
import socket
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scamshield.detector import Detector  # noqa: E402
from scamshield.metrics import LABELS  # noqa: E402
from scamshield.net import cidr, dns as D, protocol as P, service as S  # noqa: E402
from scamshield.obfuscation import LEVELS, normalize, obfuscate  # noqa: E402

ART, RES = ROOT / "artifacts", ROOT / "results"
TCP_PORT = int(os.environ.get("SCAMSHIELD_TCP", 9099))
UDP_PORT = int(os.environ.get("SCAMSHIELD_UDP", 9098))
DNS_PORT = int(os.environ.get("SCAMSHIELD_DNS", 5353))
PRETTY = {"word_lr": "Word LR", "char_lr": "Char LR", "char_svm": "Char SVM", "word_bigru": "Word BiGRU",
          "char_cnn": "Char CNN", "distil_mbert": "DistilmBERT", "muril": "MuRIL"}
GRAN = {"word_lr": "word", "char_lr": "char", "char_svm": "char", "word_bigru": "word", "char_cnn": "char",
        "distil_mbert": "subword", "muril": "subword"}

app = FastAPI(title="ScamShield")
STATE = {"detector": None, "resolver": None, "dns": None, "stats": S.Stats(), "research": {}, "errors": []}


def _load_research_models():
    """Research models from the experiments (artifacts/<name>__<regime>.*), for the comparison views."""
    from scamshield.models import classical
    try:
        from scamshield.models import neural
    except Exception:
        neural = None
    for path in sorted(ART.glob("*__*")):
        stem = path.name.split(".")[0]
        name, regime = stem.split("__", 1)
        if name not in PRETTY or regime not in ("clean", "adv"):
            continue
        try:
            if path.suffix == ".joblib":
                m = classical.make(name).load(str(path))
            elif path.suffix == ".pt" and neural:
                m = neural.make(name).load(str(path))
            elif path.is_dir() and (path / "config.json").exists() and os.environ.get("SCAMSHIELD_TRANSFORMERS", "0") == "1":
                from scamshield.models import transformer
                from transformers import AutoTokenizer
                m = transformer.make(name)
                m.tok = AutoTokenizer.from_pretrained(str(path))
                m.load(str(path))
            else:
                continue
            STATE["research"][stem] = {"model": m, "label": PRETTY[name] + (" (AT)" if regime == "adv" else ""),
                                       "granularity": GRAN[name], "regime": regime}
        except Exception as e:
            STATE["errors"].append(f"{path.name}: {e}")


@app.on_event("startup")
async def startup():
    try:
        STATE["dns"] = D.DnsServer(D.demo_zone())
        await STATE["dns"].start("0.0.0.0", DNS_PORT)
        STATE["resolver"] = D.Resolver(("127.0.0.1", DNS_PORT), timeout=0.4, retries=1)
    except OSError as e:
        STATE["errors"].append(f"DNS server not started on {DNS_PORT}: {e}")
    if not (ART / "production.joblib").exists():
        raise RuntimeError("artifacts/production.joblib missing: run  python scripts/train_production.py")
    STATE["detector"] = Detector(resolver=STATE["resolver"])
    handler = S.Handler(STATE["detector"])
    try:
        STATE["tcp"], _ = await S.start_tcp(handler, "0.0.0.0", TCP_PORT, STATE["stats"])
        STATE["udp"], STATE["udp_proto"], _ = await S.start_udp(handler, "0.0.0.0", UDP_PORT, STATE["stats"])
    except OSError as e:
        STATE["errors"].append(f"SSP services not started: {e}")
    await asyncio.get_running_loop().run_in_executor(None, _load_research_models)
    print(f"[ScamShield] SSP TCP :{TCP_PORT}, UDP :{UDP_PORT}, DNS :{DNS_PORT}; "
          f"{len(STATE['research'])} research models loaded")


# ------------------------------------------------------------------ detector
class TextIn(BaseModel):
    text: str
    dns: bool = True


@app.post("/api/analyze")
def analyze(inp: TextIn):
    if not inp.text.strip():
        raise HTTPException(400, "Type or paste a message first.")
    return STATE["detector"].analyse(inp.text, use_dns=inp.dns)


def _research_probs(text):
    out = []
    for key, e in STATE["research"].items():
        p = e["model"].predict_proba([text])[0]
        out.append({"key": key, "label": e["label"], "granularity": e["granularity"], "regime": e["regime"],
                    "probs": {l: float(v) for l, v in zip(LABELS, p)}})
    return out


@app.post("/api/compare")
def compare(inp: TextIn):
    prod = STATE["detector"].analyse(inp.text, use_dns=False, explain=False)
    return {"production": prod["probs"], "models": _research_probs(inp.text)}


class ObfIn(BaseModel):
    text: str
    level: int = 2
    seed: int | None = None


@app.post("/api/obfuscate")
def obf(inp: ObfIn):
    seed = inp.seed if inp.seed is not None else random.randint(0, 10 ** 6)
    text, ops = obfuscate(inp.text, inp.level, seed=seed, return_ops=True)
    return {"text": text, "ops": ops, "level": inp.level, "level_name": LEVELS[inp.level]["name"], "seed": seed,
            "normalized": normalize(text)}


class StressIn(BaseModel):
    text: str
    seed: int = 7


@app.post("/api/stress")
def stress(inp: StressIn):
    det = STATE["detector"]
    levels = []
    for lv in range(5):
        t = obfuscate(inp.text, lv, seed=inp.seed)
        row = {"level": lv, "name": LEVELS[lv]["name"], "text": t,
               "scam_prob": {"production": det.analyse(t, use_dns=False, explain=False)["probs"]["scam"]}}
        for m in _research_probs(t):
            row["scam_prob"][m["key"]] = m["probs"]["scam"]
        levels.append(row)
    models = [{"key": "production", "label": "ScamShield (production)", "granularity": "production", "regime": "clean"}]
    models += [{"key": k, "label": e["label"], "granularity": e["granularity"], "regime": e["regime"]}
               for k, e in STATE["research"].items()]
    return {"models": models, "levels": levels}


@app.get("/api/samples")
def samples(lang: str | None = None, label: str | None = None, n: int = 1):
    df = pd.read_csv(ROOT / "data" / "upi_bisms.csv")
    df = df[df.split == "test"]
    if lang:
        df = df[df.lang == lang]
    if label:
        df = df[df.label == label]
    return df.sample(min(n, len(df)))[["text", "label", "lang", "subtype"]].to_dict("records")


# ------------------------------------------------------------------ networking views
class FrameIn(BaseModel):
    text: str
    flip_bit: int | None = None


@app.post("/api/net/frame")
def net_frame(inp: FrameIn):
    frame = P.encode(P.FrameType.CLASSIFY_REQ, {"id": 1, "text": inp.text}, seq=1)
    magic, ver, ftype, flags, win, seq, ack, n = P.HEADER.unpack_from(frame)
    crc = int.from_bytes(frame[-4:], "big")
    out = {"length": len(frame), "hex": frame.hex(" "),
           "fields": [{"name": "MAGIC", "bytes": "0-1", "value": f"0x{magic:04x} ('SS')"},
                      {"name": "VER", "bytes": "2", "value": str(ver)},
                      {"name": "TYPE", "bytes": "3", "value": f"{ftype} ({P.FrameType(ftype).name})"},
                      {"name": "FLAGS", "bytes": "4", "value": f"0x{flags:02x} (" + ("|".join(f.name for f in P.Flag if f and flags & f) or "none") + ")"},
                      {"name": "WIN", "bytes": "5", "value": str(win)},
                      {"name": "SEQ", "bytes": "6-9", "value": str(seq)},
                      {"name": "ACK", "bytes": "10-13", "value": str(ack)},
                      {"name": "LEN", "bytes": "14-15", "value": f"{n} bytes of UTF-8 JSON"},
                      {"name": "PAYLOAD", "bytes": f"16-{15 + n}", "value": frame[16:16 + n].decode('utf-8')},
                      {"name": "CRC-32", "bytes": f"{16 + n}-{19 + n}", "value": f"0x{crc:08x}"}]}
    if inp.flip_bit is not None:
        bit = inp.flip_bit % ((len(frame) - 4) * 8)
        bad = bytearray(frame)
        bad[bit // 8] ^= 1 << (7 - bit % 8)
        from scamshield.net.errorcodes import crc32, inet_checksum, parity_bit
        try:
            P.decode(bytes(bad))
            verdict = "accepted (undetected!)"
        except P.FrameError as e:
            verdict = f"rejected: {e}"
        out["flip"] = {"bit": bit, "byte": bit // 8, "receiver": verdict,
                       "crc32_received": f"0x{crc:08x}", "crc32_recomputed": f"0x{crc32(bytes(bad[:-4])):08x}",
                       "parity_detects": parity_bit(bytes(bad[:-4])) != parity_bit(frame[:-4]),
                       "checksum_detects": inet_checksum(bytes(bad[:-4])) != inet_checksum(frame[:-4])}
    return out


class DnsIn(BaseModel):
    name: str
    type: str = "A"


@app.post("/api/net/dns")
def net_dns(inp: DnsIn):
    r = STATE["resolver"]
    if r is None:
        raise HTTPException(503, "DNS server is not running")
    name = inp.name.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if inp.type == "PTR" or cidr.is_ip(name):
        q_name, q_type = D.reverse_name(name), "PTR"
    else:
        q_name, q_type = name, inp.type
    tid, query = D.build_query(q_name, q_type, tid=0x5353)
    try:
        res = r.resolve(q_name, q_type) if q_type != "PTR" else r.resolve(q_name, "PTR")
    except D.DnsError as e:
        raise HTTPException(504, str(e))
    for a in res.get("addresses", []):
        res.setdefault("classification", []).append(cidr.classify_ip(a))
    res["query_hex"] = query.hex(" ")
    res["server"] = f"127.0.0.1:{DNS_PORT} (demo zone)"
    return res


class CidrIn(BaseModel):
    value: str


@app.post("/api/net/cidr")
def net_cidr(inp: CidrIn):
    v = inp.value.strip()
    try:
        if "/" in v:
            net = cidr.Network(v)
            d = net.describe()
            if net.version == 4 and net.prefix <= 30:
                d["split_in_4"] = [str(s) for s in net.subnets(min(net.prefix + 2, 32))]
            return {"kind": "network", **d, "special": cidr.classify_ip(cidr.int_to_ip(net.version, net.network))}
        return {"kind": "address", **cidr.classify_ip(v)}
    except (ValueError, IndexError) as e:
        raise HTTPException(400, f"Not an IP address or CIDR block: {e}")


def _local_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))      # no packet is sent; just picks the outgoing interface
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith("127."))


@app.get("/api/net/status")
def net_status():
    st = STATE["stats"].as_dict()
    return {"tcp_port": TCP_PORT, "udp_port": UDP_PORT, "dns_port": DNS_PORT, "local_ips": _local_ips(),
            "counters": st, "dns": STATE["dns"].stats if STATE["dns"] else None,
            "resolver_cache": len(STATE["resolver"].cache) if STATE["resolver"] else 0, "errors": STATE["errors"],
            "model": STATE["detector"].meta.get("trained") if STATE["detector"] else None}


@app.get("/api/results")
def results():
    out = {"tables": {}, "figures": []}
    tdir = RES / "tables"
    if tdir.exists():
        for p in sorted(tdir.glob("*.csv")):
            out["tables"][p.stem] = pd.read_csv(p).round(3).fillna("").astype(str).to_dict("split")
    fdir = RES / "figures"
    if fdir.exists():
        out["figures"] = sorted(p.name for p in fdir.glob("*.png"))
    for f in ("dataset_stats.json", "production_eval.json"):
        if (RES / f).exists():
            out[f.split(".")[0]] = json.load(open(RES / f))
    return out


app.mount("/figures", StaticFiles(directory=str(RES / "figures"), check_dir=False), name="figures")
app.mount("/static", StaticFiles(directory=str(ROOT / "app" / "static")), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "app" / "static" / "index.html")
