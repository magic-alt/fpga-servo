# Manufacturer land-pattern DRC repair - 2026-10-10

Development baseline only. DRC closure and fabrication release remain OPEN.

Online layout tools reviewed: [blwfish/kicad-mcp](https://github.com/blwfish/kicad-mcp), [Freerouting](https://github.com/freerouting/freerouting). The installed KiCad MCP reproduced the original 97 errors and the repaired 68 errors. Native KiCad 10.0.3 performed the controlled footprint migration and full parity checks. External routers were not installed or used to claim completed routing.

## Physical repair

U8/U9/U10/U20/U26 now use `fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm`. TI DCU0008A drawing 4225266/A specifies example copper lands 0.85 x 0.30mm, 0.5mm pitch, row centers 3.1mm apart and R0.05mm corners. NSMD mask margin is +0.05mm; paste apertures match copper. The drawing's 0.125mm stencil thickness still requires assembly-process validation. Sources: [SN74LVC2G08 Rev.N](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf), [SN74LVC1G74 Rev.G](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf), [SN74LVC3G17 Rev.F](https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf).

Previous generic copper lands were 1.25 x 0.35mm with row centers 2.8mm apart. Migration preserves board positions, rotations, pad UUIDs and nets. Only five schematic footprint properties and matching BOM entries changed. Before/after XML comparison passes for 164 components, 170 nets and 658 physical-pin memberships after explicitly accounting for the five footprint identity changes.

`tools/check_vendor_lands.py` failed on the old geometry and passes on the repaired board. `check_design.py` invokes this regression check. It checks copper dimensions and identities, not complete package procurement or assembly qualification.

## Verification

- Native DRC: **68 clearance errors /447 unconnected /0 parity issues**, previously97/447/0. MCP independently confirms68 errors and0 warnings. Its headline excludes unconnected items; native results remain the acceptance evidence.
- No clearance/severity settings or exclusions changed. Working project settings are byte-identical to the pre-repair snapshot, preserving the user's existing uncommitted changes.
- ERC: 0 errors /0 warnings /0 exclusions. All six project checks pass, plus vendor lands, fresh-netlist safety/OCP, PCB constraints/parity and 11 PCB regression tests.
- Schematic and board PDFs exported; eight schematic sheets and front-board view inspected. Schematic geometry unchanged.
- [Source hashes and counts](reviews/drc_vendor_lands_2026-10-10/summary.json), [raw DRC](reviews/drc_vendor_lands_2026-10-10/drc.json), [check results](reviews/drc_vendor_lands_2026-10-10/python_checks.json).

## Remaining work

The remaining 68 violations involve existing package pad spacing versus net-class rules, including ADC 0.20mm land gaps versus ANALOG0.25mm and power-connected package gaps versus POWER0.80mm. Moving the components cannot increase internal pad spacing. The pending engineering choice is to retain verified manufacturer lands with narrowly scoped same-instance pad clearance rules, or retain original spacing everywhere and select different devices/packages. Neither rule changes nor substitutions have been applied pending that choice.

447 connections still require routing. High-current copper, exact shunt/connector footprints and thermal evidence remain unfinished. S01 dynamic qualification, S09 sequencing and rapid VA5 droop/gate-off qualification remain OPEN. No brake circuit is added, following the latest user instruction. No release blockers are waived.
