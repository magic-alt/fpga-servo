# Fabrication / release gates

**Current delivery scope (user revision, 2026-10-10): BOM and schematic only. PCB/layout repair is deferred. The working PCB retains earlier development edits and is not synchronized to the final bus-OCP schematic; the isolated unfinished routing candidate is not adopted. Do not use this board for fabrication or reuse historical zero-DRC/parity claims for the current schematic.**


Rev.A is not fabrication-approved until every blocking item below is closed.

## Current selection revision (2026-10-10)

This section supersedes the component choices and routing counts in the archived chronology below. See [selection record](lcsc_sourcing_review_2026-10-10.md) for current verification and procurement evidence. The design uses phase-inline INA240A1DR with three 5 mΩ SMD shunts, plus bus-only **positive nominal +25 A** OCP (2 mΩ shunt, INA240A1DR, LM393LV). Phase-window OCP is removed; no reverse-current trip is claimed. DRV8300DPWR replaces FD6288, and unused J2 is removed. F1 is **onboard** 0456025.ER; there is no external fuse holder.

Outstanding selection-specific gates:

- Bound the complete bus-shunt-to-VGS-off delay, PWM rejection, switching SOA and fault response. The DC source description does not establish fault current or regenerative absorption.
- Confirm prospective source fault current <=500 A and voltage envelope <=72 V for the selected 25 A fuse; qualify inrush, copper/ambient derating and I²t coordination. A 25 A fuse rating is not a 25 A continuous board qualification.
- Qualify all shunt solder joints and thermal paths: phase shunts dissipate 0.5 W at 10 Arms and 2 W for a held 20 A pulse; bus shunt dissipates 1.25 W at 25 A.
- Qualify INA240 common-mode excursions (recommended -4..80 V), driver switch-node slew (DP recommended <=2 V/ns) and 470 nF bootstrap effective capacitance.
- L1 lacks a substantiated continuous RMS rating; initial <=0.5 A total 12 V load is a test restriction, not a qualified rating. Full 1 A operation remains open.
- U26 and F2 local ambient must remain <=85°C; the overall 40°C ambient +50 K rise target does not extend their ratings. Verify encoder current below F2's temperature-derated hold limit.
- Confirm JILN finished plated holes 1.02 ±0.03 mm. BOOMELE header alternatives need <=1 A per-pin operation and manufacturer drawing confirmation. Conditional alternatives in procurement are not automatically approved drop-ins.
- Verify actual motor temperature sensing; onboard NTC2 alone does not measure remote motor winding temperature.

Gate A/B, layout freeze and fabrication release remain OPEN/BLOCKED until their evidence exists. Current DRC/ERC results must come from the current selected design; historical zero counts below cannot be reused.

## Archived review chronology

Latest follow-up: [2026-10-10 qualification and repair record](layout_followup_qualification_2026-10-10.md). J2 assembly annotations/current operating inputs and external-part audit repaired; CLEAR instructions no longer rely on the obsolete 28ms total recovery assumption. After explicit user approval, the repaired PCB candidate is now the working development baseline. Fresh ERC0/0; current DRC0 violations /0 unconnected /0 parity issues after the [completed routing repair](routing_closure_2026-10-10.md). The268/485 counts are the archived pre-adoption baseline. **S01 dynamic qualification and S09 sequencing remain OPEN; no layout freeze or fabrication approval.**

Latest ADC repair: [2026-10-10 record](adc_undervoltage_repair_2026-10-10.md). Fresh native evidence: 162 board components /169 nets,164 system objects,166 footprints; ERC0 errors/0 warnings/0 exclusions (4 existing ignored check categories unchanged). At the ADC-repair stage DRC was268 violations,485 unconnected,0 schematic parity issues (historical, superseded by adopted PCB baseline below). ADC static threshold gap repaired; rapid-droop shutdown and all other audit blockers remain open. Formal layout freeze is **not approved**.

