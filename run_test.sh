#!/usr/bin/env bash
# Linux / macOS test runner: creates venv, installs deps, runs pytest and logs output
set -euo pipefail
mkdir -p logs
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest -q | tee logs/test_run.log
