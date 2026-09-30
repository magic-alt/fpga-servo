# AX7010 Servo Drive Rev.A - KiCad baseline

## Files

- `ax7010_servo_reva.kicad_sch` - KiCad 10-native top-level schematic
- `power_input.kicad_sch`, `aux_power.kicad_sch`, `gate_inverter.kicad_sch`, `current_adc.kicad_sch`, `encoder.kicad_sch`, `ax7010_interface.kicad_sch` - native hierarchical child sheets
- `ax7010_servo_reva.kicad_sym` - versioned KiCad 10-native project symbol library
- `ax7010_servo_reva.kicad_pcb` - 2-layer PCB placement / critical-routing baseline
- `ax7010_servo_reva.kicad_pro` - KiCad project settings
- `bom.csv` - first-pass BOM and sourcing gates

Local KiCad state such as `sym-lib-table`, `*.kicad_prl` and lock files is intentionally ignored and is not part of the design source. The ignored `sym-lib-table` should map the nickname `ax7010_servo_reva` to the tracked `ax7010_servo_reva.kicad_sym`; CI creates that mapping in the runner user configuration.

## Layout partitioning

From left to right in the PCB file:

1. AX7010 PL headers and interface buffers
2. ADC + analog acquisition
3. gate driver / safety logic
4. six-MOSFET bridge + current shunts
5. motor and DC-bus terminal blocks

The auxiliary buck supply is kept along the top edge, away from the current-sense/ADC area.

## Schematic acceptance

The Rev.A1 schematic is now validated through the same path used for release review:

- source of truth is the checked-in KiCad 10-native `.kicad_sch` hierarchy; legacy `.sch` and `.lib` files are no longer tracked
- CI exports the netlist directly from `ax7010_servo_reva.kicad_sch` and requires **124 functional components / 163 nets**
- KiCad 10 ERC runs directly on the tracked native hierarchy with `--severity-all --exit-code-violations` and requires **0 errors / 0 warnings**
- repository checks reject Global Labels, objects outside the A4 drawing-safe region, duplicate hierarchy ports, floating labels and zero-length wires
- cross-sheet signals use hierarchical labels/sheet pins; Global Labels are intentionally **0**
- same-sheet local labels are retained only where they avoid long or crossing wires; they are required to terminate on real wire geometry

There is no CI conversion step anymore: the file opened by KiCad, reviewed in Git, exported to the netlist and checked by ERC is the same tracked native source.

Current footprint decisions made while closing ERC:

- J3: Phoenix Contact GMSTBA 2-position, 7.62 mm footprint
- J4: Phoenix Contact GMSTBA 3-position, 7.62 mm footprint
- L2: Würth Elektronik **74438356022**, WE-MAPI 4020, 2.2 uH

## Important limitation

The **schematic is ERC-clean**, but the PCB is still a **layout baseline, not a released manufacturing file**. It establishes the board outline, 2-layer structure, major package placements, power/switching zones, critical high-current routes, connector positions, keepout intent and major net names.

Before fabrication, complete fine digital routing, fanout, copper-pour refill, PCB DRC, creepage/clearance review, thermal/current-density review and final land-pattern verification. In particular, the exact production terminal-block/shunt MPNs and their continuous/peak-current qualification remain a fabrication gate; an ERC-valid footprint assignment does not by itself qualify connector current capability.
