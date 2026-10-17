---
name: fpga-servo-kicad-repair
description: Use when repairing the fpga-servo AX7010 KiCad hierarchy, OCP and power circuitry, ERC, schematic-to-PCB synchronization, or placement readiness in this repository.
---

# FPGA servo KiCad repair

Use the repository root containing `hardware/ads8588s_servo/ax7010_servo_reva.kicad_pro`. Read root `AGENTS.md` and `docs/release_gates.md`. Keep changes on a topic branch, carrying existing uncommitted changes intact. Inspect `git status -sb` and save local snapshots before editing electrical sources. Do not push or merge merely because this skill is loaded.

## Find the actual design

The source is native KiCad 10: `hardware/ads8588s_servo/ax7010_servo_reva.kicad_sch` with project-local `ax7010_servo_reva.kicad_sym` and `sym-lib-table`. The old `.sch`, `.lib` and legacy schematic checker commands are obsolete. Enumerate sheet children from the top source instead of assuming a fixed page count. Count exported components and nets; zero ERC on an empty or stale export is not evidence.

Resolve `kicad-cli` from PATH or provide its location as a local command argument. Use a KiCad Python environment with `pcbnew` for board checks. Keep workstation installation paths out of public files.

## Repair and verify the electrical graph

### Visible power and ground wiring

Apply the mandatory power/GND rules in root `AGENTS.md`. Put every supply,
ground and PWR_FLAG graphic at the circuit it serves, with a native visible
wire path to a real component pin. Child hierarchy ports must also reach real
pins by visible wires. An isolated port-to-power-symbol stub or label-only
legend is a failure even when ERC is zero and the named net is electrically
correct. Keep local decoupling, pulls and return paths readable; use labels
between distant functional blocks rather than long ground loops.

The project's `PWR_*` graphics are passive presentation symbols. Retain the
labels required to name their nets. When moving an endpoint, inspect every
intersected wire and pin; split new T branches and add explicit junctions.
Export baseline/final KiCad XML netlists and compare exact component identity,
net names and physical pin memberships with
`.agents/skills/schematic-humanizer/scripts/compare_connectivity.py`.
Run `python tools/pcb.py check --project ads8588s --scope schematic` and review every rendered page plus
power/ground crops. That check intentionally ignores label links; native ERC
and netlist equivalence remain separate acceptance gates.

Trace critical paths through exported physical pin numbers. Use manufacturer data sheets for package pin maps, power limits and timing. Compare library symbols, embedded definitions and footprint pad numbers; ERC alone cannot detect a plausible but wrong package mapping. Preserve all unaffected UUIDs, wires and sheet geometry during localized electrical repairs.

For hardware OCP, verify raw OCP diagnostic routing, asynchronous trip, supervised startup, default enable bias and deliberate re-arm. Fault recovery without a new clear edge must remain inhibited. Describe pulse-width and recovery/removal limits; boolean behavior checks are not analog transient or bench proof. Keep supply/regeneration energy and current/thermal assumptions visible when unknown.

After edits, use the shared configured entry. Exports go to independent evidence directories rather than overwriting authored BOMs:

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py export --project ads8588s --kind bom
python tools/pcb.py verify --project ads8588s --scope schematic
python tools/pcb.py verify --project ads8588s --scope release
```

Select `--project ad7606c` for its independent schematic; that configuration also checks the retained ADS8588S reference. Native verify includes fresh physical-pin safety/OCP and all-severity ERC. Strict release still blocks the archived, unsynchronized PCB and open engineering gates; a successful schematic scope does not waive them. Use `python tools/pcb.py test --kicad-cli kicad-cli` for full fresh-netlist regressions and `--pcb-python` for the native geometry lane.

Run any additional focused checks introduced by the change. Test a new safety constraint against the old faulty netlist before relying on its passing result. Review exported schematic pages visually after geometry or symbol edits. Update interface documentation/XDC together only if physical pin assignments change.

## Synchronization and release decisions

Before changing the PCB, compare schematic and board references, footprint IDs, pin counts and nets. Existing board footprints can be schematic placeholders; a successful sync dialog does not qualify them. Resolve missing footprints from vendor mechanical drawings and retain mechanical features. Save the board before synchronization, inspect the diff, and run fresh DRC after board changes. Keep unfinished routing and actual unconnected counts visible.

Report evidence in three parts: electrical changes; exact checks and fresh ERC/DRC counts; remaining release gates. Distinguish a schematic ready for provisional placement from frozen layout or fabrication release. Read `docs/release_gates.md` for outstanding OCP bench timing, surge/regeneration, connector and shunt ratings, AX7010 interface qualification and PCB closure. Never substitute ERC exclusions, deleted copper or invented footprint assignments for closure.
