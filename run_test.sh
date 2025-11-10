#!/usr/bin/env bash
set -euo pipefail
LOGDIR=logs
mkdir -p "$LOGDIR"
pytest -q | tee "$LOGDIR/test_run.log"
