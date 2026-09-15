#!/usr/bin/env bash
# Capture an interactive Codex session in a flushed terminal transcript.
# Ultra is selected in Codex's supported UI; it is not an invented effort value.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v codex >/dev/null || { printf 'Codex CLI is unavailable. Open the Codex panel in VS Code and execute docs/codex_handoff.md.\n' >&2; exit 127; }
mkdir -p logs
run_stamp=$(date -u +%Y%m%dT%H%M%SZ)
transcript="logs/codex_${run_stamp}.log"
printf 'Opening Astra. Select the supported Ultra mode in Codex if available.\nTranscript: %s\nTask: read docs/codex_handoff.md and execute it through completion.\n' "$transcript"
exec script --quiet --flush --return --command 'codex -m gpt-6-astra "Read docs/codex_handoff.md and execute the authorized research continuation through completion. Keep meaningful live progress and actual experiment settings visible."' "$transcript"
