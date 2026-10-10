# LCSC sourcing review — 2026-10-10

**Current delivery scope (user revision, 2026-10-10): BOM and schematic only. PCB/layout repair is deferred. The working PCB retains earlier development edits and is not synchronized to the final bus-OCP schematic; the isolated unfinished routing candidate is not adopted. Do not use this board for fabrication or reuse historical zero-DRC/parity claims for the current schematic.**


The current procurement export covers **148 fitted purchased references in 68 groups** from the merged 159-component BOM. All 68 selected groups have dated Chinese-storefront stock sufficient for five boards plus 20% spares, rounded to the recorded order multiple. This is **limited-energy prototype sourcing eligibility**, not fabrication approval, a stock reservation, a checkout quotation, or full-power component qualification. PCB DRC, electrical release gates and bench validation are reported separately; this review does not assert final DRC clearance.

`python tools/export_procurement.py` regenerates [procurement_candidates.csv](../hardware/procurement_candidates.csv) from the current BOM and [selected overrides](sourcing/selected_overrides_2026-10-10.json). Overrides take precedence over historical grouped candidates. A BOM MPN, C-code or required-footprint mismatch becomes `SELECTED_PENDING_BOM_OR_FOOTPRINT`; missing evidence becomes `UNRESOLVED_SOURCE_EVIDENCE`. Unqualified candidates and insufficient inventory remain separate dispositions. Every fitted purchased reference appears once. Unknown future references cannot inherit qualification merely by sharing a value or MPN.

Historical `passive_2026-10-10.json`, `critical_2026-10-10.json` and `shunt_2026-10-10.json` remain unchanged. New `*_selected_evidence_*` and `*_selected_stock_*` files preserve the later source records, OEM links, timestamps and qualification conditions. Displayed prices are reference starting prices, not quantity-tier quotes. Refresh stock and checkout multiples before ordering.

## Final selected changes

| References | Selected part / Chinese LCSC code | Scope and remaining conditions |
|---|---|---|
| U1 | TI DRV8300DPWR / C3036056 | Noninverting D version, internal bootstrap diodes; critical single-source exception. Gate discharge, UVLO, bootstrap refresh, SH slew and power-stage validation remain open. |
| CBOOT1–3 | Fenghua 0805B474K500NT / C49955 | 470 nF, 50 V, X7R, 0805. The illustrative 143 nC / 1 V bootstrap budget requires ≥143 nF effective capacitance; actual maximum charge/on-time still needs qualification. Keep maximum capacitance ≤1 µF. Generic OEM data do not prove the bias minimum. Walsin alternate has the same application gate. |
| RG1–6 | Fenghua RS-03K33R0FT / C125766 | 33 Ω, 1%, 0603; UNI-ROYAL alternate. Gate pulse and switching tuning remain open. |
| F1 | Littelfuse 0456025.ER / C315877 | Onboard SMD fuse. Exact 25 A row: 500 A interruption at 72 VDC, 1000 A at 32 VDC. Do not transfer the catalog 125 V label into a DC rating. Source fault level, thermal derating, inrush and coordination remain open; no qualified direct alternate. |
| U2–5 | TI INA240A1DR / C2060769 | Gain 20 V/V. Phase channels retain 5 mΩ sensing; U5 measures positive bus current with grounded references and 2 mΩ shunt. Common-mode transients/recovery remain open. |
| U15 | TI LM393LVDDFR / C5213974 | One active positive bus OCP comparator. Input and output tolerate independent 0–5.5 V with supply off; POR output is high impedance. Unused comparator inputs are separated and output NC. No intrinsic hysteresis; complete latch/timing/noise verification remains necessary. |
| RSH4 | Milliohm HoYLR2512-3W-2mR-1% / C5375458 | 2 mΩ, 3 W, 1%; 1.25 W at 25 A. RALEC alternate requires different recommended land review; thermal/pulse qualification remains open. |
| R50 / R53 | RESI PTFR0603B8K20P9 / C351624; Fenghua TD03G2001BT / C666953 | 8.2 kΩ / 2.0 kΩ, 0.1%, 25 ppm/°C, 0603. From 5.1 V, threshold is nominally 1 V = +25 A with gain20 and 2 mΩ. Yageo/Panasonic alternatives are separately recorded. |
| RSH1–3 | Milliohm HoYLR2512-3W-5mR-1% / C5375461 | Native two-terminal lands with Kelvin pickups. 0.5 W at 10 A; 2 W at 20 A. RALEC alternate and all thermal/assembly qualification remain conditional. |
| J1 / J5 | JILN 321040SG0ABK00A01 / C601944; 321010SG0ABK00A01 / C429962 | OEM key slot on odd-pin side, 2.54 mm grid. Shared recommended finished hole 1.02 ±0.03 mm fits both candidate vendor limits. BOOMELE alternatives remain conditional on OEM provenance and ≤1 A/pin demand; JILN is rated 3 A. |
| F2 | JDT ASMD1812-050 / C135358 | 15 V PTC, 0.5 A hold near room temperature. Local ambient ≤85°C and derated hold current required. Bourns MF-MSMF050-2 / C17313 has a different recommended land and remains conditional. |
| NTC1–2 | Shiheng CMFA 103F3950 / C2889049 | OEM NTC land; KUU alternate requires the same temperature calibration and assembly checks. |
| J4 | KEFA KF950-9.5-3P / C475107 | Vendor footprint selected; connection resistance, wiring and full-load heating remain release checks. |
| L1 | SOREDE SDRH.1209.LF680MT00 / C2942326 | 68 µH, native OEM land. Initial total 12 V load ≤0.5 A is a conservative test cap. No OEM Irms rating; guaranteed 1 A, hot inductance and thermal performance unresolved. No qualified alternate. |
| L2 | Sunlord SWPA4020S2R2MT / C83423 | Exact M20 OEM data and native land reviewed. cjiang FHD4020S-2R2MT / C602029 shares the OEM land; hot/thermal/assembly validation remains open. |
| C3 / C4 / C94 | Faratronic C212E105J6BC000 / C604836; TDK C4532C0G2A104JT000N / C342611; Murata GRT31C5C1H104FA02L / C3839854 | Corrected P15 film, 1812 C0G and 1206 C0G footprints. C3 bus pulse/ripple and C94 recovery timing remain application gates. A 5% C94 alternative is not an equivalent for the selected 1% requirement. |
| R92 | Fenghua TD03G3241BT / C666977 | Selected 3.24 kΩ, 0.1%, ≤25 ppm/°C specification and static corner budget; Yageo RT0603BRB073K24L / C860367 alternate. Qualification-test drift limits are not guaranteed lifetime drift bounds. |

