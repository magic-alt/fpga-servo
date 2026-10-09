# AX7010 Servo Drive Rev.A - KiCad baseline

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

## Schematic acceptance

The Rev.A1 schematic is now validated through the same path used for release review:

- source of truth is the checked-in KiCad 10-native `.kicad_sch` hierarchy; legacy `.sch` and `.lib` files are no longer tracked
- CI exports the netlist directly from `ax7010_servo_reva.kicad_sch`: **157 board components / 166 nets**; XML system export includes external F1/J6 and has **159 objects / 167 nets**
- KiCad 10 ERC runs directly on the tracked native hierarchy with `--severity-all --exit-code-violations` and requires **0 errors / 0 warnings**
- repository checks reject Global Labels, objects outside the A4 drawing-safe region, duplicate hierarchy ports, floating labels and zero-length wires
- exported-netlist safety checks verify PWM/default-off, gate resistors, current paths and decoupling
- cross-sheet signals use hierarchical labels/sheet pins; Global Labels are intentionally **0**
- same-sheet local labels are retained only where they avoid long or crossing wires; they are required to terminate on real wire geometry

There is no CI conversion step anymore: the file opened by KiCad, reviewed in Git, exported to the netlist and checked by ERC is the same tracked native source.

Current footprint decisions made while closing ERC:

- J3: Phoenix Contact **1714971**, MKDS 5/2-9,5, project-local 9.52 mm footprint
- J4: Phoenix Contact **1714984**, MKDS 5/3-9,5, project-local 9.52 mm footprint
- RSH1..RSH3: Ohmite **650FPR005E**, 5 mOhm / 5 W at 25 C free air, four terminals; project-local footprint
- L2: W鐪塺th Elektronik **74438356022**, WE-MAPI 4020, 2.2 uH

## Important limitation

The **schematic is ERC-clean**. D1..D4 now match K1/A2 footprint polarity; 13 U6 serial-mode pins are visibly grounded using ADS8588S_SERIAL. PCB contains 157 electrical footprints plus four mounting holes; physical parity and native schematic parity pass. Fresh refilled KiCad10.0.3 DRC: **271 violations (220 errors / 51 warnings), 478 unconnected items, 0 schematic parity issues**. Five inherited ignored DRC check types remain. There are 20 legacy tracks, zero vias and five zones. See [latest repair record](../docs/layout_entry_repair_2026-10-09.md); do not fabricate or energize this baseline.

Before fabrication, complete fine digital routing, fanout, copper-pour refill, PCB DRC, creepage/clearance review, thermal/current-density review and final land-pattern verification. In particular, terminal-block/shunt fit, current and thermal qualification, actual AX7010 physical continuity and external F1 coordination remain fabrication gates (user confirms 2022/J10; F1 selected as KLKD025.T + LPSM0001Z); an ERC-valid footprint assignment does not by itself qualify connector current capability.

OCP latch implementation and timing gates: `docs/ocp_latch_review_2026-10-09.md`. Latest PDF has eight pages.

INA241 correction during package review: U2/U3/U4 reserved pin 4 connects to GND per TI SBOSA30D Table 5-1, despite its NC name. Symbol electrical type, schematic wiring and PCB pad nets match; net count changed from 183 to 180. `check_netlist_safety.py` rejects regression to the former floating pins.

The earlier schematic-only update externalized F1/J6 and made J3.1 VIN_FUSED. The subsequent layout-entry repair has now removed PCB F1 and synchronized J3.1 plus ADC/diode pads. System BOM remains159 rows; current board netlist157/166. The prior schematic-only record remains historical.

## Gate A/B electronic qualification status (2026-10-09)

The repository now carries a [netlist-backed electrical verification tool](../tools/gate_ab_verify.py), a [native-KiCad + ngspice CI evidence workflow](../.github/workflows/gate-ab-electrical.yml) and a [documented release decision](../docs/gate_ab_verification_2026-10-09.md). Automated wiring checks and ideal passive simulation are not equivalent to vendor switching/protection models or hardware measurements. Both **Gate A and Gate B remain BLOCKED**; the PCB also remains unfinished.
