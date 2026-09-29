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

## Important limitation

The PCB is intentionally committed as a **layout baseline, not a released manufacturing file**. It establishes the board outline, 2-layer structure, major package placements, power/switching zones, critical high-current routes, connector positions, keepout intent and major net names. Fine digital routing, complete fanout, copper-pour refill and final footprint land-pattern verification must be completed in KiCad before fabrication.

This status is deliberate: without running KiCad ERC/DRC and without the exact vendor selection for the 5 mOhm shunts / terminal blocks, claiming fabrication readiness would be unsafe.