## Exclusions and interpretation

U16, R51, R52, D2–D4 and J2 are removed by the final architecture. D1, R32 and RT1–3 are DNP options. J6 is an external system interface; F1_HOLDER is obsolete. TP1–5 are bare PCB pads and need no MPN. None contributes to order quantity.

Domestic preference means mainland manufacturers such as Fenghua, RESI, Milliohm, JILN, JDT, Shiheng, KEFA, SOREDE and Sunlord. Taiwan manufacturers such as Yageo, UNI-ROYAL, RALEC and Walsin are identified separately; they are not described as mainland brands. Critical imported exceptions and unavailable or conditional alternates remain explicit in the evidence.

The CSV's `SOURCED_PROTOTYPE_ELIGIBLE` disposition confirms source evidence, current BOM identity and available snapshot quantity. It does not close the conditions in `Qualification`, `Alternate qualification` or `Notes`, and it does not authorize substituting an alternate automatically. No parts have been purchased or reserved by this export.

C19 and C25 now have stocked cross-manufacturer alternates: Walsin 0805B104K101CT / C77456 (100 nF, 10%, 100 V, X7R, 0805; China stock 26,000 at 15:34:54 UTC) and Yageo CC0603JRX7R9BB332 / C519530 (3.3 nF, 5%, 50 V, X7R, 0603; stock 34,900 at 15:35:03 UTC). OEM package and parameter evidence is recorded in [the alternate snapshot](sourcing/c19_c25_alternate_evidence_2026-10-10.json); both retain existing lands. Walsin and Yageo are Taiwan manufacturers. C19 bus transients/DC bias and C25 control-loop tuning remain application checks. The earlier Walsin 5% suggestion was rejected for zero stock. J4 now links to the [KEFA manufacturer product](https://www.cnkefa.com/products/7736.html), correcting the historical Phoenix link.

## Final schematic verification

Fresh native export: 159 system objects /135 nets; PCB-target native netlist:158 components /135 nets. ERC:0 errors /0 warnings /0 exclusions; four pre-existing ignored categories were not changed. Five schematic/grid/layout/connectivity/power-wiring checks, physical-pin safety, 531 digital latch scenarios, six ADC tests and 27 Gate A/B tests pass. All eight PDF pages and dense supply/ground regions were visually reviewed.

`check_design.py` remains FAILED because the deferred working PCB lacks the final U5/RSH4/U15 footprint and package-rule changes. This is recorded without reducing severities or exclusions. Gate A/B remain BLOCKED for electrical/thermal/dynamic qualification. The isolated unfinished PCB candidate was not adopted.

Evidence: [verification JSON](reviews/selection_2026-10-10/verification.json), [native ERC](reviews/selection_2026-10-10/erc.json), [reviewed schematic PDF](reviews/selection_2026-10-10/schematic.pdf), [physical-pin delta](reviews/selection_2026-10-10/physical-pin-delta.json).
