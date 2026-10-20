# Dual ADC engineering first-board bring-up

AD7606C revision 2026-10-20 has **no onboard bulk DC-link capacitor bank or its damping resistors**. Connect the qualified external capacitor and parallel bleeder to J7 (pin 1 positive, pin 2 GND) before any energization, and leave them connected until independent measurement confirms less than 5 V. Follow the [external-network requirements and reference discharge calculation](reviews/ad7606c_jlc_2026-10-20/external_dc_link.md). This passive bleeder does not replace regeneration containment. The ADS8588S board retains its existing onboard bank.

**Procedure only: every physical test below is NOT_RUN.** Record board serial/revision, frozen source/manufacturing hashes, actual fitted BOM, instruments, fixture limits, conditions and raw traces separately for each ADC board. Zero ERC/DRC does not complete a physical stage. See [first-board boundaries](reviews/dual_prototype_2026-10-18/first_board_boundary.md) and [full release gates](release_gates.md).

Both boards target **24–48 V, 20 kHz PWM, 10 Arms continuous phase current, 20 A instantaneous phase amplitude for 30 s (14.142 Arms for a balanced sine), 40°C ambient with forced air**. The **12 V total continuous load is 1 A**, including the input power consumed by the downstream 5.1 V converter. Fix minimum airflow, fan-failure response and peak repetition/cooldown before rated operation. Respect each local component temperature limit; the overall 50 K temperature-rise target does not override it.

There is **no firmware or HDL implementation in this repository**. FPGA behavior below is a requirement for separately reviewed commissioning logic, not existing functionality. Keep `GATE_EN=0` until that logic and the relevant stages are verified.

There is **no onboard brake**. D1 is DNP and LM74502 OV is grounded. J7 connects the external fixture directly to protected VBUS/GND after reverse-polarity protection, upstream of RSH4. A fixture connected only at J3 may be isolated when the input controller loses power; it does not establish protected-bus containment. The planned protected-bus ceiling is **60 V including overshoot measured at the board**, subject to fixture qualification. A fuse's 72 V interruption rating is not an assembled-board voltage allowance. J7 bypasses F1: any source-capable sink fixture requires its own coordinated branch fuse, current/energy limit and disconnect. Do not count input F1 as J7 branch protection. Before any motor operation, independently verify an **external regeneration energy sink/clamp**, including energy, power, current, voltage, wiring and failure behavior. An ordinary bench supply must not be assumed to absorb energy; current limiting alone is insufficient. Do not use a motor to discover the fixture's containment capacity.

## Stage 0 — unpowered inspection

1. Compare assembly with the exact board BOM and native pad/net evidence: ADC variant, DRV8300DPWR non-inverting driver, INA240A1DR, MOSFETs, fuse, shunts, inductor and polarized capacitors. Do not substitute DI/N driver variants or unreviewed alternates.
2. Confirm U7 AM26LV32EIPWR uses its corrected OEM physical map, including enable pins 4/12, and that manufactured copper matches. Confirm J1/J5 orientation, finished-hole acceptance and seating. J1 is the active interface; J2 is absent from the current design.
3. Inspect solder/exposed pads, common-drain MOSFET lands, fuse feeds, shunt inner-edge Kelvin pickups, local decoupling and sensitive returns. Confirm six intended 10 kΩ bridge gate-source bleeders.
4. Check continuity/resistance of VBUS/GND, 12 V/GND, VA5/GND and VIO/GND, accounting for capacitor charging. Verify MOSFET source/gate/drain continuity. Establish DC-link discharge and residual-voltage checks before handling.
5. Disconnect motor, inhibit controls and review mechanical clearance, airflow and secured fused/current-limited test wiring before energizing.

## Stage 1 — auxiliary supplies without switching

Use the reviewed [two-stage fixture procedure and limits](reviews/dual_prototype_2026-10-18/power_static_budget.md). Keep `GATE_EN=0`, all PWM low, motor/encoder/external 12 V loads disconnected, and connect the source at 0 V. First qualify source current limiting and stored-energy discharge on a dummy load: panel settings alone do not bound terminal overshoot.

Stage 1 is limited to **10 V / 0.1 A at DUT terminals**. Do not advance until independently measuring TP1 >=9.5 V and **each** input MOSFET VGS >=10 V and |VDS| <=0.10 V. Failure to start under this limit means STOP and review; do not increase the limit to force startup. This is a bounded charging step, not a 10 V operating specification. Observe the reviewed temperature/fixture stop criteria.

Only after accepting those measurements, stage 2 may ramp toward 24/48 V at <=1 V/ms with <=2 A compliance and continuous VGS/VDS, bus-tracking and temperature monitoring. Lost enhancement, current limiting, loss of tracking or abnormal heating requires shutdown/reset to 0 V and investigation. Sustained 48 V / 2 A is outside the stage-1 SOA argument; characterize fault shutdown and source stored energy first. Both stages and fixture qualification remain **NOT_RUN**. VIO_3V3 comes from the verified AX7010 domain, not a local LDO.

Measure 12 V and nominal VA5=5.1 V at the loads, startup, ripple and local temperatures against the adopted corner calculations and recommended operating ranges. Include `5.1 V * I5V / (12 V * efficiency)` and all direct 12 V loads within 1 A total. The LM5164 1 A headline does not establish full-load startup.

After stable low-load operation, test load steps and continuous total 1 A at both 24 V and 48 V, 40°C and actual quantified airflow. Record loaded voltage, frequency, regulator/inductor temperatures, startup limiting and recovery. Use a reviewed resistor/electronic-load fixture; bridge switching is not the test load.

