# Rev.A design calculations

Current confirmed baseline: **24-48 V, 10 A RMS continuous phase current, 20 kHz PWM; 20 A peak for 30 s; 40 degC maximum ambient; <=50 K temperature rise; forced-air cooling; 5 V ABZ encoder; brake circuit cancelled by latest user instruction; PSU absorption not assumed** (2026-10-10). Peak repetition interval, airflow/fan failure, encoder maximum/startup current remain pending. See [thermal and encoder design basis](brake_thermal_design_basis_2026-10-10.md) and [current qualification record](layout_followup_qualification_2026-10-10.md); these inputs do not close release gates.

## Current sensing

For each phase:

- `Rshunt = 5 mOhm`
- `Gain = 20 V/V`
- `Vout_delta = Iphase * Rshunt * Gain`

Therefore:

`Vout_delta = Iphase * 0.005 * 20 = 0.1 * Iphase [V]`

With VA5=5.1 V nominal and reference=VA5/2=2.55 V:

| Phase current | Amplifier output |
|---:|---:|
| -20 A | ~0.55 V |
| -15 A | ~1.05 V |
| -10 A | ~1.55 V |
| 0 A | ~2.55 V |
| +10 A | ~3.55 V |
| +15 A | ~4.05 V |
| +20 A | ~4.55 V |

Software phase-current limits require calibration and dynamic validation. The approved phase peak is 20 A for 30 s. The latest authorized hardware OCP is a separate **positive bus-current** detector with nominal +25 A trip; U2..U4 remain phase ADC measurement channels and have no OCP comparator taps. Bus current and phase current are different quantities, so the difference between 20 A phase peak and 25 A bus trip is not a no-nuisance-trip margin.

RSH4=2 mOhm lies between `VBUS_PROT` (terminal 1, U5.IN+ pin 8) and `VBUS_BRIDGE` (terminal 2, U5.IN- pin 1). U5 is INA240A1DR, gain 20 V/V, with both reference pins grounded. Its ideal positive transfer is `Vout = Ibus * 0.002 * 20 = 0.04 * Ibus`. R50=8.2k from VA5 and R53=2k to GND set `Vthreshold = VA5 * 2/10.2`, giving 1.000 V at VA5=5.1 V and `Itrip=1/0.04=25 A`. U15 LM393LVDDFR compares U5.OUT at IN- pin 2 with threshold at IN+ pin 3; positive overcurrent pulls OCP_N low. U15's unused comparator has IN+ pin 5 at GND, IN- pin 6 at threshold, and output pin 7 NC. U16/R51/R52 are removed. This circuit provides **no reverse-current OCP** and no phase-current window protection.

The fresh candidate XML (2026-10-10), `check_adc_validity.py` and `corner_current_limits()` give VA5=5.026621..5.173923 V. Combining this rail range, R50/R53 initial tolerance +/-0.1%, and RSH4 +/-1% yields **positive passive-only trip +24.357135..+25.659766 A**. This excludes divider/shunt temperature and lifetime drift, INA gain/offset/output swing and PWM common-mode recovery, LM393LV offset/overdrive/propagation, ripple, pull-up/logic/gate delay and fault-current overshoot. It is not a guaranteed trip interval or maximum fault current. The grounded-reference INA output near zero and negative current also requires bench characterization; no negative-current transfer or protection is claimed.

The [versioned static-budget evidence](sourcing/bus_ocp_static_budget_2026-10-10.json) records the native XML hash, OEM sources and limits. The extended static engineering budget in `bus_static_error_budget()` gives **+23.935464..+26.107636 A**, while preserving nominal +25 A. Its conditional calculation envelope is local component temperatures +25..+125 degC and DC bus common-mode 24..48 V; this is not permission to exceed the board's 90 degC hotspot target or another component's lower limit. The shunt OEM only specifies its TCR test over +25..+125 degC, so no cold-temperature bound is claimed.

