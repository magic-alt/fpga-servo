# AX7010 Servo Drive Rev.A - KiCad baseline

**Current delivery scope (user revision, 2026-10-10): BOM and schematic only. PCB/layout repair is deferred. The working PCB retains earlier development edits and is not synchronized to the final bus-OCP schematic; the isolated unfinished routing candidate is not adopted. Do not use this board for fabrication or reuse historical zero-DRC/parity claims for the current schematic.**


## Files

- `ax7010_servo_reva.kicad_sch` - KiCad 10-native top-level schematic
- `power_input.kicad_sch`, `aux_power.kicad_sch`, `gate_inverter.kicad_sch`, `current_adc.kicad_sch`, `encoder.kicad_sch`, `ax7010_interface.kicad_sch`, `ocp_latch.kicad_sch` - native hierarchical child sheets
- `ax7010_servo_reva.kicad_sym` - versioned KiCad 10-native project symbol library
- `ax7010_servo_reva.kicad_pcb` - 2-layer PCB placement / critical-routing baseline
- `ax7010_servo_reva.kicad_pro` - KiCad project settings
- `bom.csv` - first-pass BOM and sourcing gates

`fp-lib-table` resolves `fpga-servo.pretty` through `${KIPRJMOD}`. `sym-lib-table` is versioned and resolves the project library through `${KIPRJMOD}`. The project therefore opens and passes ERC without a machine-specific global symbol table. `*.kicad_prl` and lock files remain local state.

The 2026-10-09 review fixed stale hierarchy instance roots, added seven FPGA-input pull-downs and six local IC bypass capacitors, repaired C43/C44/C45 (previously both terminals on GND), and synchronized the BOM and actual DNP flags. See `docs/schematic_review_2026-10-09.md` for evidence and remaining layout gates.

## Layout partitioning

From left to right in the PCB file:

1. AX7010 PL headers and signal interface
2. ADC + analog acquisition
3. gate driver / safety logic
4. six-MOSFET bridge + current shunts
5. motor and DC-bus terminal blocks

The auxiliary buck supply is kept along the top edge, away from the current-sense/ADC area.

## Current selection implementation (2026-10-10)

The eight-page native hierarchy retains three phase-inline INA240A1DR channels and 5 mΩ / 3 W two-terminal SMD shunts. Unused J2 is removed. Bus-only positive OCP uses a fourth INA240A1DR, a 2 mΩ / 3 W shunt and one LM393LV comparator at nominal +25 A. U16 and phase-window divider parts are removed. The hardware ARM latch and supervised clear remain.

The gate driver is non-inverting DRV8300DPWR with internal bootstrap diodes, 470 nF bootstrap capacitors and initial 33 Ω gate resistors. F1 is onboard Littelfuse 0456025.ER; no external fuse holder is required. J3.1 is VIN_RAW and F1 feeds VIN_FUSED. J6 remains an off-board PSU reference.

Important land decisions:

- RSH1..RSH4: local HoYLR2512_Kelvin two-terminal land; independent inner-side sense routing is required on all eight inputs.
- J4: KEFA KF950-9.5-3P; J1/J5: JILN 3210 family, finished holes 1.02 ±0.03 mm.
- L1: SOREDE 68 µH prototype selection; full 1 A regulator operation and inductor thermal rating remain unqualified. L2: Sunlord SWPA4020S2R2MT.
- NTC1/2: Shiheng CMFA103F3950 on a shared reviewed 0603 land. The onboard NTC2 does not establish actual remote motor temperature.

The [selection record](../docs/lcsc_sourcing_review_2026-10-10.md) and current native verification evidence supersede previous component counts and selection snapshots. BOM and procurement candidates are generated from the current hierarchy and sourcing evidence; stock observations are not reservations.

## Acceptance and limits

Run all repository checks, native ERC, fresh physical-pin netlist checks, all-severity PCB DRC with schematic parity, and the eight-branch Kelvin audit. Review every exported schematic page. A zero count does not establish electrical or thermal qualification.

See [release gates](../docs/release_gates.md). Gate A/B remain blocked pending measured switching, OCP delay/SOA, supply sequencing, current/thermal, connector and regeneration qualification. No fabrication approval is implied. Older implementation reports remain historical evidence; their external fuse, INA241, FD6288 and phase-window OCP descriptions do not describe this revision.
