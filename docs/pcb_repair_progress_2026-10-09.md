# Execution ledger — plan: docs/superpowers/plans/2026-10-09-pcb-repair.md

Baseline commit: fe9b115. Topic branch: fix/ocp-latch-industrial-review. hardware/.history/ preserved.

Ruling: work in the current checkout on the explicitly approved repair branch, with snapshots — the approved plan specifies this branch and preserves user work; a second worktree would move the deliverable away from the shared project.

Baseline: five repository checks PASS; KiCad Python 10.0.3 available. Snapshots and hash manifest: artifacts/pcb_repair_before/.

Pre-flight: B supplies exact package/pad definitions to C; C supplies actual nets to D; D placement constrains E routing. All freeze gates depend on full parity and fresh reports, not declining legacy violation counts.

A: complete — fresh ERC 0/0/0; fresh baseline DRC 358 violations / 129 unconnected / 396 schematic parity issues. Count differs from prior 357 due legacy report variation.
B: terminal/shunt geometry and exact MPNs implemented; AX7010 physical revision and F1 implementation remain open.
C: complete — 158 electrical footprints plus 4 mechanical; physical-pin parity PASS; native DRC schematic parity 0. Assembly exclusions and schematic fields synchronized. Eleven checker behavior regressions pass, including rejection of extra numbered pads, missing values, DNP mismatch and absent actual power/bootstrap netclass assignments.
D: preliminary placement updated; package courtyard overlaps eliminated in native DRC; exact native netclass assignments installed; four 8mm mounting-head copper reservations added (mechanical assumption pending physical review).
Ruling: retain all 20 unqualified legacy tracks and the original zone pending endpoint-qualified replacement — deleting them would manufacture a DRC reduction and hide unfinished routing. Cost: the active board still has known shorts and must not be fabricated.
Ruling: use new persistent board UUIDs for replacement footprints — the old PCB source had no persistent UUIDs; schematic UUIDs and native paths are preserved.


## Fresh evidence after placement refinement

Saved/refilled board, KiCad 10.0.3: **271 violations / 466 unconnected / 0 schematic parity issues**. Violations are 220 errors and 51 warnings; unconnected items are separately reported errors.

| DRC type | Count |
|---|---:|
| tracks_crossing | 2 |
| shorting_items | 17 |
| clearance | 113 |
| solder_mask_bridge | 88 |
| track_dangling | 8 |
| isolated_copper | 43 |

No courtyard overlap, silkscreen collision, text-height or footprint-library mismatch was reported in this run. This does not prove electrical placement quality. Some proposed class clearances conflict with native fine-pitch pads; resolve through documented electrical/manufacturing rules rather than blanket relaxation. The existing board design settings are unchanged from fe9b115. The DRC report lists five inherited/default ignored check types (missing_courtyard, track_not_centered_on_via, tuning_profile_track_geometries, footprint_filters_mismatch, footprint_type_mismatch); no new exclusions or severity reductions were introduced. Review these before release.

The old 32-footprint partial board's 129 unconnected items cannot be compared directly with the complete 162-footprint board's 466. Missing circuitry is now visible; routing is still unfinished. All 20 legacy track geometries were compared against the snapshot and preserved. Nearest-pad endpoint audit is diagnostic only, not connectivity proof.

Fresh validation: all five repository checks PASS; netlist safety PASS; OCP digital behavior PASS (531 stable-level scenarios, no transient/bench claim); ERC 0 errors / 0 warnings / 0 exclusions; physical parity and constraints PASS; 11 behavioral regressions PASS; git diff --check clean. CI now runs the new physical parity and constraints against its freshly exported netlist. CI is not a routing/fabrication certificate.

Evidence in ignored local artifacts:
- artifacts/pcb_repair_before/manifest.json and source snapshots
- artifacts/ax7010_servo_reva.net and ax7010_servo_reva_erc.json
- artifacts/pcb_parity.json and pcb_drc_repair_stage.json
- artifacts/pcb_legacy_track_audit.json
- artifacts/pcb_repair_review.svg and .png (front copper/silkscreen visual review)

## Remaining dependent work

B is incomplete: actual AX7010 board revision and physical pin verification are required; F1 remains the schematic's unresolved external-fuse or onboard-25A choice. Both were requested from the user; no answer has been assumed. Manufacturer land-pattern verification for remaining critical ICs, MOSFETs and high-voltage capacitors remains open.

D remains preliminary: courtyard clearance is achieved, but proximity, loop areas, terminal access, mounting-head envelope and thermal arrangement need qualification with those actual packages/interfaces.

E remains unimplemented: replace legacy copper only with verified same-net endpoint routes; complete DC link/half bridges, gate/bootstrap, independent Kelvin pairs, safety/auxiliary and digital paths; refill and re-review both copper layers. Require DRC 0, unconnected 0, parity 0 and reviewed rules/exclusions before layout freeze. No complete-plan or freeze claim is made.

External protection/regen specifications, 2oz fabrication/current-temperature evidence, actual AX7010 VIO/partial-power behavior and OCP transient bench qualification stay open per docs/release_gates.md. Selected terminal/shunt ratings alone do not close them.


## Additional electrical correction from manufacturer review

TI INA241 datasheet SBOSA30D Table 5-1 explicitly requires reserved pin 4 to connect to ground. U2/U3/U4 had no-connect markers. Added a focused safety-netlist rule and first confirmed three failures on the old export, then grounded all three pins with short labeled wires. The local and embedded symbol pin types changed from no_connect to passive; the physical PCB pads now carry /GND. No control/interface pin or XDC assignment changed. Fresh netlist is **158 components / 180 nets**; three isolated NC nets disappeared. Three additional ground connections now require routing, giving the final **271 violations / 466 unconnected / 0 schematic parity**. ERC and all repository/safety/OCP/parity/constraint/regression checks pass after this correction. Exported current_adc sheet was rendered and visually reviewed.

Manufacturer basis: https://www.ti.com/lit/ds/symlink/ina241a.pdf (SBOSA30D, Table 5-1, page 2). The isolated NC nets disappearing is an electrical correction, not a routing improvement.

Independent read-only review: all three Important checker findings were reproduced and fixed; a second review confirmed the INA241 manufacturer requirement, minimal schematic diff, /GND on all three physical pad4 instances, 158/180 netlist count and fresh 271/466/0 DRC evidence. No remaining Critical/Important finding in the implemented stage. Full routing and release qualification remain unfinished. Changes are local on fix/ocp-latch-industrial-review; no push or merge.


## Superseding schematic-only change: AX7010 2022 / J10 and external F1

User confirms AX7010 2022 / J10 and requests schematic optimization with PCB layout deferred. Selected external KLKD025.T + LPSM0001Z; added external PSU wiring terminal J6; J3.1 is now VIN_FUSED. System BOM has 159 objects, current PCB netlist 157 components / 179 nets. Board file unchanged, physical parity deliberately pending (old F1 extra and J3.1 net mismatch). Prior parity 0 and DRC 271/466 above remain historical. Do not synchronize or route the PCB until that phase is requested. See `docs/schematic_optimization_2022_j10_2026-10-09.md` for current source verification and remaining qualifications.
