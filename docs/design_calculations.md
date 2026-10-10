> **CURRENT TOPOLOGY OVERRIDE (2026-10-10):** Three 5mR shunts in Q2/Q4/Q6 low-side source returns, NOT phase outputs. Existing gain 20 V/V produces nominal 0.1 V/A only when lower-device conduction window is valid. The PCB is not synchronized. Refer to [low-side migration](low_side_3shunt_migration_2026-10-10.md) before using historical calculations.

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

Software limits require calibration and dynamic validation. The approved peak input is now 20 A; historical 25 A is not an operating requirement. Hardware OCP nominally trips at ±22.5 A from the 10k/160k dividers at 5.1 V. Fresh XML export (2026-10-10) and `check_adc_validity.py` yield static VA5=5.026621..5.173923 V. Using this rail range, divider ±0.1% and shunt ±1% gives a passive-only trip magnitude of 21.951188..23.062477 A, leaving 1.951188 A from the 20 A peak to the earliest calculated trip. This excludes resistor/shunt temperature and lifetime drift, INA/comparator errors, ripple and total gate-off delay. The generic divider/shunt MPNs and complete error budget remain unqualified; this is not a guaranteed no-nuisance-trip margin or a maximum fault current. Do not set the OCP nominal threshold to 20 A merely to match the operating peak.

Shunt dissipation is `P = I_RMS^2 * R`:

| RMS current | Shunt dissipation |
|---:|---:|
| 10 A | 0.50 W |
| 15 A | 1.125 W |
| 20 A | 2.00 W |
| 25 A | 3.125 W |

Use a >=5 W Kelvin shunt and verify its derating curve on the assembled PCB.

At the confirmed 10 A RMS, each nominal shunt dissipates 0.5 W. A phase held at the 20 A magnitude bound dissipates 2 W; for 30 s this is 60 J per shunt, before resistance tolerance and temperature drift. A sinusoidal phase with 20 A instantaneous amplitude has a different RMS loss; use the 2 W value as a conservative per-shunt upper envelope until the actual peak waveform is specified. With baseline 10 A RMS and a conservative 20 A flat-current interval occupying fraction d, the illustrative average is `Pshunt=0.5+1.5d W`; for a start-to-start repetition period Trep, `d=30/Trep` with Trep>=30 s. No repetition period is assumed.

At 40 degC ambient, the general 50 K rise target corresponds to a 90 degC measured hotspot limit, subject to every component's lower qualified limit. A 50 K rise implies an effective shunt-to-ambient thermal resistance <=100 K/W at steady 0.5 W, or <=25 K/W at steady 2 W; these are assembly targets, not package ratings. For a first 30 s pulse from an established 10 A RMS thermal state, an illustrative linear thermal model requires `0.5*Rtheta_steady + 1.5*Ztheta(30s) <=50 K`; repeated pulses require accumulation, hot resistance and airflow validation. The shunt's nominal 5 W rating does not prove this condition. U26's current maximum-delay qualification is limited to 85 degC local free-air temperature, hence <=45 K local rise at the confirmed ambient. Forced air requires minimum airflow, blockage/fan-loss handling and assembled-board soak evidence.

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

BSC040N10NS5 gate charge is on the order of tens of nC. At 20 kHz, average charge current does not qualify peak drive, switching quality or bootstrap hold time. FD6288 capability, effective CBOOT, refresh protocol and gate resistance require current datasheet and bench review. D2..D4 symbol/footprint polarity is corrected to K1/A2; see [repair record](layout_entry_repair_2026-10-09.md).

## Two-layer current routing

The high-current path must not rely on a single narrow trace. Plan wide top-layer copper, bottom reinforcement and qualified stitching near terminals/MOSFETs/shunts. The current PCB has zero vias and incomplete routing; these are requirements, not completed features. Verify temperature rise on the actual stack-up and copper weight.

## Local passive simulation (2026-10-09)

`tools/simulate_layout_entry.py` extracts actual passive values and checks their physical-pin topology in a fresh KiCad XML netlist before emitting six ngspice decks, CSV waveforms, JSON results and a plot. This is not a complete inverter/device simulation.

- R40/C40: tau=47ns, fc=3.386MHz; 20kHz attenuation is only -0.0001515dB. The filter does not remove PWM ripple and is shared by ADC/OCP.
- R88/C92: tau=1us with an ideal FPGA output. No Schmitt threshold, propagation, metastability or power-ramp model is included.
- C1+C2=200uF nominal: an unsunk ideal 1A regeneration current raises 48V to 55V in 1.4ms, storing only 0.0721J extra. 55V is an overvoltage example, not an operating allowance.
- Three 5mOhm shunts at 10A RMS dissipate 0.5W each, 1.5W total. Package rating alone does not qualify assembly temperature.

Full current/thermal/switching qualification remains open; see [power-stage review](power_stage_layout_review_2026-10-09.md) and [analog/safety review](analog_safety_layout_review_2026-10-09.md).


## Kelvin electrical-node modeling

A four-terminal current shunt has separate force and sense pads, but the Kelvin pad on each side is electrically the same node as the corresponding force pad. Rev.A1 therefore models each side with the same net name:

- U phase: `SW_U` and `PH_U`
- V phase: `SW_V` and `PH_V`
- W phase: `SW_W` and `PH_W`

Kelvin behavior is enforced in PCB routing: each INA241 input trace must originate independently at the dedicated shunt sense pad and must not share load-current copper before that terminal. Separate schematic pseudo-nets would incorrectly make the four-terminal shunt electrically open unless a formal net-tie model were added.
