# Schematic Humanizer reference validation

2026-10-09. This extends the installed upstream Skill with a reference rather than a second competing workflow.

A read-only subagent first answered three retrieval/application scenarios without the new reference: repeated inverter/sense stages; overlapping hierarchy labels/title-block notes; Git badges and missing page numbers. The baseline supplied reasonable generic guidance but lacked a concrete spacing recipe and could not identify the KiCad-specific badges or the source-instance/PDF diagnostic sequence. It explicitly reported those unknowns. It did not demonstrate unsafe editing.

After reading the Skill and new reference, the agent produced these actionable decisions:

- Choose phase/channel spacing from the widest rendered block plus a routing corridor; keep connection anchors on 1.27 mm and inspect transformed pins.
- Trace the native wire graph before deleting same-name labels; nearby stubs can be distinct wire islands. Require exact component identities, named nets and physical pin memberships after changes.
- Reserve the full rendered extent of notes rather than their anchors; separate source page instances, PDF page IDs and uninspected editor visibility.
- Identify the green check/red hollow circle specifically as KiCad 10 Project Manager Git status, independent of ERC.

The follow-up found no conflation of proximity with electrical equivalence, PDF success with a fixed GUI preference, or Git cleanliness with ERC success. This is a focused reference retrieval/application check, not a broad benchmark or independent full hardware-design approval.

Local application supplied a concrete counterexample: removing a visually redundant parent GND label split the exported net. The comparison failed (181 nets, added sheet-local GND); adding the explicit intended same-net wire restored exact 159-component / 180-net / 648-membership equivalence. The rejected intermediate drawing was not promoted. The final graph and unchanged PCB hash are recorded in `.pcba-workflow/schematic-presentation-proof.json`.

`python -X utf8 .../skill-creator/scripts/quick_validate.py .agents/skills/schematic-humanizer` passed. UTF-8 was required because the Windows default GBK decoder cannot read the upstream multilingual Markdown. The bundled comparison script ran against fresh before/final native XML exports and passed.
