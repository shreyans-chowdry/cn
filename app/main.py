"""
ScamShield demo server.

    uvicorn app.main:app --port 8000        (run from the project root)

Serves a single-page UI plus a JSON API:
  POST /api/predict    {text, models?, normalize?}       -> per-model class probabilities
  POST /api/obfuscate  {text, level, lang?, seed?}       -> obfuscated text + operations applied
  POST /api/stress     {text, lang?, seed?}              -> scam probability of every model at L0..L4
  GET  /api/samples?lang=&label=                         -> random test messages
  GET  /api/results                                      -> experiment tables (CSV -> JSON)
"""
import json
import random
import re
import sys
import time
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scamshield.metrics import LABELS  # noqa: E402
from scamshield.obfuscation import obfuscate, normalize, LEVELS  # noqa: E402
from scamshield.data.templates import LANG_NAMES  # noqa: E402

ART = ROOT / "artifacts"
RES = ROOT / "results"
PRETTY = {"word_lr": "Word LR", "char_lr": "Char LR", "char_svm": "Char SVM", "word_bigru": "Word BiGRU",
          "char_cnn": "Char CNN", "distil_mbert": "DistilmBERT"}
GRAN = {"word_lr": "word", "char_lr": "char", "char_svm": "char", "word_bigru": "word", "char_cnn": "char",
        "distil_mbert": "subword"}

app = FastAPI(title="ScamShield — multilingual UPI SMS scam detection")
MODELS = {}


def _load_models():
    from scamshield.models import classical, neural
    for path in sorted(ART.glob("*")):
        stem = path.name.split(".")[0]
        if "__" not in stem:
            continue
        name, regime = stem.split("__", 1)
        if name not in PRETTY:
            continue
        try:
            if path.suffix == ".joblib":
                m = classical.make(name).load(str(path))
            elif path.suffix == ".pt":
                m = neural.make(name).load(str(path))
            elif path.is_dir() and (path / "config.json").exists():
                from scamshield.models import transformer
                m = transformer.make(name)
                from transformers import AutoTokenizer
                m.tok = AutoTokenizer.from_pretrained(str(path))
                m.load(str(path))
            else:
                continue
            MODELS[f"{name}__{regime}"] = {"model": m, "name": name, "regime": regime,
                                           "label": f"{PRETTY[name]}{' (AT)' if regime == 'adv' else ''}",
                                           "granularity": GRAN[name]}
        except Exception as e:  # keep the server up even if one artifact is broken
            print(f"[warn] could not load {path.name}: {e}")
    print(f"[ScamShield] loaded {len(MODELS)} models: {', '.join(MODELS)}")


_load_models()

