# Fabrication / release gates

Rev.A is not fabrication-approved until every blocking item below is closed.

Current target confirmed 2026-10-09: **24-48V bus, 10A continuous phase current, 20kHz PWM**. RMS interpretation, ambient, peak current and regeneration envelope still need closure. Latest [electrical repair](layout_entry_repair_2026-10-09.md) supersedes historical counts; earlier [schematic explanation and simulation](schematic_layout_entry_review_2026-10-09.md) retains the audit context.

## Connector / FPGA

- [x] User confirms ALINX AX7010 2022 hardware, active connector J10 (2026-10-09). Manufacturer drawing sheets 5/15 cross-checked; physical continuity remains open below.
- [ ] Pin-by-pin continuity check against the actual AX7010 schematic.
- [ ] Vivado IOSTANDARD=LVCMOS33 review for every used PL pin.
- [ ] Verify no used pin conflicts with another on-board AX7010 function in the selected project.

## Schematic

- [x] KiCad 10-native hierarchy is the source of truth; current PCB netlist exports **157 board components / 166 nets**; system XML has159 objects /167nets including external F1/J6.
- [x] Native schematic layout/A4-boundary checks pass for the top sheet and all seven child sheets.
- [x] KiCad 10 ERC is clean: **0 errors / 0 warnings** on the tracked native hierarchy.
- [ ] Exact manufacturer ordering code on every IC/MOSFET/shunt.
- [ ] Verify FD6288 bootstrap network against current datasheet typical application.
- [ ] Verify regulator component values with vendor calculation/reference design.
- [ ] Verify comparator thresholds and latch behavior across tolerance/temperature.
- [ ] Define production-safe default for all control pins during FPGA reset/configuration.

## Layout entry decision (2026-10-09)

ERC is clean and mechanical/functional placement studies can proceed. Final component placement / routing freeze remains blocked by these schematic-level decisions:

- [x] D1..D4 symbol/footprint polarity corrected to K1/A2 in local/embedded library and PCB; native source and physical-pin regressions pass. D1 remainsDNP.
- [x] U6 serial-mode DB0..6, DB9..13, DB14/HBEN (physical pins16..22,27..32) visibly grounded with dedicated serial-mode symbol; physical-pin/type regression passes.
- [ ] Qualify VA5 undervoltage: G50 may not assert until below ADC's 4.75V operating minimum; gate enable does not prove valid ADC data.

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

- [x] Reconcile external fuse and electrical repairs: remove obsolete PCB F1, synchronize J3.1/diode/ADC pads and J1 metadata; current native parity0, physical-pad checkPASS,161footprints includingH1..4. See `docs/layout_entry_repair_2026-10-09.md`.
- [ ] Close PCB DRC: fresh refilled KiCad10.0.3 on repaired sources has **271 violations (220 errors / 51 warnings), 478 unconnected items, 0 schematic parity issues**. No new exclusions/severity reductions. Five inherited ignored types remain for review. See `docs/reviews/layout_entry_repair_2026-10-09/drc_final.json`.
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
- [ ] 10 A continuous thermal soak under confirmed RMS definition, ambient, cooling and enclosure; historical 15 A is superseded.

## Follow-up findings (2026-10-09)

- [x] U19 RVZ 14-pin mapping and Texas_R-PUSON-N14 footprint corrected; U19/latch stage158/183, later INA stage158/180, external-fuse stage157/179 are historical. Current ADC-serial repair stage is157/166.
- [x] Replace GMSTBA 12A selection with Phoenix Contact 1714971 / 1714984, nominal 32A; local 9.52mm footprints implemented from manufacturer drawings. Actual wire, temperature derating and mechanical fit remain open.
- [x] Replace BVB-I-R005 with Ohmite 650FPR005E, four-terminal 5mOhm / 5W at 25C free air; local footprint and force/sense mapping implemented. Assembly fit, low-temperature accuracy, transient and board thermal qualification remain open.
- [x] OCP latch design approved and implemented; see `docs/ocp_latch_review_2026-10-09.md` for timing conditions and remaining qualification.

