# Rev.A bring-up sequence

## Stage 0 - unpowered inspection

1. Verify polarity/orientation of all MOSFETs, FD6288, regulators, ADC and current-sense amplifiers.
2. Verify no short between VBUS and GND, 12 V and GND, 5 V and GND, 3.3 V and GND.
3. Verify all six gate-source resistances match the intended pulldowns.
4. Verify shunt Kelvin pads are not shorted into the load-current copper except at the shunt terminals.

## Stage 1 - low-voltage auxiliary power only

Use a current-limited 15-24 V bench supply, <=200 mA initially.

Expected rails:

- 12 V rail in regulation
- 5 V rail in regulation
- VIO_3V3 is absent until AX7010 is connected; it is supplied by AX7010, not a local LDO
- once AX7010 VIO is present, `RUN_OK=0` while GATE_EN is high impedance or low
- all six gate-driver inputs low

Do not fit motor or high-current DC-link wiring yet.

## Stage 2 - FPGA I/O without bridge switching

Connect AX7010 through the two 2x20 cables.

1. Confirm all six PWM pins idle low after configuration/reset.
2. Confirm `GATE_EN` remains low by default.
3. Read ADC BUSY and perform conversions with static analog voltages.
4. Drive an RS-422 ABZ source and validate A/B/Z counting in PL.
5. Verify loss of AX7010 power does not source damaging current through the servo-board interface.

## Stage 3 - gate-drive verification

Power the DC bus at 15-24 V, current limited.

1. Fit bridge MOSFETs but no motor.
2. Enable one leg at a time with low duty.
3. Measure GH/GL directly gate-to-source.
4. Verify dead time, no simultaneous gate overlap and expected bootstrap refresh.
5. Measure switch-node ringing and tune gate resistors/snubber footprints if required.

## Stage 4 - current-sense verification

Inject known bidirectional current through each phase shunt independently.

Acceptance:

- zero-current output ~2.5 V
- gain ~100 mV/A
- monotonic from at least -20 A to +20 A equivalent input
- ADC code-to-current scale within calculated calibration tolerance

## Stage 5 - low-energy motor spin

Use 15-24 V bus and a small PMSM/BLDC motor.

- open-loop six-step or voltage-vector test first
- then current-loop FOC at low current
- verify current polarity and Clarke/Park phase order
- verify hardware OCP removes gate commands

## Stage 6 - 48 V qualification

Only after Stage 0-5 pass:

- increase to 48 V with current-limited source / suitable battery protection
- verify switching overshoot remains below device design margin
- perform thermal soak at 5 A, 10 A, then 15 A phase RMS targets
- perform regeneration tests with a safe bus-energy sink

## Configuration / OCP acceptance additions

- With AX7010 VIO present and the PL unconfigured, measure all six raw PWM inputs and GATE_EN low (10k pull-downs), then confirm all six FD6288 inputs remain low.
- Repeat with independent rail power-up, rail loss and AX7010 disconnect; capture gate-to-source voltages rather than relying on logic readings alone.
- Verify C43/C44/C45 connect VA_5V to GND, and C80..C85 are mounted at their associated IC supply pins.
- Test both polarities of all three OCP channels around the nominal +/-22.06A equivalent thresholds. Record tolerance and fault-to-gate-off delay.
- Confirm ARMED (TP5) and all six commands remain low after a fault recovers without a new FAULT_CLEAR edge. Test clear held high, clear during fault and clear with GATE_EN high. Re-arm only with EN low and healthy conditions; follow `ocp_latch_review_2026-10-09.md`, including recovery/removal phase scans and minimum-pulse tests.
