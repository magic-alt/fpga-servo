# Layout entry electrical repair implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Repair the two verified schematic defects, reconcile the PCB and report remaining layout work honestly on `fix/layout-entry-electrical`.

**Architecture:** Keep actual diode A/K direction while correcting physical numbers to K1/A2 in local and embedded symbols. Wire ADC serial-only inputs visibly to ground. Preserve mechanical features and existing work; validate intended graph deltas rather than claiming graph equivalence for deliberate repairs.

**Tech Stack:** KiCad10.0.3, native schematic forms, pcbnew, Python physical-pin checks, ngspice46.

**Spec:** `docs/schematic_layout_entry_review_2026-10-09.md`; 24–48V, 10A continuous, 20kHz.

## Global constraints

- No credentials/environment contents; no blanket exclusions or severity reductions.
- Preserve existing project settings, board outline and H1..4 centers.
- Never remove necessary copper solely to lower DRC counts or mark required pins NC.
- Incomplete routing and bench/thermal gates remain explicit.

## Review focus

- Symbol semantics vs actual K-marked footprint pads.
- ADC serial-mode pins and unaffected DOUT/control connections.
- New ground bus must not intersect REGCAP/reference or other signals.
- PCB sync must include off-board fuse removal, J3 net and J1 custom field without fabricating parity.
- Existing shorted/obsolete copper needs endpoint-qualified repair; prelayout unconnected count cannot be waived.

## Tasks

- [x] Create branch, inspect dirty state, save 12 hardware snapshots.
- [x] Add physical diode/ADC regressions; demonstrate failure on old netlist.
- [x] Correct local/embedded diode pin numbers, visibly ground13 ADC pins, regenerate BOM and netlists, ERC and six source checks.
- [x] Synchronize limited reviewed changes using native pcbnew (desktop UI unavailable), inspect exact pad/reference changes and preserve mechanics.
- [x] Classify DRC root causes, retain necessary paths, record478 unconnected and required fabrication/thermal inputs. Native parity issues corrected to zero.
- [x] Re-run local simulation, export/render modified pages, update status/release gates and complete independent review.
- [ ] Complete placement, endpoint-qualified replacement of legacy copper, full routing and DRC closure after fabrication/thermal constraints are confirmed. This is unfinished PCB work, not waived by successful electrical repair.
