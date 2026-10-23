# ScamShield: Robustness of Multilingual UPI SMS Scam Detection under Code-Mixing and Obfuscation

Computer Networks project. Shreyans Chowdry (24BDS0114), VIT Vellore.

Payment scams on UPI arrive as SMS/WhatsApp text written in Hinglish, Tanglish, Benglish and Tenglish, and scammers
deliberately misspell the trigger words (`K.Y.C`, `P1N`, `rеfund` with a Cyrillic `е`, invisible characters…).
This project builds a controlled framework to measure how well scam classifiers survive that:

1. **UPI-CMX dataset** — 11,986 synthetic, template-based SMS in 5 language settings × 3 classes (scam / genuine / promotion),
   with hard negatives (genuine KYC/OTP advisories, genuine reward and loan promos) and a template-disjoint test split.
2. **Graded obfuscation scheme L0–L4** — light misspelling → leetspeak/separators → homoglyphs/zero-width chars → cross-script rewriting.
3. **12 classifiers** — word-level (NB, RF, LR, SVM, BiGRU), character-level (char-n-gram LR/SVM, Char-CNN, CANINE)
   and subword multilingual transformers (DistilmBERT, XLM-R, MuRIL).
4. **Metrics** — macro-F1, scam false-negative rate, expected calibration error, latency, with bootstrap CIs and paired tests.
5. **Experiments** — robustness curves, cross-lingual transfer, adversarial training, a canonicalisation defence, latency.
6. **Web demo** — type or load a message, slide the obfuscation level, see every model's verdict and where it breaks.

## Quick start (macOS / Linux)

```bash
./setup.sh        # creates .venv and installs requirements (one time)
./run_demo.sh     # opens http://localhost:8000
```

The demo ships with the trained classical and neural models. To add the DistilmBERT transformer to the demo
(the 540 MB model is not included), run once — on an Apple-Silicon Mac it uses the GPU:

```bash
source .venv/bin/activate
python scripts/train_demo_models.py --transformer
```

## Reproducing the experiments

```bash
source .venv/bin/activate
bash scripts/run_all.sh                      # everything (transformers take hours on CPU, far less on a GPU)
SKIP_TRANSFORMERS=1 bash scripts/run_all.sh  # classical + neural only (~1 hour on a laptop)
PYTHONPATH=src python -m pytest -q tests     # unit tests
```

Every run is cached in `results/runs/`, so the pipeline is resumable. Outputs:

| Path | Contents |
|---|---|
| `data/upi_cmx.csv` | the dataset (`text, label, subtype, lang, template_id, script, split`) |
| `data/obf/` | cached obfuscated test sets (4 levels × 2 threat models × 3 seeds) |
| `results/RESULTS.md` | every table in one readable file |
| `results/tables/*.csv` | tables for the paper |
| `results/figures/*.png, *.pdf` | figures for the paper |
| `results/runs/` | raw per-run metrics (JSON) and predicted probabilities (NPZ) |
| `artifacts/` | trained models used by the demo |
| `paper/METHODS.md` | full method description to draw on when writing the paper |

## Project layout

```
src/scamshield/
  data/templates.py     parallel message templates (5 languages × 21 intents)
  data/lexicon.py       slot fillers, natural spelling variants, native-script lexicon
  data/generator.py     builds UPI-CMX with the template-disjoint split
  obfuscation.py        L0–L4 obfuscation operators + canonicalisation defence
  models/classical.py   TF-IDF word / char n-gram models
  models/neural.py      word BiGRU and character CNN (PyTorch, from scratch)
  models/transformer.py DistilmBERT, XLM-R, MuRIL, CANINE fine-tuning
  metrics.py            macro-F1, FNR, ECE, bootstrap CI, paired bootstrap, McNemar
  experiments.py        experiment stages (prepare / main / xling / latency)
  analysis.py           tables, figures and hypothesis tests
app/                    FastAPI server + single-page UI
scripts/                run_all.sh, train_demo_models.py
tests/                  unit tests
```

## API

| Endpoint | Body | Returns |
|---|---|---|
| `POST /api/predict` | `{text, models?, normalize?}` | per-model class probabilities and latency, ensemble verdict, detected language |
| `POST /api/obfuscate` | `{text, level, lang?, seed?}` | obfuscated text and the operations applied |
| `POST /api/stress` | `{text, lang?, seed?}` | scam probability of every model at L0…L4 |
| `GET /api/samples?lang=&label=&n=` | | random test messages |
| `GET /api/results` | | all experiment tables |

## Note on the data

UPI-CMX is synthetic. Templates were written from publicly reported scam patterns (KYC/PAN suspension, refund/collect-request
PIN fraud, lottery, wrong-transfer, task jobs, electricity disconnection, customs parcels, fake support, instant loans,
reward-points phishing) and genuine bank/UPI message formats. It allows controlled experiments but is not a substitute for
real SMS; the template-disjoint test split is used so scores reflect generalisation to unseen phrasings rather than memorised templates.
