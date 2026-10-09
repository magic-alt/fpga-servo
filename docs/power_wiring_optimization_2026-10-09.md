# Power and ground presentation optimization

Based on the latest `origin/main`, commit `391dd90`, on topic branch
`fix/ocp-latch-industrial-review`. Existing untracked user files were preserved.

The native KiCad 10 hierarchy remains authoritative. The eight pages were
reviewed in full, with enlarged reviews of the interface power pins, regulators,
current amplifiers, ADC supplies, gate-driver supply, phase-U bootstrap/drain,
encoder receiver, clear filter, supervisors and buffer ports.

## Changes

- Removed seven isolated power-port/graphic pairs from the gate/inverter and
  current/ADC page headers; moved the ports onto visible circuit wiring.
- Moved all nine OCP hierarchy ports from the separate bottom legend to their
  actual circuit nodes. Added an explicit junction at the PWR_READY branch.
- Moved the AX7010 VIO power flag onto the connector supply wire.
- Added 54 native passive power/ground graphics at real local circuit nodes;
  retained the net-naming labels. These graphics are presentation symbols,
  not additional electrical power drivers.
- Made supply/ground labels horizontal, separated adjacent connector ground and
  VIO graphics, moved the C93 fields away from signal ports, and corrected
  page-edge text and the system sheet/title-block clearance.
- Added `tools/check_power_wiring.py` to both CI workflows. It deliberately
  ignores same-name label links and requires every power graphic, power flag
  and child hierarchy port to reach a real component pin by visible wiring.
  It detects the original isolated groups before the repair.

## Verification

KiCad XML exports were compared with the skill's exact connectivity comparator:
**159 system components / 180 nets / 648 pin memberships**, unchanged.
The PCB export independently contains **157 board components / 179 nets**;
external F1 and J6 remain outside PCB placement.

Final ERC: **0 errors / 0 warnings / 0 exclusions**. The inherited ignored-check
list is unchanged. No ERC severities or exclusions were modified.

The five repository source checks, new visible power-wiring check, native
netlist safety check, OCP digital behavior check (531 scenarios), and 11 PCB
checker regression tests passed. BOM regeneration produced no content changes.

PCB SHA-256 remains
`581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`.
The PCB, footprints, physical pin assignments and XDC were not changed.

Review artifacts are under `artifacts/power_wiring_review/`: `before.xml`,
`final.xml`, `before_erc.json`, `final_erc.json`, `final.pdf`, `final_1.png`
through `final_8.png`, and `crop_*.png`. The machine-readable current visual
audit is `.pcba-workflow/schematic-visual-audit.json`.

This completes the schematic wiring/presentation repair. It does not close
the existing PCB synchronization/routing, footprint qualification, power-energy
or bench-timing gates in `docs/release_gates.md`; no PCB DRC was rerun because
the board bytes are unchanged.

## PR review evidence

[Final eight-page schematic PDF](reviews/power_wiring_2026-10-09/final.pdf),
[gate/inverter page](reviews/power_wiring_2026-10-09/gate_inverter.png), and
[OCP latch page](reviews/power_wiring_2026-10-09/ocp_latch.png) are included in Git.
The same directory contains the baseline/final XML netlists, ERC reports,
regression output and original failing power-wiring check for reproduction.

## Inherited CI blocker

Fresh PCB parity still fails on the unchanged board: extra board-mounted F1
and J3.1 on VIN_RAW instead of VIN_FUSED. PCB constraints pass. These are the
existing deferred synchronization findings in `docs/release_gates.md`; exact
schematic net equivalence and unchanged PCB bytes preserve this baseline.
The existing kicad-erc workflow runs PCB parity before ERC, so its job remains
expected to fail at that gate. Native ERC was run independently and is clean.
See [fresh parity report](reviews/power_wiring_2026-10-09/pcb_parity.json).
