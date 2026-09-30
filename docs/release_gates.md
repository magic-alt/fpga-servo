# Fabrication / release gates

Rev.A is not fabrication-approved until every blocking item below is closed.

## Connector / FPGA

- [ ] Confirm the physical AX7010 board revision in hand and whether its silk references are J10/J11 or another revision.
- [ ] Pin-by-pin continuity check against the actual AX7010 schematic.
- [ ] Vivado IOSTANDARD=LVCMOS33 review for every used PL pin.
- [ ] Verify no used pin conflicts with another on-board AX7010 function in the selected project.

## Schematic

- [x] KiCad 10-native hierarchy is now the checked-in source of truth; direct CLI export produces **124 components / 163 nets**.
- [x] Native schematic layout/A4-boundary checks pass for the top sheet and all six child sheets.
- [x] KiCad 10 ERC is clean: **0 errors / 0 warnings** on the tracked native hierarchy.
- [ ] Exact manufacturer ordering code on every IC/MOSFET/shunt.
- [ ] Verify FD6288 bootstrap network against current datasheet typical application.
- [ ] Verify regulator component values with vendor calculation/reference design.
- [ ] Verify comparator thresholds and latch behavior across tolerance/temperature.
- [ ] Define production-safe default for all control pins during FPGA reset/configuration.

## Footprints

- [ ] FD6288T TSSOP20 package drawing checked.
- [ ] INA241A2 SOIC-8 package drawing checked.
- [ ] ADS8588S LQFP64 land pattern checked.
- [ ] BSC040N10NS5 PG-TDSON-8 exposed drain pad checked.
- [ ] 5 mOhm shunt exact vendor footprint and power rating checked.
- [ ] Terminal block current rating and drill sizes checked.

## PCB

- [ ] Reconcile all schematic references, footprints and nets with the partial board. The current PCB baseline has 32 footprints; the schematic has 124 symbols.
- [ ] Close the current PCB DRC baseline (358 violations and 129 unconnected items in KiCad 10.0.3) after schematic-to-board parity is restored.
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
