#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then
  uv sync --frozen --extra test --extra evolution
else
  if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
  .venv/bin/python -m pip install -e '.[test,evolution]'
fi
printf '\nSetup complete. Activate with: source .venv/bin/activate\n'
