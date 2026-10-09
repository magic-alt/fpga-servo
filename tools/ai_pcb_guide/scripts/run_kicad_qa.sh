#!/usr/bin/env bash
# Read-only KiCad 10 diagnostic gate. Native DRC currently expected to fail.
set -uo pipefail
ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
CLI="${KICAD_CLI:-kicad-cli}"
PYTHON="${PYTHON:-python3}"
SCH="$ROOT/hardware/ax7010_servo_reva.kicad_sch"
BOARD="$ROOT/hardware/ax7010_servo_reva.kicad_pcb"
OUT="$ROOT/artifacts/pcb-qa"
mkdir -p "$OUT"
"$CLI" --version || exit 3
rc=0
"$CLI" sch erc --severity-all --exit-code-violations -o "$OUT/erc.rpt" "$SCH" || rc=2
if "$CLI" sch export netlist --format kicadxml -o "$OUT/netlist.xml" "$SCH"; then
    "$PYTHON" "$ROOT/tools/ai_pcb_guide/scripts/board_parity_audit.py" --netlist "$OUT/netlist.xml" --board "$BOARD" --output "$OUT/parity_audit.json" --strict || rc=2
else
    rc=2
fi
"$CLI" pcb drc --schematic-parity --refill-zones --severity-all --exit-code-violations -o "$OUT/pcb_drc.rpt" "$BOARD" || rc=2
echo "Evidence: $OUT; code=$rc"
exit "$rc"
