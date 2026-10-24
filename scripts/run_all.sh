#!/usr/bin/env bash
# Full experimental pipeline. Every run is cached in results/runs/, so the script is resumable.
# Fast models first (about an hour on a laptop), transformers last (hours on CPU, much less on a GPU / Apple Silicon).
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=src
FAST=word_nb,word_rf,word_lr,word_svm,char_lr,char_svm,word_bigru,char_cnn
XFAST=word_lr,char_lr,word_svm,char_svm,word_bigru,char_cnn

python -m scamshield.experiments prepare
python -m scamshield.experiments main     --models $FAST
python -m scamshield.experiments latency  --models $FAST
python -m scamshield.experiments xling    --models $XFAST
python -m scamshield.experiments cues     --models $FAST
python -m scamshield.experiments external            # public SMS corpora (Ayushmaan's datasets)
python -m scamshield.experiments network             # CRC, ARQ, TCP vs UDP, DNS experiments
python scripts/train_production.py                   # the detector served by the web app and phone app
python -m scamshield.experiments analyze

if [ "${SKIP_TRANSFORMERS:-0}" = "1" ]; then exit 0; fi
python -m scamshield.experiments main     --models distil_mbert,muril --regimes clean,adv
python -m scamshield.experiments main     --models xlmr,canine --regimes clean
python -m scamshield.experiments latency  --models distil_mbert,muril,xlmr,canine
python -m scamshield.experiments xling    --models distil_mbert,muril
python -m scamshield.experiments analyze
