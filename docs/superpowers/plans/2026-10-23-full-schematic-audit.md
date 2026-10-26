# Full schematic audit and repair plan

**Goal:** Review both retained servo variants against native connectivity and OEM requirements; repair confirmed defects without inventing hardware qualification.

**Scope:** The user authorized audit and repair of both schematic projects. Preserve original untracked work, existing ADC selections, external AD DC-link decision, mechanical features and manufacturing gates. Work on `codex/full-schematic-audit-20261023`.

- [x] Snapshot all configured design inputs and export fresh native baseline evidence.
- [x] Review power, inverter, sense/OCP, ADC, encoder, FPGA interface and supervisor sources; independently review public manufacturer documents.
- [x] Correct U1's obsolete library identity and logical pin names to DRV8300D PW20; retain physical pin numbers, geometry, values, footprints and wiring. Add a manufacturer pin-map guard and negative tests.
- [x] Correct R92 misleading precision description and stale current architecture descriptions; keep actual selected MPN and electrical budget.
- [x] Export fresh XML and verify the only component identity change is U1's intended symbol rename; all net names and physical memberships remain exact.
- [x] Run both schematic checks, native ERC and strict release/PCB checks; render all pages and inspect changed areas. Run applicable regressions with explicit skipped/missing dependency boundaries.
- [x] Obtain independent review of repairs and document remaining design/performance/manufacturing evidence gaps without fabricated signoff.

**Acceptance:** Zero unexpected connectivity/geometry changes; no severity reductions or exclusions. Actual dynamic protection, RTL/STA, current/thermal and manufacturer acceptance remain separate gates.