## Stage 2 — independent rails and inhibition

Verify actual AX7010 2022/J10 pinout, VIO and PL conflicts before J1 connection. Use a reviewed breakout to exercise VIO first/last, bus/12 V first/last, VA5 rise/loss, FPGA unconfigured/configured/reset, cable disconnect and restoration. Stay within unpowered-pin limits; do not back-drive converter outputs without a reviewed isolation/injection method.

Capture all six **actual gate-to-source voltages**, together with rails, PWR_GOOD, PWR_READY, ARMED, GATE_EN and clear. Require default inhibition, no unintended turn-on and no automatic re-arm after recovery. Driver UVLO may leave gates high impedance; measure actual discharge. Test the fastest credible VA5 droop and prove all actual VGS off before ADC supply falls below 4.75 V. Static threshold margin is not shutdown timing evidence.

## Stage 3 — ADC-specific startup and static acquisition

Keep bridge disabled. Apply controlled analog voltages within selected ranges and permitted pin currents. Verify supply/reset timing, reference settling, channel order, signed coding, offsets/gains and fresh-frame detection. Check grounded unused channels.

| Contract | ADS8588S board | AD7606C-16 board |
| --- | --- | --- |
| Digital supply | DVDD/VIO from AX7010 3.3 V; prove independent AVDD/DVDD partial-power behavior | ADC VDRIVE/AVCC use VA5; TXU0204 translates to VIO; prove translator supply/OE sequences |
| Reference | REFIN/REFOUT 2.5 V with 10 µF; joined REFCAPA/B 4 V with 10 µF; separate 1 µF REGCAP capacitors | REFIN/REFOUT 2.5 V with 100 nF; joined REFCAPA/B nominal 4.4 V with 10 µF; separate 1 µF REGCAP capacitors |
| Interface | Existing serial straps, dual DOUTA/B and common CONVST; verify full eight-channel frame and BUSY | Serial software-mode reset/configuration through SDI; explicitly select/read back four DOUTA/B/C/D operation and ranges; do not assume reset defaults provide it |
| Timing | Actual ADC/FPGA voltage-corner, serial clock and framing requirements | Include TXU0204 direction/OE/propagation, 47 Ω paths, actual loads and FPGA setup/hold; ADC maximum clock is not system timing closure |

Separately implemented commissioning logic must hold GATE_EN low until supplies, reset/reference settling, configuration and fresh valid frames are established. Configuration loss, stale data or rail faults must inhibit switching. No implementation or pass is supplied by this procedure.

## Stage 4 — sensing, positive-bus OCP and latch

Inject bounded bidirectional current through each 5 mΩ phase shunt independently. Ideal INA240A1 phase sensitivity is 100 mV/A around VA5/2; ideal ±20 A spans midrail±2 V. Record actual gain/offset/linearity and calibration. NTC2 is another board location, not winding-temperature measurement.

Test the separate 2 mΩ bus shunt, grounded-reference INA240A1 and LM393LV active-low comparator. Ideal bus sensitivity is 40 mV/A and nominal **positive bus OCP is +25 A**. Determine actual trip interval at defined supply/temperature corners. This is neither reverse-current protection nor a three-phase window protector. External regeneration containment remains necessary.

Start with logic-level fault injection. A separately reviewed bounded-energy current fixture must then measure shunt-to-VGS-off delay, current slope/peak, PWM suppression and MOSFET stress; do not begin with a hard bus short. Test narrow pulses, clear/fault races, clear held high/during fault/with GATE_EN high and fault removal at different PWM phases. After recovery, ARMED and gate commands must stay inhibited until a deliberate new clear edge with enable low and healthy conditions. Record minimum-pulse and recovery/removal limitations.

## Stage 5 — encoder and low-energy gate switching

With bridge inhibited, use a controlled 5 V RS-422 ABZ source to verify J5 pairs, corrected U7 map, direction/Z, common-mode envelope and separately implemented PL counting. Confirm shield/return and termination; RT1–3 are DNP. AM26LV32E guarantees open-circuit failsafe only; shorted/idle/terminated inputs need explicit behavior qualification. Test F2 hot hold/trip, encoder inrush and cable-short response: a 0.5 A PTC marking is not a precise current limit.

For switching, keep motor disconnected and use a bounded-energy current-limited 24 V fixture with transient containment. Begin one leg at low duty using approved commissioning logic. Measure bootstrap precharge/refresh and maximum dwell, real VGS, deadtime/no overlap, switch-node overshoot and both-edge slew/ringing. Respect DRV8300D recommended SH voltage and 2 V/ns slew alongside MOSFET ratings. The 33 Ω gates are initial values, not waveform qualification. Recheck OCP and rail-loss shutdown under switching before any motor.

## Stage 6 — motor and rated qualification

Proceed only with measured acceptance for applicable previous stages and an already validated external sink/clamp. Start at 24 V and limited current with secured motor, reviewed motion constraints and stop behavior. Verify phase order and current/encoder directions before raising current or closing separately implemented control loops.

Increase voltage/current within demonstrated fixture/device limits. Record 10 Arms thermal soak at 40°C and quantified airflow, including relevant junction/case/connector/shunt/fuse/inductor temperatures. Qualify 20 A for 30 s only after fixing repetition/cooldown. Recheck auxiliary rails, gate waveforms, OCP, ADC recovery, encoder, externally contained regeneration and fan-failure shutdown/recovery.

All stages remain **NOT_RUN** here. Attach board-specific measured records and update only the corresponding result. Calculations, logic simulation and zero ERC/DRC are not physical execution.