Current confirmed target: **24-48V bus, 10Arms continuous phase current, 20kHz PWM, 20A peak for30s, 40degC maximum ambient, <=50K temperature rise, forced air, 5V ABZ encoder; brake circuit cancelled by latest user instruction; no assumed PSU absorption** (2026-10-10). Peak repetition interval, minimum airflow/fan-loss behavior, encoder maximum/startup current remain OPEN. S03 is not closed; assume no upstream energy absorption. See [thermal/encoder design basis](brake_thermal_design_basis_2026-10-10.md). Latest [electrical repair](layout_entry_repair_2026-10-09.md) supersedes historical counts; earlier [schematic explanation and simulation](schematic_layout_entry_review_2026-10-09.md) retains the audit context.

Latest adopted PCB development baseline: [2026-10-10 copper repair](pcb_legacy_route_repair_2026-10-10.md), **97 clearance errors /447 unconnected /0 parity** at adoption, superseded by the [historical68/447/0 land repair](drc_vendor_land_repair_2026-10-10.md), with no shorts or crossing tracks. All97 errors involve pads of the same package. The user explicitly approved adoption as a development baseline that has not passed release acceptance; the reviewed candidate was written to the working board, with byte equality verified. Original working board and project rules are archived. See [adoption and fresh checks](reviews/pcb_legacy_routes_2026-10-10/adopted_adoption.json). No release blockers are waived.

## Connector / FPGA

- [x] User confirms ALINX AX7010 2022 hardware, active connector J10 (2026-10-09). Manufacturer drawing sheets 5/15 cross-checked; physical continuity remains open below.
- [ ] Pin-by-pin continuity check against the actual AX7010 schematic.
- [ ] Vivado IOSTANDARD=LVCMOS33 review for every used PL pin.
- [ ] Verify no used pin conflicts with another on-board AX7010 function in the selected project.

## Schematic

- [x] KiCad 10-native hierarchy is the source of truth; current PCB netlist exports **162 board components /169 nets**; system XML has164 objects /170nets including external F1/J6.
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
- [ ] Qualify VA5 undervoltage dynamics: TPS389001 static trip is now above 4.75V across specified corners; fast droop, total gate-off delay, ripple and sequencing remain OPEN. The former G50 static gap is superseded by the 2026-10-10 repair.

- [x] OCP hardware ARM latch implemented; FAULT_CLEAR on J1.10 re-arms only with GATE_EN low and healthy conditions.
- [ ] Qualify latch fault pulses, clear/fault phase races, power ramps and actual gate-off timing on the bench; digital regression is insufficient.
- [ ] Ambient is confirmed40C with50K general rise. Prove U26 local free-air temperature<=85C (<=45K local rise at40C) for Rev.F maximum timing, or redesign and requalify the chain. General90C hotspot acceptance does not extend its timing table or establish junction temperature.
- [ ] Confirm AX7010 VIO minimum supports the G33 worst-case reset release (~3.194V).
- [ ] Validate power sequencing and partial-power behavior with AX7010 VIO, VA_5V and VDRV_12V independently present/absent. Pull-downs establish a configuration-time default but do not constitute a safety-rated shutdown system.
- [ ] Close input surge / regeneration energy handling: D1 is actually DNP, LM74502 OV is disabled. The user cancelled the brake circuit; it is removed from implementation scope. Qualify the remaining system surge/regeneration envelope without assuming source absorption; no brake sizing prerequisite is imposed on other repairs.
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
- [x] Close PCB DRC: current adopted root board has **0 violations /0 unconnected /0 schematic parity issues** with native all-severity refill/save checks; [final evidence](reviews/routing_completion_2026-10-10/final-drc.json). Earlier 64-item, 97/447 and 268/485 stages are historical. No added exclusions or severity reductions. Electrical/thermal/manufacturing qualification remains open.
- [x] Correct H1..H4 M3-labelled mounting-hole drills from 1.0 mm to 3.2 mm, preserving centers and the board outline; `check_design.py` rejects undersized M3-labelled holes.
- [x] KiCad native all-severity DRC clean, including zero unconnected and parity items; manufacturing readiness remains subject to the other gates.
- [ ] Board outline/mechanical keepout reviewed.
- [ ] 2 oz copper stack-up confirmed with fabricator.
- [ ] DC-link loop, three half-bridge loops and gate loops reviewed in layout.
- [ ] No sensitive analog trace routed under/adjacent to switch-node copper.
- [x] Kelvin sense routing reaches shunt pads independently: six native copper-cluster checks PASS; [evidence](reviews/routing_completion_2026-10-10/final-kelvin.json).
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

