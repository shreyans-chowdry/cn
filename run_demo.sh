#!/usr/bin/env bash
# Start ScamShield: web UI on http://localhost:8000, plus the network services the phone app uses
#   TCP 9099  ScamShield protocol (server mode of the Android app)
#   UDP 9098  ScamShield protocol over UDP (Go-Back-N / Selective Repeat batches)
#   5353      demo DNS server used for link checks
set -e
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate
export PYTHONPATH=src
if [ ! -f artifacts/production.joblib ]; then
  echo "Training the detector first (about a minute)..."
  python scripts/train_production.py
fi
( sleep 4 && (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null || true) ) &
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
