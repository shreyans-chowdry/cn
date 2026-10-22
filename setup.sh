#!/usr/bin/env bash
# One-time setup: creates a virtual environment and installs dependencies.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo
echo "Setup done. Start the demo with:  ./run_demo.sh"
