#!/usr/bin/env bash
# init.sh — run at the start of every session to confirm the project is healthy
# exit 0 = healthy, session can proceed
# exit 1 = broken, fix before implementing anything new

set -euo pipefail

echo "── loretools health check ──"

echo "checking dependencies..."
uv sync --all-extras --quiet || { echo "FAIL: uv sync failed"; exit 1; }

echo "running unit tests..."
uv run pytest tests/unit -q || { echo "FAIL: unit tests failed"; exit 1; }

echo "checking public API import..."
uv run python -c "import loretools; print('ok')" || { echo "FAIL: loretools import failed"; exit 1; }

echo "── all checks passed ──"
exit 0
