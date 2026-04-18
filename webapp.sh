#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo "Starting demo webapp at http://${HOST}:${PORT}"
poetry run uvicorn apps.demo_webapp.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload
