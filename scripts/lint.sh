#!/usr/bin/env bash
# Lint + validate the BAMI content-fabric repository.
# Usage (from the repository root): ./scripts/lint.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ruff =="
python -m ruff check shared tools scripts tests || true

echo "== schema check (sample deck) =="
python -c "from shared.pptx.schema import load_deck; load_deck('clients/_sample/deck.json'); print('deck.json OK')"

echo "== build sample =="
python -m tools.pptx_gen --schema clients/_sample/deck.json --out .pi/temp/lint_out.pptx

echo "== validate sample =="
python -m tools.pptx_validate .pi/temp/lint_out.pptx

echo "== pytest =="
python -m pytest -q