LANG_MARKERS = {
    "hi": {"aapka", "aapke", "aapko", "hai", "karein", "nahi", "liye", "karne", "bhej", "abhi", "turant", "jayega", "paise", "mein", "kar"},
    "ta": {"ungal", "pannunga", "irukku", "illa", "inniku", "neenga", "naan", "udane", "panam", "anuppunga", "aagiduchu", "ungalukku"},
    "bn": {"apnar", "korun", "hoyeche", "theke", "jonno", "ache", "taka", "ekhuni", "apni", "kore", "pathan", "shudhu"},
    "te": {"mee", "cheyandi", "undi", "ayyindi", "nunchi", "kosam", "meeku", "ippude", "dabbulu", "lo", "chesi", "matrame"},
}
SCRIPT_RANGES = {"hi": (0x0900, 0x097F), "bn": (0x0980, 0x09FF), "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F)}


def detect_lang(text):
    for lg, (lo, hi) in SCRIPT_RANGES.items():
        if any(lo <= ord(ch) <= hi for ch in text):
            return lg
    toks = set(re.findall(r"\w+", text.lower()))
    scores = {lg: len(toks & mk) for lg, mk in LANG_MARKERS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"


class PredictIn(BaseModel):
    text: str
    models: list[str] | None = None
    normalize: bool = False


class ObfIn(BaseModel):
    text: str
    level: int = 2
    lang: str | None = None
    seed: int | None = None


class StressIn(BaseModel):
    text: str
    lang: str | None = None
    seed: int = 7


def _predict(text, keys, norm=False):
    x = normalize(text) if norm else text
    out = []
    for k in keys:
        e = MODELS[k]
        t0 = time.perf_counter()
        p = e["model"].predict_proba([x])[0]
        ms = (time.perf_counter() - t0) * 1000
        out.append({"key": k, "label": e["label"], "granularity": e["granularity"], "regime": e["regime"],
                    "probs": {l: float(v) for l, v in zip(LABELS, p)}, "prediction": LABELS[int(p.argmax())],
                    "latency_ms": round(ms, 2)})
    return out


@app.get("/api/models")
def list_models():
    return [{"key": k, "label": e["label"], "granularity": e["granularity"], "regime": e["regime"]}
            for k, e in MODELS.items()]


@app.post("/api/predict")
def predict(inp: PredictIn):
    if not inp.text.strip():
        raise HTTPException(400, "empty text")
    keys = [k for k in (inp.models or MODELS) if k in MODELS]
    res = _predict(inp.text, keys, inp.normalize)
    scam_votes = sum(r["prediction"] == "scam" for r in res)
    avg = {l: sum(r["probs"][l] for r in res) / max(len(res), 1) for l in LABELS}
    lang = detect_lang(inp.text)
    return {"lang": lang, "lang_name": LANG_NAMES.get(lang, lang), "results": res,
            "ensemble": {"probs": avg, "prediction": max(avg, key=avg.get),
                         "scam_votes": scam_votes, "n_models": len(res)},
            "normalized_text": normalize(inp.text) if inp.normalize else None}


@app.post("/api/obfuscate")
def obf(inp: ObfIn):
    lang = inp.lang or detect_lang(inp.text)
    seed = inp.seed if inp.seed is not None else random.randint(0, 10 ** 6)
    text, ops = obfuscate(inp.text, inp.level, lang, seed=seed, return_ops=True)
    return {"text": text, "ops": ops, "level": inp.level, "level_name": LEVELS[inp.level]["name"],
            "lang": lang, "seed": seed}


@app.post("/api/stress")
def stress(inp: StressIn):
    lang = inp.lang or detect_lang(inp.text)
    levels = []
    for lv in range(5):
        t = obfuscate(inp.text, lv, lang, seed=inp.seed)
        preds = _predict(t, list(MODELS))
        levels.append({"level": lv, "name": LEVELS[lv]["name"], "text": t,
                       "scam_prob": {p["key"]: p["probs"]["scam"] for p in preds}})
    return {"lang": lang, "models": list_models(), "levels": levels}


@app.get("/api/samples")
def samples(lang: str | None = None, label: str | None = None, n: int = 6):
    df = pd.read_csv(ROOT / "data" / "upi_cmx.csv")
    df = df[df.split == "test"]
    if lang:
        df = df[df.lang == lang]
    if label:
        df = df[df.label == label]
    s = df.sample(min(n, len(df)))
    return s[["text", "label", "lang", "subtype"]].to_dict("records")


@app.get("/api/results")
def results():
    out = {"tables": {}, "figures": []}
    tdir = RES / "tables"
    if tdir.exists():
        for p in sorted(tdir.glob("*.csv")):
            out["tables"][p.stem] = pd.read_csv(p).fillna("").astype(str).to_dict("split")
    fdir = RES / "figures"
    if fdir.exists():
        out["figures"] = sorted(p.name for p in fdir.glob("*.png"))
    for f in ("dataset_stats.json", "perturbation_stats.json"):
        if (RES / f).exists():
            out[f.split(".")[0]] = json.load(open(RES / f))
    return out


app.mount("/figures", StaticFiles(directory=str(RES / "figures"), check_dir=False), name="figures")
app.mount("/static", StaticFiles(directory=str(ROOT / "app" / "static")), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "app" / "static" / "index.html")
