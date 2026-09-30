# AX7010 Servo Drive Rev.A - KiCad baseline

## Files

- `ax7010_servo_reva.sch` - KiCad legacy-format schematic baseline; modern KiCad opens and converts it
- `ax7010_servo_reva.lib` - project-local legacy symbol library
- `ax7010_servo_reva.kicad_pcb` - 2-layer PCB placement / critical-routing baseline
- `ax7010_servo_reva.kicad_pro` - project settings placeholder for modern KiCad
- `sym-lib-table` - points KiCad to the local legacy symbol library
- `bom.csv` - first-pass BOM and sourcing gates

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

- source remains the checked-in KiCad legacy hierarchy so the existing project is preserved
- CI opens the hierarchy with KiCad 10 Eeschema and saves a native `.kicad_sch` conversion
- the converted hierarchy exports a populated netlist with **124 functional components / 163 nets**
- KiCad 10 ERC runs with `--severity-all --exit-code-violations` and currently reports **0 errors / 0 warnings**
- repository checks reject Global Labels, objects outside the A4 drawing-safe region, duplicate hierarchy ports, floating labels, zero-length wires, missing symbol-pin endpoints and invalid simple-hierarchy AR records
- cross-sheet signals use hierarchical labels/sheet pins; Global Labels are intentionally **0**
- same-sheet local labels are retained only where they avoid long or crossing wires; they are required to terminate on real wire geometry

The ERC gate also verifies that the legacy-to-native conversion remains usable. An empty legacy CLI netlist is not treated as evidence; the authoritative netlist/ERC is generated from the KiCad 10 native conversion.

Current footprint decisions made while closing ERC:

- J3: Phoenix Contact GMSTBA 2-position, 7.62 mm footprint
- J4: Phoenix Contact GMSTBA 3-position, 7.62 mm footprint
- L2: Würth Elektronik **74438356022**, WE-MAPI 4020, 2.2 uH

## Important limitation

The **schematic is ERC-clean**, but the PCB is still a **layout baseline, not a released manufacturing file**. It establishes the board outline, 2-layer structure, major package placements, power/switching zones, critical high-current routes, connector positions, keepout intent and major net names.

Before fabrication, complete fine digital routing, fanout, copper-pour refill, PCB DRC, creepage/clearance review, thermal/current-density review and final land-pattern verification. In particular, the exact production terminal-block/shunt MPNs and their continuous/peak-current qualification remain a fabrication gate; an ERC-valid footprint assignment does not by itself qualify connector current capability.
