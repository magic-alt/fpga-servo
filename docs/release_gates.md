# Fabrication / release gates

Rev.A is not fabrication-approved until every blocking item below is closed.

## Connector / FPGA

- [ ] Confirm the physical AX7010 board revision in hand and whether its silk references are J10/J11 or another revision.
- [ ] Pin-by-pin continuity check against the actual AX7010 schematic.
- [ ] Vivado IOSTANDARD=LVCMOS33 review for every used PL pin.
- [ ] Verify no used pin conflicts with another on-board AX7010 function in the selected project.

## Schematic

- [x] KiCad 10-native hierarchy is now the checked-in source of truth; direct CLI export produces **158 components / 180 nets**.
- [x] Native schematic layout/A4-boundary checks pass for the top sheet and all seven child sheets.
- [x] KiCad 10 ERC is clean: **0 errors / 0 warnings** on the tracked native hierarchy.
- [ ] Exact manufacturer ordering code on every IC/MOSFET/shunt.
- [ ] Verify FD6288 bootstrap network against current datasheet typical application.
- [ ] Verify regulator component values with vendor calculation/reference design.
- [ ] Verify comparator thresholds and latch behavior across tolerance/temperature.
- [ ] Define production-safe default for all control pins during FPGA reset/configuration.

## Layout entry decision (2026-10-09)

ERC is clean and initial placement studies can proceed. Final component placement / routing freeze remains blocked by these schematic-level decisions:

- [x] OCP hardware ARM latch implemented; FAULT_CLEAR on J1.10 re-arms only with GATE_EN low and healthy conditions.
- [ ] Qualify latch fault pulses, clear/fault phase races, power ramps and actual gate-off timing on the bench; digital regression is insufficient.
- [ ] Confirm required ambient/junction range; U26 Rev.F timing bounds are specified only through 85C, so no 125C shutdown-delay claim.
- [ ] Confirm AX7010 VIO minimum supports the G33 worst-case reset release (~3.194V).
- [ ] Validate power sequencing and partial-power behavior with AX7010 VIO, VA_5V and VDRV_12V independently present/absent. Pull-downs establish a configuration-time default but do not constitute a safety-rated shutdown system.
- [ ] Close input surge / regeneration energy handling: D1 is actually DNP, LM74502 OV is disabled, and upstream protection / receptive source requirements remain mandatory.
- [ ] Freeze actual AX7010 connector revision and exact shunt / power connector / fuse footprints before routing power copper.
- [x] R80..R86 provide 10k pull-downs on all six PWM inputs and GATE_EN; R56..R61 remain on the gated FD6288 input nets.
- [x] U8..U11 and U15/U16 have dedicated 100nF bypass capacitors; C43..C45 correctly bridge VA_5V to GND.
- [x] Project-relative symbol library table and hierarchy instance UUID regression checks are in place.
- [x] BOM contains one row per schematic component; obsolete buffers/LDO entries have been eliminated and new U20..U25 latch circuitry is included and DNP flags are explicit.

## Footprints

- [ ] FD6288T TSSOP20 package drawing checked.
- [ ] INA241A2 SOIC-8 package drawing checked.
- [ ] ADS8588S LQFP64 land pattern checked.
- [ ] BSC040N10NS5 PG-TDSON-8 exposed drain pad checked.
- [ ] 5 mOhm shunt exact vendor footprint and power rating checked.
- [ ] Terminal block current rating and drill sizes checked.

## PCB

- [x] Reconcile schematic references, physical pad numbers, DNP states, footprint IDs and nets: 158 electrical + 4 mechanical footprints; fresh native DRC schematic parity 0. See `docs/pcb_repair_progress_2026-10-09.md`.
- [ ] Close the synchronized PCB DRC: latest saved/refilled KiCad 10.0.3 run has **271 violations (220 errors / 51 warnings), 466 unconnected items, 0 schematic parity issues**. Original partial-board 357/129 is historical; counts are not directly comparable after adding missing components. No new exclusions or severity reductions. Five inherited/default ignored DRC check types remain and must be reviewed before release.
- [x] Correct H1..H4 M3-labelled mounting-hole drills from 1.0 mm to 3.2 mm, preserving centers and the board outline; `check_design.py` rejects undersized M3-labelled holes.
- [ ] KiCad DRC clean.
- [ ] Board outline/mechanical keepout reviewed.
- [ ] 2 oz copper stack-up confirmed with fabricator.
- [ ] DC-link loop, three half-bridge loops and gate loops reviewed in layout.
- [ ] No sensitive analog trace routed under/adjacent to switch-node copper.
- [ ] Kelvin sense routing reaches shunt pads independently.
- [ ] ADC reference/decoupling and analog-ground returns reviewed.
- [ ] Encoder RS-422 connector has ESD and selectable termination near receiver.
- [ ] Thermal copper and via arrays reviewed for MOSFETs/regulators.

## Bench evidence before higher power

- [ ] Power-rail startup / shutdown captures.
- [ ] Six gate waveforms and dead-time captures.
- [ ] Switch-node overshoot at 24 V and 48 V.
- [ ] Current-sense gain/offset calibration on all three phases.
- [ ] OCP trip test with gates demonstrably forced low.
- [ ] ABZ receiver test to maximum planned encoder frequency.
- [ ] 15 A thermal soak evidence or revised continuous-current rating.

## Follow-up findings (2026-10-09)

- [x] U19 RVZ 14-pin mapping and Texas_R-PUSON-N14 footprint corrected; U19 repair stage was 158 components / 183 nets; latch stage before the INA241 reserved-pin correction was 158 / 183; current stage is 158 / 180.
- [x] Replace GMSTBA 12A selection with Phoenix Contact 1714971 / 1714984, nominal 32A; local 9.52mm footprints implemented from manufacturer drawings. Actual wire, temperature derating and mechanical fit remain open.
- [x] Replace BVB-I-R005 with Ohmite 650FPR005E, four-terminal 5mOhm / 5W at 25C free air; local footprint and force/sense mapping implemented. Assembly fit, low-temperature accuracy, transient and board thermal qualification remain open.
- [x] OCP latch design approved and implemented; see `docs/ocp_latch_review_2026-10-09.md` for timing conditions and remaining qualification.

Detailed evidence and board differences: `docs/schematic_followup_2026-10-09.md`.

Latest OCP implementation evidence: `docs/ocp_latch_review_2026-10-09.md`.

Latest physical-pin PCB audit and mechanical-hole repair: `docs/pcb_pre_sync_review_2026-10-09.md`.

Latest implementation evidence and unfinished routing: `docs/pcb_repair_progress_2026-10-09.md`. Package drawings and qualifications: `docs/pcb_package_qualification_2026-10-09.md`. The selected shunt/terminal part numbers do not close the unchecked footprint, thermal or mechanical gates above.

- [x] INA241 U2/U3/U4 pin 4 grounded according to TI SBOSA30D Table 5-1; the reserved NC name must not be interpreted as permission to float it. Fresh ERC remains zero and physical PCB parity passes.
