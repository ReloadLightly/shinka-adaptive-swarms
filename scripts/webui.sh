#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
default_root="${project_root}/results/evolution"
if [[ ! -d "$default_root" ]]; then default_root="${project_root}/artifacts/evolution"; fi
results_root="${1:-$default_root}"
webui_port="${2:-8888}"
if [[ ! -d "$results_root" ]]; then
  printf 'Results directory does not exist: %s\n' "$results_root" >&2
  exit 2
fi
printf 'Native ShinkaEvolve WebUI: http://localhost:%s\n' "$webui_port"
python_bin="${project_root}/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then python_bin="python"; fi
exec "$python_bin" -u -m shinka.webui.visualization "$results_root" --port "$webui_port"
