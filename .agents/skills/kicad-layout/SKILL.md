---
name: kicad-layout
description: Plan and execute KiCad PCB mechanical placement, schematic-to-board sync, critical servo inverter routing, ADC/Kelvin, FPGA/encoder signals, with staged DRC and human review gates.
---

# KiCad PCB Layout & Routing Gate

## Preconditions

Schematic/ERC + final footprint mapping review PASS, board mechanical constraints approved, FPGA connector revision/pinmap reviewed. If the board is missing many schematic footprints, prioritize native `Update PCB from Schematic`/F8 rather than routing.

## Sequence

1. Verify the active topic branch; preserve existing work and follow root AGENTS.md before creating or switching branches. Archive previous partial PCB baseline without promoting it to manufacturer source.
2. Use KiCad GUI Update PCB from Schematic (F8), or a synchronization tool actually exposed by the active MCP, and review added/replaced/deleted footprints; pay special attention to H1–H4 mechanical-only features. Do not manually edit S-expressions to fabricate netlist parity.
3. Verify references, footprint IDs, pin/pad/net mapping with KiCad DRC `--schematic-parity`; capture unmatched counts and missing pads.
4. Present a placement plan and review checkpoints. Place J3/J4/AX7010 headers, mount holes, DC-link/MOSFET, gate driver/bootstrap, shunt/INA, ADC and ESD/ABZ in physical order.
5. Route and review critical copper in this order: DC-link return → switching loops → gate/bootstraps → Kelvin sense → OCP safety → ADC/encoder → remaining logic. Never autoroute critical high-current, high-dv/dt or safety paths without approval.
6. Use board-appropriate width/clearance/stackup constraints based on fabricator + thermal calculations. Refill zones and run native DRC after every staged modification.
7. Deliver before/after KiCad render, native DRC reports, unconnected trend, modified paths and unresolved problems; avoid auto-changing schematic/electrical topology.

## Exit criteria

Native DRC 0 errors and 0 unconnected, all physical MPN/pad geometries approved, critical loop and thermal human review PASS; this still does not imply complete manufacturing qualification.

## fpga-servo local integration

Read `docs/ai_pcb_local_setup_2026-10-09.md` and the existing project skill `.agents/skills/fpga-servo-kicad-repair/SKILL.md` before applying this workflow. Root AGENTS.md and user authorization take precedence. Use existing `tools/check_pcb_parity.py` for physical pin/net/value/DNP verification; the tutorial XML audit is supplemental. Use fresh exports rather than the tutorial historical 124-component/32-footprint baseline. Tool names must be discovered from the active MCP; do not assume a sync/router tool exists.
