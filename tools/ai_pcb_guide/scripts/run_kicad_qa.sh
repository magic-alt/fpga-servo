#!/usr/bin/env bash
# Reference convenience wrapper; all logic lives in the shared toolkit.
set -euo pipefail
root="$(cd "${1:-.}" && pwd)"
cli="${2:-kicad-cli}"
python_exe="${3:-python3}"
exec "$python_exe" "$root/tools/pcb.py" verify --project ads8588s --scope release --kicad-cli "$cli"