Detailed evidence and board differences: `docs/schematic_followup_2026-10-09.md`.

Latest OCP implementation evidence: `docs/ocp_latch_review_2026-10-09.md`.

Latest physical-pin PCB audit and mechanical-hole repair: `docs/pcb_pre_sync_review_2026-10-09.md`.

Latest implementation evidence and unfinished routing: `docs/pcb_repair_progress_2026-10-09.md`. Package drawings and qualifications: `docs/pcb_package_qualification_2026-10-09.md`. The selected shunt/terminal part numbers do not close the unchecked footprint, thermal or mechanical gates above.

- [x] INA241 U2/U3/U4 pin4 grounded perTI SBOSA30D Table5-1; reserved NC name does not permit floating. Latest ERC and physical/native PCB parity pass after layout-entry repair.

## Schematic-only optimization: confirmed AX7010 2022 / J10

- [x] Select external F1 KLKD025.T (25A / 600VDC), required LPSM0001Z holder near source positive; remove the unqualified board-mounted 2920 fuse placeholder from the schematic. F1/J6 are off-board, not DNP and not PCB placement parts.
- [x] J3.1 is the fused source input; native safety regression requires it to connect to Q7.5 and U18.1/.5. J10 ground, VIO and active signal pins have focused regression coverage.
- [ ] Validate fuse/holder ambient derating, actual DC source fault current/time constant, cable ampacity, short-circuit clearing energy and startup-inrush coordination. Fuse selection alone does not establish MOSFET protection, surge protection or regenerative-energy handling.
- [x] Earlier deferred synchronization completed after user's explicit repair request: obsoleteF1 removed, J3.1 corrected; routing remains unfinished and is not waived by parityPASS.

Fresh schematic ERC is 0 errors / 0 warnings / 0 exclusions; no ignored checks or severities changed. Full details and source evidence: `docs/schematic_optimization_2022_j10_2026-10-09.md`.

## Gate A/B electrical qualification automation (2026-10-09)

New [Gate A/B verification report](gate_ab_verification_2026-10-09.md) and [automated evidence workflow](../.github/workflows/gate-ab-electrical.yml) check a **fresh KiCad XML netlist** against physical-pin contracts, passive corner calculations and reproducible ideal-source ngspice benches. All numeric results explicitly exclude vendor active-device, PWM, physical layout and thermal behavior. `--strict-gates` returns 2 while either gate is open. Current status **Gate A BLOCKED / Gate B BLOCKED**, independently of ERC passing or CI green.

- [ ] **A-ADC-UNDERVOLTAGE:** TPS3808G50 upper falling threshold about 4.743V is below the ADS8588S AVDD 4.75V operating minimum. Implement and qualify a threshold/independent inhibit that prevents PWM when ADC data is invalid; test all supply sequences and corner tolerances.
- [ ] **A-PEAK-THERMAL-SPEC / A-VENDOR-FOOTPRINT-MPN:** freeze true 10Arms, peak/ambient/cooling, vendor ordering codes, pad drawings and initial electrical/thermal margin.
- [ ] **B-IC-TRANSIENT-MODELS:** validate available vendor model pin mapping and license, simulate actual FD6288/INA241/TLV9024/LM5164/MOSFET dynamics including switching overshoot, bootstrap and protection delays.
- [ ] **B-TOTAL-OCP-DELAY / B-SWITCHING-SOA:** bound worst-case full analog-to-VGS-off chain and correlate with low-energy measured fault response and safe MOSFET SOA.
- [ ] **B-REGENERATION-SINK:** qualify upstream absorption and OV protection for maximum mechanical energy; the current 200uF, 1A ideal model reaches illustrative 55V from 48V in 1.4ms without a sink.
- [ ] **B-BENCH-EVIDENCE:** power-domain partial-supply, ADC validity, six gate waveforms, dead time, OCP, thermal and ABZ signal-path evidence with serial/board revision and oscilloscope traces.

Do not change these checkboxes until traceable model and bench evidence exists. This GitHub qualification PR does not change the electrical sources, PCB layout or the earlier outstanding DRC/unconnected counts.
