# AD7606C 12 V / total 1 A power ECO — 2026-10-18

User requirement: 12 V auxiliary rail must support **1 A continuous total load** at the existing 24–48 V input and 40 C ambient design target. The budget includes gate drive, the input power of the downstream 5.1 V converter, and other 12 V consumers; it is not an additional 1 A external output. Board startup, temperature rise, dynamic regulation and fabrication qualification remain open.

## Changes

| Reference | Previous | Current primary |
| --- | --- | --- |
| L1 | SOREDE 68 uH; substantiated Irms unavailable | Wurth 7447709151, 150 uH +/-20%, 2.1 A rated RMS, 2.7 A typical at 10% L drop, 200 mOhm max at 20 C |
| R21 | 453 kOhm / 1% | Yageo RT0603BRD07442KL, 442 kOhm / 0.1% / 25 ppm/K |
| R22 | 49.9 kOhm / 1% | Yageo RT0603BRD0749K9L, 49.9 kOhm / 0.1% / 25 ppm/K |
| R23 | 453 kOhm ripple injection RA | Yageo RC0603FR-07200KL, 200 kOhm / 1% |
| C25 | 3.3 nF X7R | Murata GRM1885C1H332JA01D, 3.3 nF C0G / 50 V / 5% |

U12 LM5164, its bootstrap capacitor, RON, C26 and all electrical connections are retained. Exact L1/R21/R22/R23/C25 identities are declared in project configuration; the original ADS8588S project is unchanged. Identity ECOs do not exempt any physical pin from the inherited connectivity comparison.

## Calculation and limits

The old 68 uH corner exceeds the LM5164 1.25 A minimum peak limit. Independently, the old 453k/3.3nF ripple network is below the recommended 20 mV at 24 V input. Both are now negative regressions. The lower nominal feedback ratio and precise R21/R22 bound the output envelope after increasing the ripple amplitude.

The [profile](../aux_power_profile.json) records manufacturer facts separately from engineering allowances: frequency 240–360 kHz, effective minimum L = 150uH x 0.8 x 0.9 x 0.9 = 97.2 uH, 0.7 RMS and 0.8 typical-saturation factors. Feedback resistors use 0.1% initial + 0.25% TCR + 0.5% drift allocation; RA uses 2.5% and C0G CA 6.5% total budgets. Minimum coupling gain is 0.95. These are design assumptions to verify, not guaranteed manufacturer limits or lifetime qualifications.

| Calculated bound | Result |
| --- | --- |
| 1 A load, 24 V input, maximum ripple corner | 1.1283 A peak |
| 1 A load, 48 V input, maximum ripple corner | 1.1992 A peak |
| Minimum margin to minimum IC peak limit | 50.83 mA |
| Maximum inductor RMS | 1.0066 A |
| Maximum-limit + 100 ns delay fault-peak estimate | 1.7994 A |
| Minimum injected FB ripple | 21.92 mV |
| Maximum injected FB ripple | 64.35 mV |
| Output envelope using triangular-ramp valley approximation | 11.466–12.514 V |

These bounds close the stated static calculation under its assumptions. They do not prove the switching-frequency bounds, hot inductance, ramp shape, transient response, output-capacitance DC-bias behavior, full-load startup or thermal performance. The 100 ns delay and 2.7 A saturation figures are not guaranteed worst-case fault bounds. Full-load startup may enter current limiting; no start-up time is promised. Validate it with the actual total load before release.

The manufacturer land has two 5.4 x 2.9 mm pads with 7.0 mm inner gap (9.9 mm centers), rotated 90 degrees in the local footprint; 12 +/-0.5 mm body and 10 mm maximum height. Native pcbnew updates L1 geometry/fields, preserving footprint/pad UUIDs, position, all net identities and other footprint geometry; support-part values/fields follow the same authorized ECO. A core keepout prevents vias, traces and pours under the central body; the original recommendation prohibits vias and sensitive traces underneath. C30's visible reference moves 2 mm left to avoid the enlarged L1 silk. [Footprint review](l1_footprint_review_2026-10-18.json).

The current BOM and schematic require the exact primary parts. No unverified old alternative is promoted. L1 and R21 local distributor codes are left empty rather than invented; procurement remains open.

