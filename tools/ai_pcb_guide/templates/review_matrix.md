# PCB Design Release Review Matrix

**Project / Version**: ______  **Commit**: ______  **KiCad Version**: ______

| Gate | Owner | Evidence path/SHA256 | State | Reviewer / Date | Blockers |
|---|---|---|---|---|---|
| G0 Requirements | | | NOT_STARTED | | |
| G1 ERC/netlist/BOM | | | NOT_STARTED | | |
| G2 MPN/Footprints | | | NOT_STARTED | | |
| G3 PCB schematic-parity | | | NOT_STARTED | | |
| G4 DRC/thermal/EMI | | | NOT_STARTED | | |
| G5 Gerber/drill/BOM/assembly | | | NOT_STARTED | | |
| G6 Bring-up/OCP/recovery | | | NOT_STARTED | | |

Allowed `State`: NOT_STARTED, IN_PROGRESS, PARTIAL, PASS, BLOCKED, WAIVED. For WAIVED include owner, risk analysis and approval ID; release blockers cannot be silently waived.

## Evidence Manifest (illustrative)

```json
{
  "commit": "40-character SHA",
  "tool": "kicad-cli",
  "version": "10.x actual value",
  "command": "pcb drc --schematic-parity --refill-zones ...",
  "file": "artifacts/pcb_drc.rpt",
  "sha256": "sha256 of file",
  "result": "FAIL",
  "violations": null,
  "unconnected": null,
  "reviewer": null
}
```

Do not replace `null` with made-up zeros. Always store original reports and identify the commit used to run them.
