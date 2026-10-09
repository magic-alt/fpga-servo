---
name: kicad-schematic
description: Safely repair KiCad 10 schematic, pin mapping, footprint assignments, hierarchical labels and BOM for the AX7010 motor-driver board, with independent ERC and datasheet review.
---

# KiCad Schematic & Footprint Gate

## Preconditions

Confirm the user-authorized repair scope, actual source SHA, KiCad 10 installation and device MPN/package drawing. Continue independent audit and repair work while requesting genuinely missing design inputs.

## Steps

1. Inspect schematic hierarchy, symbol/library and exact datasheet pinouts. Use the configured KiCad MCP / GUI, not uncontrolled file-wide regex edits. Prefer native KiCad forward annotation and versioned project libraries.
2. Limit modification to approved references (e.g. RSH1-3 and U19). Compare 4T shunt force/sense pads, ADC range, gate-driver supplies, OCP latch polarity, connectors, and off-state safety against vendor documentation.
3. Verify symbol-to-pad number and footprint geometry; re-export KiCad 10 netlist, BOM and ERC using actual `kicad-cli` commands.
4. Check cross-sheet labels remain hierarchical (no new global label unless explicit spec change), no floating wires, no object beyond A4 boundary, and avoid false NC/power flags to suppress legitimate errors.
5. Save machine-produced ERC, netlist, BOM, focused changes and datasheet page references; review the proposed PCB diff and continue within the user-authorized scope.

## Exit criteria

Apply root `AGENTS.md`'s mandatory power/GND visible-wiring rules and the
[project repair skill](../fpga-servo-kicad-repair/SKILL.md#visible-power-and-ground-wiring).
Power, ground, PWR_FLAG and child hierarchy ports must connect by visible
native wiring to real component pins; label-only isolated stubs fail acceptance.
Require `python tools/check_power_wiring.py`, baseline/final XML netlist
equivalence, native ERC and visual review of all power/ground regions.

Real footprint mapping is assigned, approved and versioned; native ERC zero error/warning on checked SHA; expected functional component/net changes intentional; BOM matches schematic. Do not claim footprint is production-qualified without datasheet/dimensional signoff.

## fpga-servo local integration

Read `docs/ai_pcb_local_setup_2026-10-09.md` and the existing project skill `.agents/skills/fpga-servo-kicad-repair/SKILL.md` before applying this workflow. Root AGENTS.md and user authorization take precedence. Use existing `tools/check_pcb_parity.py` for physical pin/net/value/DNP verification; the tutorial XML audit is supplemental. Use fresh exports rather than the tutorial historical 124-component/32-footprint baseline. Tool names must be discovered from the active MCP; do not assume a sync/router tool exists.
