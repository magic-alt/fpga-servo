# AD7606C continuation baseline — 2026-10-18

Local branch: `feat/ad7606c-hardware-completion`; clean starting HEAD `2c9d17f`.

| Commit | Delivered change |
| --- | --- |
| `7df0087` | Hardware-only repository; interface constraints moved under hardware projects; root fpga directory removed. |
| `bcd0b03` | Native synchronized four-layer placement candidate; approved outline, holes and connector anchors retained. |
| `2c9d17f` | 12 V total continuous 1 A static-corner ECO, exact BOM/inductor land, explicit visible junctions and GUI-save stability repair. |

Baseline native evidence: 181 components, 162 nets, 672 physical-pin memberships; both native ERCs 0 errors/warnings/exclusions; PCB parity PASS. Native DRC FAIL: 499 unconnected, 0 other violations, 0 schematic parity. Full regression 180 tests:166 passed/14 explicit skips; native geometry39/39 (tool fixtures, not new-board copper acceptance). Final native GUI save preserves the exact graph. See `aux_power_native_2026-10-18.json` and `aux_power_review_2026-10-18.md`.

Continue in the existing topic worktree. First review actual package/pad geometry, netclass names, critical-loop placement and the 1 A regulator layout. Retain mechanical anchors and all source connectivity. Route DC-link/switching paths, gate/bootstrap, Kelvin/OCP, then ADC/encoder/logic; perform fresh native DRC and parity after each stage. Do not autoroute high-current, high-dv/dt or safety paths. Do not change severities, add exclusions or disconnect required pins to achieve zero counts.

Physical acceptance remains OPEN: 24 V/48 V loaded startup, continuous total1 A at40 C with actual cooling, temperature rise, frequency/ripple, load steps, short circuit/recovery and validity/gate-off behavior. Simulated or static evidence must stay distinct from actual bench measurements. No fabrication release until current-board ERC/DRC/parity and engineering gates close.
