# Final dual-board power and supply review — 2026-10-19

**No newly demonstrated static electrical fault was identified in this read-only power review. Human engineering and fabrication-process acceptance remain OPEN; physical qualification remains NOT_RUN.** The reviewed canonical boards are:

| Project | Canonical board | SHA-256 |
| --- | --- | --- |
| AD7606C | `hardware/ad7606c_servo/ax7010_servo_ad7606c.kicad_pcb` | `dc0fb0a39529daa627db700bc2f53dd435f776633b9bd93aa8b1f0053b5f2134` |
| ADS8588S | `hardware/ads8588s_servo/ax7010_servo_reva.kicad_pcb` | `e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226` |

Existing final native DRC artifacts record zero violations, unconnected items and schematic-parity items. This review reads those reports; it does not claim another DRC execution or motor/thermal acceptance. [Companion JSON](final_power_review.json) binds actual geometry, calculations, UUID inventories, reports and maps by hash. No PCB was modified. Earlier AD `729dea…` and ADS `a4b815…` reports/maps are historical.

The application is 24–48 V, 20 kHz PWM, 10 Arms continuous phase current and **20 A instantaneous sinusoidal phase amplitude for 30 s**, equivalent to 14.142 Arms during that interval; this is not a 20 Arms rating. Ambient is 40°C with forced air whose velocity remains unqualified. The 12 V source has a **1 A total** budget including downstream-converter input current. Outer/inner copper is 70/30 µm. Before motor operation, a verified external sink/clamp on protected-bus J7 must hold actual bus voltage, including overshoot, at or below 60 V. Ordinary supply absorption is not assumed.

Both final boards have the same screened VDRV path from C22.1 to U1.7: **92.85247 mm** of track and four through-vias. Its 0.6 mm outer-layer portion totals 40.01391 mm, section 0.042 mm². Other portions are 1.0, 0.8, 0.4 and 0.3 mm wide; the 0.3 mm portions total 8.97581 mm. The model uses copper resistivity 1.724e−8 Ω·m at 25°C, coefficient 0.00393/K, and conservative 1.8 mm via barrels with **assumed 18 µm copper walls**. Actual minimum plating requires substantiation; resin fill contributes no credited conduction.

Path resistance is 46.720 mΩ at 25°C and 58.654 mΩ at 90°C. Assigning the entire accepted 1 A budget to this branch gives 58.65 mV drop and 58.65 mW loss at 90°C. Legacy IPC-2221 external-trace screens give approximately 1.02 K rise for 0.6 mm and 3.20 K for 0.3 mm at 1 A. These screens exclude mutual heating, pulsed current, copper/plating tolerances and actual sharing; they are not measured temperatures. C46/C69 are nominally 100 nF/10 µF. Effective capacitance, local gate-return impedance, independent rail sequences and actual VGS remain unqualified.

Native pad/annulus intersections give these same local contacts on both boards, counting unique via UUIDs:

| Devices | Drain contacts | Source contacts |
| --- | --- | --- |
| Q1/Q3/Q5, high side | **No local drain-pad via** | Two SW vias each, diameter/drill 0.8/0.4 mm |
| Q2/Q4/Q6, low side | Six SW vias each, 1.0/0.5 mm | Three GND vias each, 1.0/0.5 mm |
| Q7/Q8, protection | Twelve vias each, 0.8/0.4 mm | No direct source-pad via contact |

High-side drain heat first spreads through top-side VBUS_BRIDGE copper. Low-side six-via thermal behavior cannot be assigned to high-side devices. The missing high-side local drain array is a thermal qualification limitation, not a newly proven static circuit fault.

Conservatively assigning peak-regime transistor current of 10 Arms to each bridge array gives barrel-loss screens at 90°C of 0.0861 W for two 0.4 mm source vias, 0.0459 W for three 0.5 mm source vias and 0.0230 W for six 0.5 mm drain vias. Twelve protection drain vias at the 17.3205 Arms normal-bus bound screen at 0.0431 W. Equal sharing is only an allocation assumption; parallel top copper may also carry current. These values do not prove via temperature, fatigue life or equal sharing.

