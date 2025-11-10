#!/usr/bin/env bash
set -euo pipefail
LOGS_DIR=logs
mkdir -p $LOGS_DIR
# If a venv exists, use it; otherwise rely on system python
if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi
pytest -q 2>&1 | tee $LOGS_DIR/test_run.log
