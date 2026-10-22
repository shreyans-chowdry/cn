#!/usr/bin/env bash
# Start the ScamShield web demo at http://localhost:8000
set -e
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate
export PYTHONPATH=src
if ! ls artifacts/*.joblib >/dev/null 2>&1; then
  echo "No trained models found, training the demo models first (a few minutes)..."
  python scripts/train_demo_models.py
fi
( sleep 3 && (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null || true) ) &
python -m uvicorn app.main:app --port 8000
