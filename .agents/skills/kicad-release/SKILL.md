---
name: kicad-release
description: Verify KiCad PCB manufacturing readiness, native ERC/DRC schematic parity, electrical/thermal/connector review, Gerber/drill/BOM/CPL consistency and low-energy bring-up evidence. Never waive blockers silently.
---

# KiCad Fabrication Release

## Gate prerequisites

Requirements, MPN/footprints, mechanical, netlist parity, native KiCad DRC, current/thermal, EMC and power stage protection human review must be complete. A passed `kicad-cli sch erc` cannot stand in for the PCB checks.

## Workflow

1. Freeze target SHA, record KiCad version and board design rules/stackup/fabricator requirements.
2. Re-run KiCad CLI `sch erc` and `pcb drc --schematic-parity --refill-zones --severity-all --exit-code-violations`, preserving original text reports. Block on unexpected warnings, errors, unconnected nets.
3. Cross-check BOM/MPN/DNP, pick-and-place/centroids, reference designators and component orientation. Confirm all fabrication library files versioned.
4. Export Gerber X2 or fabricator-required format, Excellon drill, PnP, BOM, drawings and STEP in an isolated evidence directory. Verify Gerber in an independent viewer, outlines closed, copper layers correct, drills/NPTH/PTH/paste/silk consistent.
5. Compute SHA256 for every file, write manifest containing tool version, input commit, command, pass/fail and human review signature/date.
6. Prepare low-energy bring-up plan; do not imply that PCB DRC proves electrical safety or hardware performance.

## STOP CONDITIONS

Unknown AX7010 connector revision, unqualified current shunt or high-current terminal, incomplete OCP gate shutdown proof, unstable DC bus regen strategy, failing DRC/parity, unsigned power/thermal review, missing Gerber checks. Report BLOCKED with concrete remaining evidence. Never edit DRC exclusions to make a red check green.

## fpga-servo local integration

Read `docs/ai_pcb_local_setup_2026-10-09.md` and the existing project skill `.agents/skills/fpga-servo-kicad-repair/SKILL.md` before applying this workflow. Root AGENTS.md and user authorization take precedence. Use existing `tools/check_pcb_parity.py` for physical pin/net/value/DNP verification; the tutorial XML audit is supplemental. Use fresh exports rather than the tutorial historical 124-component/32-footprint baseline. Tool names must be discovered from the active MCP; do not assume a sync/router tool exists.
