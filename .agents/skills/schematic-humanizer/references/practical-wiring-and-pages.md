# Practical wiring and page review

## Repeated stages

Use one phase/channel as a visual template, then repeat its relative geometry.
For a three-phase inverter, use equal-pitch U/V/W columns; for current sensing,
use equal-pitch amplifier/filter rows. Preserve the actual force/sense pin mapping.
Align corresponding MOSFETs, gate resistors, gate-source pulls, bootstrap parts,
and shunts. Align INA outputs, series resistors, filter capacitors and bypass parts.
Keep high-current flow, gate drive, Kelvin sense and logic readable as separate paths.

Choose the pitch from the widest rendered block, including references, values,
pin names and labels, plus a free routing corridor. Do not use a fixed pitch that
forces the last phase into the page border. In KiCad, connection anchors must
stay on the project's grid (50 mil = 1.27 mm in this project); text can use a
smaller positioning grid. Check actual transformed pin coordinates after rotation.

Connect bootstrap, gate-resistor/pull-down and local output-filter loops with
native wires. Match labels for distant driver outputs or cross-block ADC signals
when a direct wire would cross a symbol or require a large loop. Wire length is
not the deciding threshold: inspect traceability, crossings and whitespace.
Keep the phase ordering identical at driver, power stage, sensing and connector.

## Labels and connection proof

On parent sheet symbols, place net text outside the symbol: right-justified at
left-facing port stubs and left-justified at right-facing stubs. Keep horizontal
text readable; vertical labels need clearance from component fields. Label
anchors must remain on a proven wire or pin, rather than merely near it.

Before removing a same-name label, trace the native wire graph. Two nearby stub
ends can be connected only by their labels, even when the page looks continuous.
A nearby hierarchical label can also name another wire island. Proximity and a
shared name do not prove that removing one preserves connectivity. Either retain
both and separate their text, or visibly join proven same-net stubs and then
remove the redundant label. Do not bridge unrelated pins or crossings.

A useful counterexample is two GND stubs with a short visual gap. Removing one
label can create a sheet-local GND net. Detect it by exact named-net and physical
ref/pin comparison, restore the original graph, then add the intended visible
wire and compare again. ERC alone may miss a plausible split ground net.

For KiCad, export both snapshots using the same version:

```powershell
kicad-cli sch export netlist --format kicadxml --output before.xml root.kicad_sch
# Apply presentation edits to the authoritative source.
kicad-cli sch export netlist --format kicadxml --output after.xml root.kicad_sch
python scripts/compare_connectivity.py before.xml after.xml
```

Invoke the comparison script relative to this Skill folder or use its full path.
Require exact component identities, net names and physical pin memberships.
A mismatch blocks promotion: correct the edit and repeat the export, comparison,
ERC and render. Do not normalize away a newly split net or renamed net to pass.

## Full-page geometry

Reserve the actual lower-right drawing-sheet title-block rectangle. Checking
only a note's anchor is insufficient: its rendered width can reach that rectangle.
Shorten local prose, wrap it deliberately or move detailed rationale to a companion
document. Keep safety conditions and qualifications intact. After changing any
note, inspect its full text extent and nearby wires again.

Render every hierarchical page from the root, plus enlarged crops of connectors,
IC pin banks, gate/boot loops, divider/filter nodes, power-good and reset logic.
Compare page edges, local wire junctions and note extents at readable resolution.
Keep PCB bytes unchanged during a schematic presentation-only task.

## Page numbers and Git badges

First identify the interface reporting the issue. In KiCad 10 Project Manager,
a green check means a tracked file is unchanged; a red hollow circle means
uncommitted changes. Confirm with `git status --short`. These are Git badges,
not ERC, connectivity or manufacturing approval. Untracked files have a separate
status; committed files can still contain electrical errors.

For missing page numbers:

1. Open the project root schematic, then navigate children in the hierarchy.
2. Inspect the root `sheet_instances` page and each child's `instances/project/path`
   page. Enumerate actual children; check count, uniqueness and intended ordering.
3. Export the whole hierarchy to PDF with drawing-sheet border/title block enabled.
   Check both the PDF page count and each rendered title-block `Id: n/N`.
4. If the PDF and source are correct but the editor omits them, inspect the
   Appearance panel's Drawing Sheet visibility, hierarchy panel visibility,
   zoom and current root/context. Do not rewrite page instances on that evidence.
5. If source numbers are missing/duplicated, repair them in the hierarchy navigator
   (Edit page number) and repeat export. If printing omits the frame/title block,
   enable Plot drawing sheet in the plot dialog.

An explicit `02 / 08` inside each parent sheet box can provide navigation context;
keep it synchronized with stored instances and clear of port names. It supplements
the title-block page ID. Never claim an editor preference was fixed unless the
actual UI was inspected and verified.

Official references:
- KiCad 10 Project Manager Git integration: https://docs.kicad.org/10.0/en/kicad/kicad.html
- KiCad 10 hierarchy, appearance and plotting: https://docs.kicad.org/10.0/en/eeschema/eeschema.html
- TI TIDA-00913 schematic, used for visual grouping rather than copied values: https://www.ti.com/lit/pdf/TIDROJ7