For semiconductor conduction, twice the 25°C RDS value gives an engineering allocation of 8 mΩ per MOSFET, **not an OEM guaranteed hot maximum**. Balanced sinusoidal modulation gives bridge conduction of 2.4/4.8 W continuously/peak interval, approximately 0.4/0.8 W per device. Normal-bus RMS bounds of 12.247/17.321 A give Q7+Q8 combined conduction of 2.4/4.8 W. Switching, diode recovery, deadtime, gate drive, fuse and copper losses are additional. Each 5 mΩ phase shunt screens at 0.5/1.0 W; the 2 mΩ bus shunt at 0.3/0.6 W. No achieved case or junction temperature follows from these allocations.

The whole-board reserved-plane guard now checks tracks, arcs and copper zones, including footprint-owned zones and empty-net copper. Both boards have **zero non-GND tracks or copper zones on In1**. Foreign-net through-via antipads remain: **433 AD / 370 ADS**. The complete UUID/net/annulus inventories are included; annulus bounds are not void bounds. L1's footprint rule area is a keepout, not copper. These facts do not prove a uniform-current sheet or impedance-free return.

Old ADS `a4b815…` retained fourteen VA5 In1 tracks and is superseded. The repair removes old branches and adds an explicit physical VA5 bridge; the parent's native witness verifies the original two zone components and their 32 actual pads become connected. It is not justified as merely deleting unused copper. The unchanged guard rejects the old board with fourteen violations and accepts final `e68d2fb…` with zero.

Actual filled GND zones were sampled across X=82–122 mm at eleven horizontal cuts on each board. The smallest sampled In1 aggregate width is 25.9 mm at Y=59 mm, section 0.777 mm² at 30 µm; sampled F/B aggregate widths there are 12.55/16.35 mm. These sums include disconnected runs and exclude tracks/pads. They are **not** certified minimum necks, sharing budgets or thermal passes. Local copper and source-pad arrays add paths; return spreading and PWM edge impedance require measurement.

The bank retains **0.630145 W** worst damping-resistor allocation using `11 A / (10 × 0.8)` and 1% resistance tolerance, below the 0.708 W budget at 90°C. The historical 0.589 W model is superseded. Controlled two-stage startup and the external clamp remain prerequisites. Connect at 0 V with motor/encoder/external 12 V loads disconnected and bridge inhibited. Stage 1 is ≤10 V, ≤0.1 A; advance only after independent TP1 ≥9.5 V and measured FET enhancement/low-VDS conditions. Stage 2 then ramps ≤1 V/ms toward 24/48 V with ≤2 A limit. This fixture procedure does not qualify normal 10 V operation or hot plugging. See [the static budget](power_static_budget.md) for full conditions and assumptions.

| Project | Electrical vias requiring POFV | Component PTH, not POFV | Included H1–H4 | Total PTH |
| --- | ---: | ---: | ---: | ---: |
| AD7606C | 511 | 83 | 4 | 594 |
| ADS8588S | 468 | 83 | 4 | 551 |

Each component-hole count comprises 79 ordinary holes plus four mounting PTH. Native mounting identity, position, drill and plating match each project's original baseline exactly. [AD map](../../../artifacts/dual-servo/final-power-dual-20261019-r2/ad7606c/pofv-map/all-via-pofv-map.pdf) and [ADS map](../../../artifacts/dual-servo/final-power-dual-20261019-r2/ads8588s/pofv-map/all-via-pofv-map.pdf) each contain three pages, with overview/detail PNGs, complete UUID/XY CSVs and hashed manifests alongside. Via-in-pad assembly uses the selected paid four-layer Type VII epoxy-filled, planarized, copper-capped POFV process. These are process-selection drawings; vendor acceptance remains OPEN.

Scope measurements, rail sequences, gate behavior, OCP timing/fault injection, source-fault/inrush response, regeneration clamp, ADC noise/settling, thermal loading and motor tests remain **NOT_RUN**. Human sign-off and vendor process acceptance remain **OPEN**.
