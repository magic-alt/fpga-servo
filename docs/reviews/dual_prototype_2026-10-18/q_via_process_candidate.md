# MOSFET thermal via manufacturing candidate

**Process candidate only; manufacturer acceptance, final CAM binding and physical qualification OPEN.** The parent selected retention of existing critical copper/vias with explicit IPC-4761 Type VII nonconductive epoxy fill, planarization and copper capping. A KiCad tent flag does not demonstrate a sealed via when another pad's mask opening exposes that hole. No PCB source, purchase, upload or manufacturer message was performed by this review.

## Manufacturer guidance and selected process

[Infineon Discrete Leadless Assembly Rev7, 2020-12-18](https://www.infineon.com/assets/row/public/packages/73/package_download/infineon-board-assembly-recommendations-discrete-leadless-package-en.pdf?fileId=db3a30433e30e4bf013e368e34f51779), pp11–14, discusses .2–.5mm holes and1.0–1.2mm initial pitch. Its options include stencil segmentation with holes below aperture beams, planar epoxy fill plus overplating, or nearby masked vias where a direct thermal path is unnecessary. Opposite-side-only tenting can worsen voiding. Its usual drain printing range is50–65%, with120–150µm stencils; application experiments remain necessary. The chosen flat filled/capped process follows its assembly approach while preserving critical geometry. It is not a MOSFET thermal qualification.

[JLC's public via filling guide](https://jlcpcb.com/blog/via-filling-guide), retrieved2026-10-19, describes Type VII fill/cap, supports epoxy-filled/capped holes up to.5mm, charges POFV on four layers, and treats conductive copper-epoxy as a separate more expensive option. The selected nonconductive process receives **zero extra electrical or thermal copper credit**. No numerical fee was published or quoted here. JLC's [capability table](https://jlcpcb.com/capabilities/pcb-capabilities) separately lists epoxy fill and capping; final material/diameter/stackup/flatness acceptance must be obtained for the actual order. The .5mm holes are at the guide's stated boundary, not below it.

Both official documents and the JLC HTML snapshot were downloaded with URL, SHA-256 and byte count in `artifacts/dual-servo/q-via-review/downloads.json`. Infineon Rev7 SHA-256 `4cef5eb32b11c7c1035c5db66610fc694e9a1244aae2b413369905cd93832eec`; JLC guide snapshot SHA-256 `7689bdf744f194b930973ff9848e93ebf9dc0d58bb85153c6d5a2a5f268ccf60`. The older2012 SON note was retained as historical corroboration; it is not substituted for Rev7.

## Actual process-snapshot inventory

The interim board is immutable `artifacts/dual-servo/ad-analog/frozen-20261019-0152/ax7010_servo_ad7606c.kicad_pcb`, SHA-256 `28e016515b427868da1c5a89aa250e3fdf9a3ad77b467725075f6b6241e93c76`. **These counts must be regenerated from the final adopted boards.** Neither current source PCB was used as a completed manufacturing input.

`artifacts/dual-servo/q-via-review/AD0152/vip_inventory.json` and `Q_drain_vip_drill_selection.csv` contain actual via UUID, reference, XY, net, drill, annulus, distance to mask/paste, through-layer pair, native layer connectivity and local refilled-zone polygon contacts. The board was refilled only in memory and its input hash rechecked unchanged. Zone contacts require actual same-net filled polygon intersection near the annulus; a shared net name alone is not reported as a plane contact. This snapshot has no additional mask graphics outside pad apertures; the inventory refuses unsupported mask graphics rather than silently omitting them.

| Interim0152 selection | Actual count |
|---|---:|
| All through vias |437|
| .3mm drill |274|
| .4mm drill |118|
| .5mm drill |45|
| Via hole disk intersects any native pad mask opening, including THT |112|
| Q-drain hole/mask intersections |42|
| Q1 / Q3 / Q5 drain mask intersections |0 each|
| Q2 / Q4 / Q6 drain mask intersections |6 each, .5mm drill|
| Q7 / Q8 drain mask intersections |12 each, .4mm drill|

Selection uses **hole circle versus actual F/B.Mask pad-aperture union**, including boundary overlap. Merely testing the hole center would miss three vias per Q2/Q4/Q6. All Q-drain selected holes have zero mask separation because they actually intersect the exposed union; inventory also records annulus/paste and hole/paste distances. `test_aperture_intersection.py` passed three native regressions: an outside center with overlapping hole is selected; a truly separated hole is excluded; changing the via to tented leaves the conflicting pad-mask union present.

A final drawing may either identify precisely the validated UUID/XY hole table or select a fabricator-accepted full-board filled/capped process for every applicable via. Final data must resolve all112 interim pad-mask intersections, not only the42 Q-drain subset, before an ordinary-hole exception is asserted. Process scope must be explicit; this report does not infer that a paid global option has already been ordered.

## Paste and barrel reference budget

The native Q7 polygon unions in the0152 board give drain copper22.492515mm² and drain stencil apertures12.405031mm², including drain lead extensions and twelve internal paste windows. This is55.1518% area and1.550629mm³ printed paste for a.125mm stencil. The main central drain rectangle alone has twelve.9×.9 windows,9.72/21.15=45.96%; that partial ratio should not be confused with the full drain union. Final stencil thickness/transfer efficiency and joint inspection remain assembly decisions.

![Actual Q7 process geometry sketch](../../../artifacts/dual-servo/q-via-review/q7-pofv-process-comparison.png)

The sketch uses immutable0113 Q7 geometry; final hole selection uses the separately hashed0152 inventory. It illustrates a process change, not a modified PCB or measured filled structure. Twelve open.4mm holes through1.614mm have2.433855mm³ geometric barrel capacity, exceeding the1.550629mm³ paste print volume. This is a capacity comparison, not a prediction that all holes fill with solder. Filled/capped processing removes that open sink; it does not guarantee low joint voiding.

Only plated copper is credited. `barrel_reference_budget.json` is reproducible with `calculate_barrel_reference.py`; it uses explicit **assumed** radial barrel Cu20µm, laminate1.614mm and Cu resistivity1.724×10⁻⁸Ωm. These are reference inputs, not a guaranteed JLC minimum plating contract.

| Reference geometry | Cu barrel section | Single-via R at20°C | Parallel-array R at20°C | Cu-only vertical thermal resistance of array |
|---|---:|---:|---:|---:|
| .4mm finished hole,12vias |.026389mm²|1.0544mΩ|.08787mΩ|12.742K/W|
| .5mm finished hole,6vias |.032673mm²|.8516mΩ|.14194mΩ|20.582K/W|

The calculation is `A=π((d/2+t)²−(d/2)²)`, `R=ρL/A`; parallel idealization excludes spreading, caps, entry necks, unequal current, contact resistance and temperature rise. Thermal values exclude lateral spreading, package/joint and ambient paths. A manufacturer minimum barrel thickness and its processing losses must be bound before using these numbers in a final current/thermal budget. Nonconductive resin is not treated as copper or as an added high-conductivity thermal path.

## Drawing/order and verification requirements

Proposed process note: “Selected through vias: IPC-4761 Type VII, full nonconductive epoxy resin fill, cured and planarized, copper capped and finish plated on both ends. Four-layer POFV paid process candidate. No exposed holes, gas-trapping cavities or partial plug accepted as this process. Proposed finished pad dimple/protrusion≤25µm, subject to written fabricator agreement. Preserve separately specified outer2oz/inner1oz actual stackup; state minimum barrel and cap plating after processing. Exact selection in final hash-bound hole table.”

The25µm value is a proposed flatness acceptance target, not measured or accepted by the manufacturer. Final contract must resolve .5mm boundary holes, finish, fill completeness/void criteria, planarization, barrel/cap minima and inspection coupons. CAM must cross-check selected drill coordinates, F/B mask and paste unions, pad connectivity, fills and source/output hashes. Assembly SPI/AXI, reflow/joint quality and full electrical/thermal qualification remain OPEN.

Alternative unfilled methods require a new reviewed layout and assembly process: split mask/paste into windows with masked via islands and sufficient stencil beams, or move vias beside the solder land into solid connected copper. Either option changes solder area/heat spreading and may affect critical current or switching geometry. They were not applied or qualified. The selected Type VII route avoids asserting that a mask flag or an unverified via relocation preserves the existing thermal design.

## Final adopted board inventory — 2026-10-19

The interim0152 and provisional729dea/a4b815 selections above are historical. The final adopted AD board `dc0fb0a39529daa627db700bc2f53dd435f776633b9bd93aa8b1f0053b5f2134` has **511 electrical through vias +83 component holes =594 PTH**. The final ADS board `e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226` has **468 vias +83 component holes =551 PTH**. Both have zero NPTH; the83 component holes include four plated M3 mounting holes. All H1–H4 identities/positions/drills/plating match the original preserved board exactly.

Fresh native UUID/XY/drill/net inventories, **all-electrical-vias-POFV-selection.csv**, three-page POFV location PDFs and individual image hashes are in `artifacts/dual-servo/final-power-dual-20261019-r2/{ad7606c,ads8588s}/`. Ordinary component holes are explicitly not selected for filling. This all-via list is distinct from the subset intersecting mask/paste apertures; it is the process selection for the proposed paid four-layer Type VII nonconductive epoxy-filled/planarized/copper-capped process. The static map does not establish manufacturer acceptance, minimum barrel/cap plating, voiding, thermal sharing or assembly qualification. Final package copies and controlled-hole notes are source-bound separately.
