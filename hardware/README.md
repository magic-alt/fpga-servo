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
- CI exports the netlist directly from `ax7010_servo_reva.kicad_sch` and requires **158 functional components / 180 nets**
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

The **schematic is ERC-clean**, but the PCB is still a **development layout, not a released manufacturing file**. The 2026-10-09 synchronization now contains 158 electrical footprints plus four mounting holes, complete physical-pad/net/DNP parity and preliminary placement. Latest saved/refilled DRC: **271 violations / 466 unconnected / 0 schematic parity issues**. The 20 legacy tracks and original copper zone remain for endpoint-qualified replacement; known shorts remain. Do not fabricate or energize this board. See `docs/pcb_repair_progress_2026-10-09.md`.

Before fabrication, complete fine digital routing, fanout, copper-pour refill, PCB DRC, creepage/clearance review, thermal/current-density review and final land-pattern verification. In particular, terminal-block/shunt fit, current and thermal qualification, actual AX7010 physical continuity and external F1 coordination remain fabrication gates (user confirms 2022/J10; F1 selected as KLKD025.T + LPSM0001Z); an ERC-valid footprint assignment does not by itself qualify connector current capability.

OCP latch implementation and timing gates: `docs/ocp_latch_review_2026-10-09.md`. Latest PDF has eight pages.

INA241 correction during package review: U2/U3/U4 reserved pin 4 connects to GND per TI SBOSA30D Table 5-1, despite its NC name. Symbol electrical type, schematic wiring and PCB pad nets match; net count changed from 183 to 180. `check_netlist_safety.py` rejects regression to the former floating pins.

2026-10-09 schematic-only update: F1 is external, J6 represents the external PSU connection, and J3.1 is VIN_FUSED. System BOM: 159 rows; PCB netlist: 157 components / 179 nets. PCB intentionally unchanged and requires later F1 removal/J3 net synchronization. See `docs/schematic_optimization_2022_j10_2026-10-09.md`.
