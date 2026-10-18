# Historical unsynchronized PCB regression

This directory preserves the ADS8588S legacy PCB, native project and custom
rules from `b0172a2f65902c7281cf4a8454f192dc791a9ef9`. They were copied from the
verified starting snapshot under `artifacts/dual-servo/baseline/ads8588s/`;
their normalized text was compared with that Git commit before copying.
`provenance.json` records the exact copied-file SHA-256 values.

`board.net` is the original fresh KiCad netlist from
`artifacts/plan-audit/ads8588s/20261018T144449Z-6eoy6y27/`. The original
`pcb_ci_baseline.json` was copied without changing its hashes, known blockers,
parity details or constraints. Its text hashes normalize line endings; the
provenance hashes preserve the copied bytes.

These are immutable historical regression inputs, not the current PCB and not
fabrication evidence. The archived design remains blocked. Historical tests
must compare these files to the unchanged expected blockers. Active PCB,
prototype and release checks operate on the current design and must reject
the same faults rather than accept them as historical exceptions.
