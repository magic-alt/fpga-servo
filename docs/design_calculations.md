# Rev.A design calculations

## Current sensing

For each phase:

- `Rshunt = 5 mOhm`
- `Gain = 20 V/V`
- `Vout_delta = Iphase * Rshunt * Gain`

Therefore:

`Vout_delta = Iphase * 0.005 * 20 = 0.1 * Iphase [V]`

With a 2.5 V reference:

| Phase current | Amplifier output |
|---:|---:|
| -25 A | ~0.0 V |
| -20 A | ~0.5 V |
| -15 A | ~1.0 V |
| 0 A | ~2.5 V |
| +15 A | ~4.0 V |
| +20 A | ~4.5 V |
| +25 A | ~5.0 V |

Practical software limits should be set below the output rails; ±20 A is a comfortable calibrated measurement range and ±25 A is a short-duration hardware envelope.

Shunt dissipation is `P = I_RMS^2 * R`:

| RMS current | Shunt dissipation |
|---:|---:|
| 10 A | 0.50 W |
| 15 A | 1.125 W |
| 20 A | 2.00 W |
| 25 A | 3.125 W |

Use a >=5 W Kelvin shunt and verify its derating curve on the assembled PCB.

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

## MOSFET conduction sanity check

For one current path through two BSC040N10NS5 devices, using 4 mOhm each at the datasheet test condition:

`Ppath ~= I^2 * 8 mOhm`

- 15 A -> 1.8 W instantaneous conduction path loss
- 20 A -> 3.2 W
- 25 A -> 5.0 W

Actual inverter dissipation must be computed over PWM duty, device temperature, switching energy and dead-time diode conduction. These values are only a first-order check.

## Gate-drive current sanity check

BSC040N10NS5 total gate charge is on the order of tens of nC. With a 20 kHz PWM rate, average gate-charge power is modest, but peak source/sink current and gate-loop inductance dominate switching quality. FD6288 output capability is adequate for a first Rev.A prototype; final gate resistance is a bench-tuning item.

## Two-layer current routing

The high-current path must not rely on a single narrow trace. Rev.A layout uses wide top-layer copper regions with bottom-layer reinforcement and dense stitching near terminals/MOSFETs/shunts. Final copper temperature rise must be verified on the actual stack-up and copper weight.