Historical implementation and incomplete-routing evidence: `docs/pcb_repair_progress_2026-10-09.md`. Package drawings and qualifications: `docs/pcb_package_qualification_2026-10-09.md`. The selected shunt/terminal part numbers do not close the unchecked footprint, thermal or mechanical gates above.

- [x] INA241 U2/U3/U4 pin4 grounded perTI SBOSA30D Table5-1; reserved NC name does not permit floating. Latest ERC and physical/native PCB parity pass after layout-entry repair.

## Schematic-only optimization: confirmed AX7010 2022 / J10

- [x] Select external F1 KLKD025.T (25A / 600VDC), required LPSM0001Z holder near source positive; remove the unqualified board-mounted 2920 fuse placeholder from the schematic. F1/J6 are off-board, not DNP and not PCB placement parts.
- [x] J3.1 is the fused source input; native safety regression requires it to connect to Q7.5 and U18.1/.5. J10 ground, VIO and active signal pins have focused regression coverage.
- [ ] Validate fuse/holder ambient derating, actual DC source fault current/time constant, cable ampacity, short-circuit clearing energy and startup-inrush coordination. Fuse selection alone does not establish MOSFET protection, surge protection or regenerative-energy handling.
- [x] Earlier deferred synchronization completed after user's explicit repair request: obsoleteF1 removed, J3.1 corrected; routing was unfinished at that synchronization stage; final zero-unconnected evidence is linked above.

Fresh schematic ERC is 0 errors / 0 warnings / 0 exclusions; no ignored checks or severities changed. Full details and source evidence: `docs/schematic_optimization_2022_j10_2026-10-09.md`.

## Gate A/B electrical qualification automation (2026-10-09)

New [Gate A/B verification report](gate_ab_verification_2026-10-09.md) and [automated evidence workflow](../.github/workflows/gate-ab-electrical.yml) check a **fresh KiCad XML netlist** against physical-pin contracts, passive corner calculations and reproducible ideal-source ngspice benches. All numeric results explicitly exclude vendor active-device, PWM, physical layout and thermal behavior. `--strict-gates` returns 2 while either gate is open. Current status **Gate A BLOCKED / Gate B BLOCKED**, independently of ERC passing or CI green.

- [ ] **A-ADC-UNDERVOLTAGE / S01:** static design repaired by TPS389001DSER and 5.1V regulation; **dynamic qualification OPEN**. The minimum static headroom is 58.519mV, not a gate-off timing guarantee. Qualify effective C31, rail ripple/transients, fastest droop and worst total delay to all six actual VGS turning off before ADC AVDD falls below 4.75V. S09 sequencing and C94 recovery remain OPEN; follow the [qualification procedure](layout_followup_qualification_2026-10-10.md).
- [ ] **A-PEAK-THERMAL-SPEC / A-VENDOR-FOOTPRINT-MPN:** freeze true 10Arms, peak/ambient/cooling, vendor ordering codes, pad drawings and initial electrical/thermal margin.
- [ ] **B-IC-TRANSIENT-MODELS:** validate available vendor model pin mapping and license, simulate actual FD6288/INA241/TLV9024/LM5164/MOSFET dynamics including switching overshoot, bootstrap and protection delays.
- [ ] **B-TOTAL-OCP-DELAY / B-SWITCHING-SOA:** bound worst-case full analog-to-VGS-off chain and correlate with low-energy measured fault response and safe MOSFET SOA.
- [ ] **B-REGENERATION-SINK:** qualify upstream absorption and OV protection for maximum mechanical energy; the current 200uF, 1A ideal model reaches illustrative 55V from 48V in 1.4ms without a sink.
- [ ] **B-BENCH-EVIDENCE:** power-domain partial-supply, ADC validity, six gate waveforms, dead time, OCP, thermal and ABZ signal-path evidence with serial/board revision and oscilloscope traces.

Do not change these checkboxes until traceable model and bench evidence exists. That earlier qualification PR did not close routing. The subsequent routing-completion evidence above supersedes its DRC/unconnected counts without closing these dynamic gates.