## Verification evidence

See [calculation JSON](aux_power_calculation_2026-10-18.json) and [native acceptance](aux_power_native_2026-10-18.json). Fresh exports compare every named net and every physical pin; all net memberships remain identical, and only the five authorized component identities change. The completed final native run reports both ERCs 0 errors / 0 warnings / 0 exclusions; exact PCB parity PASS; DRC FAIL with 0 errors / 0 warnings / 0 exclusions, 499 unconnected and 0 schematic parity. Source hashes are unchanged during the run. The main suite ran 180 tests: 166 passed /14 explicit skips; native geometry 39/39 passed (fixtures/retained board, not new copper). [Fresh ERC](native_1a_erc_2026-10-18.json), [fresh DRC](native_1a_drc_2026-10-18.json).

34 missing wire-end T junctions were added without moving or removing any wire/pin. Exact 181-component /162-net /672-pin connectivity before/after is preserved. The new opt-in generic check rejects missing T junctions and preserves unjoined crossing wires. These visible-native-object additions improve drawing hygiene; junctions alone did not resolve the GUI save problem; the explicit-width repair below does.

All 11 exported pages were reviewed. All252 native junctions explicitly use0.635 mm dots so local branches remain visible in native exports; positions, UUIDs and all pin memberships are unchanged. The phase-W group has moved left by 100 mil, retaining native wiring and every physical pin/net membership, to clear the right drawing border. [Audit record](../.pcba-workflow/schematic-visual-audit.json), [12 V crop](aux_12v_dense_2026-10-18.png), [input bank crop](input_bank_dense_2026-10-18.png), [gate sheet](gate_margin_2026-10-18.png), [PCB placement](pcb_power_eco_2026-10-18.png).

GUI save stability is now PASS. The original implicit-zero-width wires reproduced 162 ->307 nets after a full GUI save; a three-capacitor subset reproduced2 ->5. Explicit positive wire width makes the same capacitor subset stable. All1068 implicit-zero wire strokes now explicitly retain the original6 mil (0.1524 mm) default width; object UUIDs, pins and named nets are unchanged. The final full11-page copy was opened and saved with native KiCad10.0.3, then re-exported:181 components /162 nets /672 physical-pin memberships compare exactly, including component identities. [Final before](gui_stable_before_2026-10-18.json) /[final after](gui_stable_after_2026-10-18.json). The causal implementation detail inside KiCad has not been proven; the controlled width-only repair and successful native roundtrip are the evidence. Old failed snapshots remain diagnostic history and were not promoted. The opt-in source check rejects implicit widths; four negative/positive regressions cover it.

## Required physical acceptance

At 24 V and 48 V, measure continuous total 1 A operation at 40 C ambient and the actual cooling condition, loaded output voltage, switching-frequency range, local regulator/inductor temperatures and startup. Require the stated 50 K rise target and all component junction/case limits; a datasheet JEDEC thetaJA number is not proof for this board. Then test load steps, short-circuit peaks and recovery, output ripple, 5.1 V validity, and gate-off behavior. Complete routing and native DRC 0 violations / 0 unconnected / 0 parity before manufacturing review.

## Sources

- [TI LM5164 Rev.D](https://www.ti.com/lit/ds/symlink/lm5164.pdf), pp5–6 peak limits; pp10–13 ripple and current-limit behavior; pp17–21 equations and selection.
- [TI schematic review](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1568691/lm5164-lm5164ddar-schematics-review), manufacturer recommendation to increase inductance near 1 A.
- [Wurth 7447709151 Rev003.001](https://www.we-online.com/components/products/datasheet/7447709151.pdf), pp1–2 ratings/land. Latest text was read; the original vendor drawing was visually checked using a Rev002.008 distributor mirror with matching land dimensions. Direct OEM download returned403.
- [Yageo RT series](https://yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L), ordering/tolerance/TCR; [49.9k exact primary](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD0749K9L).
- [Murata OEM part document](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM1885C1H332JA01-01A.pdf), indexed OEM title: 3300pF, C0G, 50 V, 0603; direct fetch returned403. OEM catalog copy lists the exact model. Procurement confirmation remains required.
