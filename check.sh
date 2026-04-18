#!/usr/bin/env bash
set -euo pipefail

echo "==> Ruff (lint)"
poetry run ruff check src/ apps/ tests/

echo "==> Pyright (typecheck)"
poetry run pyright src/ tests/

echo "==> Pytest"
poetry run pytest tests/ -q

echo ""
echo "All checks passed!"
