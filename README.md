# fpga-servo

FPGA-based servo drive development platform for the ALINX AX7010 / Zynq-7000 board.

## Rev.A hardware target

`hardware/ax7010_servo_reva` is the first KiCad hardware baseline for a single-axis PMSM/BLDC servo inverter:

- 24-48 V DC bus, 10 A continuous phase current, 20 kHz PWM (confirmed 2026-10-09)
- three-phase bridge using 100 V N-channel MOSFETs
- FD6288T three-phase half-bridge gate driver
- three inline 5 mOhm phase shunts
- INA241A2 current-sense amplifiers, 20 V/V, 5 V supply, mid-supply reference
- ADS8588S 8-channel simultaneous 16-bit SAR ADC
- differential ABZ encoder input using AM26LV32E
- AX7010 40-pin PL expansion connector interface
- 2-layer PCB baseline, 2 oz copper recommended

The official recent AX7010 documentation names the two 40-pin PL expansion connectors J10/J11. Some older board revisions/silkscreens may differ; therefore the design uses neutral names `AX7010_PL_A` / `AX7010_PL_B` and documents the electrical pin map explicitly.

## Repository layout

- `hardware/` KiCad 10-native schematic / PCB baseline, BOM and design notes
- `fpga/` AX7010 XDC pin constraints matching the hardware pin map
- `docs/` architecture, calculations, bring-up and release gates
- `tools/` lightweight repository checks that do not require KiCad to be installed

## Status

Rev.A is a **development baseline**, not a fabrication release. Critical architecture, power-stage topology, interface allocation, footprint intent and layout zoning are present. Before fabrication the release gates in `docs/release_gates.md` must be closed, especially KiCad ERC/DRC, exact footprint verification, switching-loop review, thermal verification and connector revision confirmation.

Latest [layout-entry repair](docs/layout_entry_repair_2026-10-09.md): bootstrap diode polarity and ADC serial-mode straps are corrected; ERC and schematic/PCB parity are clean. PCB still has 271 DRC violations and 478 unconnected items; placement/routing freeze remains blocked. The [earlier schematic explanation and audit](docs/schematic_layout_entry_review_2026-10-09.md) retains passive simulation and remaining electrical/bench gates.
