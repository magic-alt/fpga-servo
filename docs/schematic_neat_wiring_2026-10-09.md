# Gate Driver / Current Sense readability refinement

2026-10-09, branch `fix/ocp-latch-industrial-review`.

Only the geometry of `hardware/gate_inverter.kicad_sch` and
`hardware/current_adc.kicad_sch` was changed in this iteration. The snapshot is
`artifacts/schematic_neat/before/`. Existing work on other sheets was preserved.

## Drawing changes

- Arrange the half bridges W/V/U from left to right to follow the FD6288 output
  grouping. The external phase names and connector physical pin mapping remain
  U/V/W as before.
- Rotate the four-terminal shunts beside their half-bridge paths, allowing the
  high-side source to low-side drain connection to run directly between the
  MOSFETs. Force and Kelvin pin numbers and electrical connections are unchanged.
- Group bootstrap parts above their associated bridges; align the gate resistors
  and move the upper gate-source bias resistors clear of the shunts.
- Move logic bypass capacitors away from PWM input labels. Retain the repeated
  three-channel arrangement and distinct hardware enable block.
- Keep current amplifiers and RC filters in three aligned rows. Move their
  bypass capacitors away from the differential input labels.
- Align ADC reference capacitors with their corresponding pins, with the supply
  bypass bank below them and explicit common ground wiring.
- Use the existing 1.27 mm connection grid, with additional space where the A4
  drawing permits. Fine-pitch IC fanouts retain the necessary closer spacing.

## Measured geometry

Measurements count drawn schematic wires, not PCB tracks. Proper crossings
exclude junctions and wire endpoint contacts.

| Page | Wire segments before / after | Drawn wire length before / after (mm) | Proper crossings before / after |
| --- | --- | --- | --- |
| Gate Driver | 332 / 316 | 4330.70 / 4267.20 | 77 / 59 |
| Current Sense | 351 / 333 | 3957.32 / 3905.25 | 53 / 51 |

The selected drawing balances total distance, crossings and readability; it is
not a proof of the global shortest drawing. Gate Driver degree-two corners
increase from 168 to 177 while crossings decrease; Current Sense corners decrease
from 117 to 113. A perimeter-rail alternative was rejected because it increased
total wire length substantially. Detailed measurements are saved in
`artifacts/schematic_neat/geometry_metrics.json`.

## Verification

- Native schematic, connection grid, A4 layout, connectivity and design checks:
  PASS.
- Fresh native netlist: 157 board components / 179 nets; system BOM: 159 entries.
- Physical-pin net partitions exactly match the pre-edit native netlist.
- Independent wire-only continuity check: Gate Driver 42 nets / Current Sense
  33 nets; all page-local pins on each net are physically connected without
  relying on labels to bridge disconnected islands.
- Component properties, component UUIDs, pin UUIDs and library identifiers are
  unchanged.
- Native KiCad ERC: 0 errors / 0 warnings / 0 exclusions. No severities or
  exclusions were changed.
- Safety connectivity: PASS. OCP digital behavior: 531 scenarios PASS.
- Other schematic pages are byte-identical to this iteration's snapshot.
- PCB unchanged; SHA256:
  `581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`.

The existing hierarchical interfaces are retained. The previously prepared
project-wide global-label migration remains unapplied. This drawing refinement
does not change the outstanding manufacturing and bench gates.

## Review exports

- [Two-page optimized drawing](../artifacts/schematic_neat/Gate_Driver_Current_Sense_optimized.pdf)
- [Full native schematic PDF](../artifacts/schematic_neat/final.pdf)
- Native evidence: `artifacts/schematic_neat/final.net` and
  `artifacts/schematic_neat/final_erc.json`.
