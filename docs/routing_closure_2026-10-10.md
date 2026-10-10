# PCB DRC and connection repair - 2026-10-10

Work in progress. User requested continued repair until DRC and connections are closed. The working board is an unreleased development baseline. Latest adopted stage: **0 DRC violations /64 unconnected /0 schematic parity issues**. Dynamic and manufacturing acceptance remain OPEN.

## Actual repair

- Local TI DCU lands corrected for U8/U9/U10/U20/U26 (previous stage).
- U18 migrated to TI DDF0008A example lands: 1.05 x 0.45mm, 0.65mm pitch, 2.6mm row spacing. U2/U3/U4 migrated to TI D0008A example lands: 1.55 x 0.60mm, 1.27mm pitch, 5.4mm row spacing. Sources: [LM74502](https://www.ti.com/lit/ds/symlink/lm74502.pdf), [INA241A](https://www.ti.com/lit/ds/symlink/ina241a.pdf). Source package drawings, not nominal body sizes, guide these migrations.
- C18/C19 use the complete native 0805 footprint, increasing copper gap above the external POWER0.8mm rule. Values and electrical networks unchanged; exact purchase MPN/voltage/assembly qualification remain release gates. C18 is the floating VCAP capacitor; its differential voltage differs from bus common mode.
- Fourteen exact same-instance pad-to-pad rules handle package internal spacing: Q1..Q8 >=0.60mm; U2/U3/U4 >=0.65mm; U1 >=0.25mm; U6/U18 >=0.20mm. These are engineering constraints for existing package lands, not DRC exclusions. No external trace/via clearance or net-class value was reduced. No severity setting was changed. The preexisting modified project settings file remains byte-identical to the start of this turn.
- Native DSN export, local routing, SES import, controlled geometric completion and repeated native DRC produced actual front/back traces and vias. Existing Kelvin line segments were retained during congestion re-route, but a later independent topology audit found external force-to-sense bridges. Segment retention alone was insufficient; see the correction below. Board outline and H1..H4 positions remain unchanged.
- Freerouting2.5.0 native executable crashed on snapshot serialization before producing a usable result. Official Freerouting1.9.0 Java release is used locally with analytics disabled and single-thread optimization; no cloud routing is used. Its SES import exposed three legacy via diameter/drill issues, corrected using native KiCad before accepting the stage. [Official router](https://github.com/freerouting/freerouting).

## Measured trend

| Stage | DRC violations | Unconnected | Parity |
| --- | ---: | ---: | ---: |
| Start | 68 | 447 | 0 |
| Manufacturer lands and ordinary signals | 0 | 369 | 0 |
| Ground routes | 0 | 237 | 0 |
| Remaining-network three-pass route | 0 | 117 | 0 |
| Congestion re-route | 0 | 102 | 0 |
| Local GND completion | 0 | 91 | 0 |
| Collision-checked same-layer completion | 0 | 86 | 0 |
| Collision-checked layer bridging | 0 | 81 | 0 |
| Fine logical vias | 0 | 78 | 0 |
| Control-area ground plane and constrained re-route | 0 | 70 | 0 |
| Java25 router candidate, width correction and unused-stub cleanup | 0 | 65 | 0 |

[Raw latest DRC](reviews/routing_closure_2026-10-10/working-drc.json). ERC remains0/0; six footprint identity changes preserve all164 components /170 nets /658 physical-pin memberships. Native parity and physical-pad regression pass for162 board components /169 board nets /166 footprints. Intermediate failed candidates remain under artifacts and were not adopted merely to improve counts.

## Open work

Continue residual connections and critical current paths; require fresh native DRC0 and unconnected0 before claiming routing closure. Copper sliver and drilling-clearance failures in intermediate completion candidates were rejected and corrected, not excluded. Package escape candidates with open ends were not promoted. Thermal/current capacity, switching-loop/return review, supplier footprint approval and assembly process approval remain OPEN. S01 dynamic qualification and S09 sequencing remain OPEN; no bench waveforms have been invented. The brake circuit remains cancelled.

The control/ADC front ground-return zone is restricted to x2.5..61mm and y25..96.5mm, outside the switching power stage. Filled copper is saved to the working PCB. A standalone candidate DSN export without its matching project file lost net-class constraints; that failed candidate was rejected (142 clearance errors), restored from the verified stage, and subsequent exports assert POWER3000um/800um and GATE400um before routing. The original project settings remain unchanged.

## Continued repair checkpoint

Freerouting2.5.0 now runs locally on the official Java25 runtime. Its previous candidate was accepted only after correcting undersized neckdowns to the project minimum and removing native-identified unused router stubs in five checked stages; unconnected stayed65 throughout cleanup. No component/pad/network was removed. Native all-severity DRC with refill/save and schematic parity:0 violations /65 unconnected /0 parity. Independent physical parity:162 components /169 nets /166 footprints.

Found the DSN import-state mismatch: (type route) is read as user-fixed by Freerouting. The isolated subsequent candidate makes ordinary signal copper (type normal) while preserving phase/load nets and wide copper. This is a routing-input correction, not a native DRC rule change. Candidate placement and bounded package-escape experiments remain unadopted.


## Kelvin topology correction

Independent copper connectivity review found that same-net routing had joined all six shunt force/sense pairs externally. Native DRC and electrical netlist parity did not detect that topology error. The bridges were removed; native KiCad jumper pad/pin groups now describe the four-terminal shunt internal pairs (1,3) and (2,4). Physical pins, network names and the complete 164-component/170-net/658-membership schematic graph remain unchanged. Fresh native ERC is zero; native filled-board DRC remains 0 violations /65 unconnected /0 parity.

`tools/check_pcb_kelvin.py` now verifies six actual copper clusters, each containing only its shunt sense pad and corresponding INA input. All six pass; the pre-correction board fails all six. Future routing candidates must pass this independent check before adoption. Dynamic qualification remains OPEN.

[Layout rules and open industrial constraints](pcb_layout_rules_2026-10-10.md) distinguishes current net-class settings from unverified thermal, 3W/2H, return-path and manufacturing requirements.


## Local completion and regression checkpoint

A collision-checked local CLEAR_FILT connection and a local GND branch were adopted after removal of two newly duplicated copper primitives. Fresh all-severity native DRC with zone refill/save and schematic parity: **0 violations /64 unconnected /0 parity**. Exact physical parity remains162 components /169 nets /166 footprints. Six native Kelvin clusters pass; four regression tests pass, including six independently injected real force/sense copper bridges and invalid internal-pair metadata. The six project checks and six vendor-land regression tests pass; fresh ERC0 and stable-level OCP531 scenarios pass. These do not establish dynamic or manufacturing qualification.

Further driver-placement/routing candidates remain isolated. Candidate scripts must preserve the matching project file after native SaveBoard: saving an independently loaded candidate may generate default project settings. Router export now explicitly checks that POWER width3000um/clearance800um is present. Six virtual router-only Kelvin nets isolate the dedicated sense copper; SES import must restore the original net names and pass the native copper-cluster checker before any adoption. The working project settings were preserved.


The central-driver isolated router candidate completed12 local passes, but fresh native checks returned30 violations /77 unconnected /0 parity. Its six Kelvin branches passed after restoring virtual net names, proving the routing isolation mechanism; its routing result was rejected. It was not copied to the working board, which remains0/64/0.


## Committed development checkpoint

Fresh verification before the checkpoint commit: six repository checks PASS; vendor-land, physical PCB constraints and six Kelvin branches PASS; 21 related regression tests PASS (6 vendor lands, 4 Kelvin, 11 PCB checks). Fresh native netlist: 162 board components /169 nets; physical parity: 166 footprints including H1..H4, PASS. OCP stable-level regression: 531 scenarios PASS. Native all-severity ERC: 0 violations. Native all-severity PCB DRC with zone refill and schematic parity: 0 violations /64 unconnected /0 parity issues. These 64 remaining connections are not closed; this commit is a development checkpoint, not a routing-complete or manufacturing-approved release. Existing ignored DRC categories remain unchanged.

The checkpoint includes manufacturer land-pattern migrations, bounded internal-pad rules, current routing and ground-return copper, four-terminal shunt internal-group metadata and independent Kelvin topology regressions, matching BOM/schematic footprint assignments, routing tools and review evidence. Dynamic protection, sequencing, thermal/current capacity and manufacturing release gates remain OPEN.