| Term | Maximum/allocated magnitude used |
|---|---:|
| R50 PTFR0603B8K20P9 | Initial 0.1% + 25 ppm/degC × 105 K = 0.3625% |
| R53 TD03G2001BT | Initial 0.1% + 25 ppm/degC × 105 K = 0.3625% |
| RSH4 HoYLR2512-3W-2mR-1% | Initial 1% + 50 ppm/degC × 100 K = 1.5% |
| INA240 gain | 0.2% + 2.5 ppm/degC × 100 K = 0.225% |
| INA240 input offset | 25 uV + 250 nV/degC × 100 K, plus DC CMRR and PSRR = 87.739 uV |
| LM393LV input offset | Full-temperature 3 mV, plus DC CMRR and PSRR = 4.155 mV |

The [RESI PTFR ordering table](https://atta.szlcsc.com/upload/public/pdf/source/20250401/FF0B2EF5B31106388F28E532ECCD4B84.pdf) identifies code P as 25 ppm/degC; the [FH TD ordering table](https://atta.szlcsc.com/upload/public/pdf/source/20200616/C657321_2CFA27FA726BC0D0F6223AF922169515.pdf) identifies G as 25 ppm/degC. A conservative 105 K resistor span covers a +20 degC reference to +125 degC. [HoYLR's exact 2mOhm approval sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260807/2744A3B9486B05923CE3C700940B3DAC.pdf) specifies 50 ppm/degC. These initial-plus-TCR bounds do not include mounting or qualification-test drift.

The [INA240 electrical table](https://www.ti.com/lit/ds/symlink/ina240.pdf) supplies gain/offset limits and drift, minimum DC CMRR 120 dB and maximum PSRR 10 uV/V. The model allows common-mode change from the 12 V test point to 48 V and actual supply deviation from 5 V. The [LM393LV table](https://www.ti.com/lit/ds/symlink/lm393lv.pdf) supplies full-temperature +/-3 mV offset, 60 dB CMRR and 70 dB PSRR; drift is not added again. A 1.1 V comparator common-mode envelope bounds the threshold crossing.

The equation is `Itrip = ((Vthreshold + VOS_comparator) / G_actual - VOS_INA) / Rshunt_actual`, sweeping independent worst signs and both verified VA5 bounds. This remains **an engineering estimate, not a guaranteed trip interval**: LM393LV's quoted error-table conditions are at/up to 5 V, while actual VA5 is slightly higher; INA reference rejection and input-bias mismatch lack guaranteed maxima for this application. Grounded-reference transfer, Kelvin/thermoelectric errors, reflow, load-life/humidity drift, PWM transients and dynamic fault overshoot still need qualification. The OEM shunt's separate reliability-test allowances cannot be treated as zero drift or collapsed into a lifetime guarantee. The model checks the three exact MPNs before using their TCRs; an alternate needs its own reviewed budget.

RSH4 dissipates 1.25 W at a constant 25 A and 0.8 W at a constant 20 A. Its bus RMS current, pulse energy, mounted temperature and independent inner-land Kelvin pickups require separate qualification; phase RMS current cannot be substituted for bus RMS current.

Shunt dissipation is `P = I_RMS^2 * R`:

| RMS current | Shunt dissipation |
|---:|---:|
| 10 A | 0.50 W |
| 15 A | 1.125 W |
| 20 A | 2.00 W |
| 25 A | 3.125 W |

Select HoYLR2512-3W-5mR-1% (3 W, two-terminal SMD). Apply independent inner-land Kelvin pickup and verify its derating and assembled temperature. A 3920 >=5 W alternative is the fallback if the 2512 assembly cannot meet the thermal limit.

At the confirmed 10 A RMS, each nominal shunt dissipates 0.5 W. A phase held at the 20 A magnitude bound dissipates 2 W; for 30 s this is 60 J per shunt, before resistance tolerance and temperature drift. A sinusoidal phase with 20 A instantaneous amplitude has a different RMS loss; use the 2 W value as a conservative per-shunt upper envelope until the actual peak waveform is specified. With baseline 10 A RMS and a conservative 20 A flat-current interval occupying fraction d, the illustrative average is `Pshunt=0.5+1.5d W`; for a start-to-start repetition period Trep, `d=30/Trep` with Trep>=30 s. No repetition period is assumed.

At 40 degC ambient, the general 50 K rise target corresponds to a 90 degC measured hotspot limit, subject to every component's lower qualified limit. A 50 K rise implies an effective shunt-to-ambient thermal resistance <=100 K/W at steady 0.5 W, or <=25 K/W at steady 2 W; these are assembly targets, not package ratings. For a first 30 s pulse from an established 10 A RMS thermal state, an illustrative linear thermal model requires `0.5*Rtheta_steady + 1.5*Ztheta(30s) <=50 K`; repeated pulses require accumulation, hot resistance and airflow validation. The shunt's nominal 3 W rating does not prove this condition. U26's current maximum-delay qualification is limited to 85 degC local free-air temperature, hence <=45 K local rise at the confirmed ambient. Forced air requires minimum airflow, blockage/fan-loss handling and assembled-board soak evidence.

## ADC resolution

The ADS8588S is configured for ±5 V input range. The nominal LSB is:

`10 V / 65536 = 152.6 uV/LSB`

Since current sensitivity is `0.1 V/A`, the ideal code resolution is:

`152.6 uV / 0.1 V/A = 1.526 mA/LSB`

Noise, PWM common-mode transients, reference error and layout dominate before quantization does.

## Bus-voltage divider

Rev.A nominal divider:

- high side: 280 k + 280 k
- low side: 39 k
- total: 599 k

`Vadc = Vbus * 39 / 599 = 0.065108 * Vbus`

| VBUS | ADC voltage |
|---:|---:|
| 24 V | 1.563 V |
| 48 V | 3.125 V |
| 55 V | 3.581 V |
| 60 V | 3.906 V |
| 75 V | 4.883 V |

The board is not specified for 75 V continuous operation; this table only shows divider headroom.

The operating range is 24-48 V; every table row above 48 V is calculation-only. C5=10nF and `(560k || 39k)` give tau=364.608us and fc=436.51Hz. This bus-monitor filter cannot be treated as fast hardware overvoltage protection.

## MOSFET conduction sanity check

For one current path through two BSC040N10NS5 devices, using 4 mOhm each at the datasheet test condition:

`Ppath ~= I^2 * 8 mOhm`

- 10 A -> 0.8 W instantaneous conduction path loss
- 15 A -> 1.8 W (historical comparison)
- 20 A -> 3.2 W
- 25 A -> 5.0 W

Actual inverter dissipation must be computed over PWM duty, device temperature, switching energy and dead-time diode conduction. These values are only a first-order check.

## Gate-drive current sanity check

U1 is the non-inverted **DRV8300DPWR**, with integrated bootstrap diodes. The DI variant is not interchangeable with the hardware all-low inhibit. D2..D4 are removed; CBOOT1..3 are 470 nF between BST and the corresponding switch node, and RG1..6 are 33 ohm. See the [TI DRV8300 datasheet](https://www.ti.com/lit/ds/symlink/drv8300.pdf) for the D/DI input distinction and PW20 pin map. All six input commands are gated; FPGA deadtime remains at least 500 ns, pending measured switching verification.

Using BSC040N10NS5 Qg=72 nC as an illustrative charge and the driver's typical 0.75 A source/1.5 A sink capabilities gives Q/I=96 ns/48 ns. These are ratios, not guaranteed switching or fault turn-off times: 33 ohm resistance, Miller charge, gate voltage, driver impedance and board inductance dominate actual waveforms. One 72 nC charge from a nominal 470 nF bootstrap capacitor gives an ideal 0.153 V droop before effective-capacitance derating, quiescent/leakage charge, duty-cycle hold time and recharge losses. Bootstrap refresh, UVLO, effective capacitance and full shutdown latency remain unqualified.

## Onboard input fuse

F1 is **Littelfuse 0456025.ER**, a 25 A very-fast-acting SMD fuse on the PCB. J3.1 and F1.1 are VIN_RAW; F1.2, Q7 drain and the U18 LM74502 reverse-polarity controller input are VIN_FUSED. The LM5164 auxiliary regulator is supplied from VBUS_PROT, downstream of reverse-polarity protection. J6 is only the excluded external system interface; no external fuse or holder is required by this design revision.

The [Littelfuse 456 datasheet](https://www.littelfuse.com/assetdocs/littelfuse_fuse_456_datasheet.pdf?assetguid=d86b18f9-14fa-4764-87ff-8aec12e9a89d) specifies the **25 A row** at 500 A interrupting capacity at 72 VDC, and 1000 A at 32 VDC. Its 125 VAC label does not establish a 125 VDC rating. The 72 VDC rating exceeds the 48 V operating maximum; regeneration/surge bus voltage <=72 V and prospective source fault current <=500 A remain open qualification requirements for this prototype selection. Catalog stock is not electrical qualification.

Nominal cold resistance is 1.92 mOhm and nominal melting I²t is 45 A²s; neither alone proves fault coordination. Manufacturer time-current, continuous-current/ambient derating, inrush, source/cable energy and mounted-temperature limits must be met. OEM thermal conditions use broad 100 um copper; the present two-layer copper/via implementation does not independently prove 25 A operation. F1 does not replace fast bus OCP or limit fault current to 25 A. This is a documented critical single-source prototype exception.

## VA5 validity and R92 tolerance

U25 TPS389001DSER senses VA5 through R92=3.24k/R93=1k while powered independently by VIO. R92's selected 0.1%, 25 ppm/C primary and reviewed alternative use a common +/-0.702% static budget; R93/R94/R95 use +/-0.25% including their stated allocations. These are prototype budgets derived from separate qualification tests/allocations, not a combined-environment or lifetime guarantee.

`check_adc_validity.py` calculates falling shutdown threshold 4.791889..4.961002 V, maximum recovery 5.001931 V, and regulated VA5 5.026621..5.173923 V. The minimum falling threshold is 41.889 mV above ADS8588S's 4.75 V minimum. The allocated 10 mV normal ripple still leaves static recovery headroom. This does not qualify fast droop: TPS3890's 18 us typical delay at 5% overdrive is not a guaranteed maximum, and the complete supervisor-to-MOSFET shutdown chain remains open.

## Two-layer current routing

The high-current path must not rely on a single narrow trace. Plan wide top-layer copper, bottom reinforcement and qualified stitching near terminals/MOSFETs/shunts. The prior routed PCB is a development baseline; SMD-shunt integration requires fresh routing, DRC and thermal review. Verify temperature rise on the actual stack-up and copper weight.

## Local passive simulation (2026-10-10)

`tools/simulate_layout_entry.py` extracts actual passive values and checks their physical-pin topology in a fresh KiCad XML netlist before emitting six ngspice decks, CSV waveforms, JSON results and a plot. This is not a complete inverter/device simulation.

- R40/C40: tau=47ns, fc=3.386MHz; 20kHz attenuation is only -0.0001515dB. The filter does not remove PWM ripple and serves only the phase ADC. Its ideal 2.5-to-4.9 V step crosses the 3.7 V midpoint at about 1.03358 us for a step beginning at 1.001 us; this is phase ADC settling, not bus OCP delay.
- R88/C92: tau=1us with an ideal FPGA output. No Schmitt threshold, propagation, metastability or power-ramp model is included.
- C1+C2=200uF nominal: an unsunk ideal 1A regeneration current raises 48V to 55V in 1.4ms, storing only 0.0721J extra. 55V is an overvoltage example, not an operating allowance.
- Three 5mOhm shunts at 10A RMS dissipate 0.5W each, 1.5W total. Package rating alone does not qualify assembly temperature.

Full current/thermal/switching qualification remains open; see [power-stage review](power_stage_layout_review_2026-10-09.md) and [analog/safety review](analog_safety_layout_review_2026-10-09.md).


## Kelvin electrical-node modeling

The selected two-terminal SMD shunt has one physical terminal per side. Independent sense and force traces meet within that terminal land and share its electrical node:

- U phase: `SW_U` and `PH_U`
- V phase: `SW_V` and `PH_V`
- W phase: `SW_W` and `PH_W`
- Bus: `VBUS_PROT` and `VBUS_BRIDGE`

Kelvin behavior is enforced in PCB routing: each INA240 input trace must originate independently at the inner edge of the corresponding two-terminal SMD shunt pad. Force and sense copper may meet only within that terminal land. A two-terminal shunt must not be represented by invented physical sense pins or jumper groups. PCB integration and thermal qualification are separate gates.
