---
name: kicad-audit
description: Audit KiCad schematics and PCB parity, incomplete footprints, obsolete nets, BOM, ERC/DRC evidence and project blockers, especially fpga-servo. Read-only analysis; no KiCad design file changes.
---

# KiCad Hardware Audit

## Scope

Read-only design audit and gate evidence collection for FPGA servo boards. Use when asked to "检查工程/查错/为什么画不完/PCB 如何收敛" and before any schematic or layout modification.

## Workflow

1. `git rev-parse HEAD`, `git status --short`; record KiCad 10 CLI version and actual repository file hashes. Do not assume installation.
2. Review `hardware/README.md`, `docs/release_gates.md`, schematic hierarchy, PCB, BOM, FPGA pin constraints and all project-local libraries.
3. Export **KiCad native** XML netlist and BOM (if CLI available), run ERC and PCB DRC+schematic parity, preserve exit codes and reports.
4. Run `tools/ai_pcb_guide/scripts/board_parity_audit.py` against XML netlist; classify missing footprints, ref mismatch, board-only/obsolete footprints, stale net names, trace/via/zones. This helper is not a substitute for KiCad-native checks.
5. Review 4T shunts, U19 ESD and power-domain inconsistencies; verify MPNs only with datasheet evidence; separate confirmed facts from hypotheses.
6. Report P0/P1/P2 root causes, minimal PR breakdown, evidence gaps and *one* next task. Do not fix defects in audit mode.

## Outputs

`artifacts/pcb-qa/{erc.rpt,netlist.xml,parity_audit.json,pcb_drc.rpt}` when available; audit findings table with fields `component`, `source`, `issue`, `evidence`, `severity`, `next_action`; explicit `BLOCKED/PARTIAL/PASS`.

## Exit criteria

Completion means the audit accurately describes what is currently broken and what was actually checked. Audit PASS does not mean board/fabrication PASS. Do not guess DRC counts from document history.

## fpga-servo local integration

Read `docs/ai_pcb_local_setup_2026-10-09.md` and the existing project skill `.agents/skills/fpga-servo-kicad-repair/SKILL.md` before applying this workflow. Root AGENTS.md and user authorization take precedence. Use existing `tools/check_pcb_parity.py` for physical pin/net/value/DNP verification; the tutorial XML audit is supplemental. Use fresh exports rather than the tutorial historical 124-component/32-footprint baseline. Tool names must be discovered from the active MCP; do not assume a sync/router tool exists.
