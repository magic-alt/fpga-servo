# fpga-servo

FPGA-based single-axis PMSM/BLDC servo-drive daughterboard for the ALINX AX7010 / Zynq-7000 (2022 board, active PL connector J10).

> **Design / manufacturing hold — 2026-10-11.** The latest `main` incorporates [PR #15](https://github.com/magic-alt/fpga-servo/pull/15), which changed the **schematic, BOM and part selection only**. The working PCB was deliberately not synchronized with the final positive bus-OCP circuit (U5/RSH4/U15). The zero-DRC result from an older PCB revision is **not** valid for the current schematic. There is no fabrication release, no certified OCP fault-off delay, and no approval for full-power operation.

## Rev.A-P prototype design basis

| Item | Current design (not yet qualified) |
| --- | --- |
| Input / switching | DC 24–48 V; 20 kHz six-command PWM from AX7010 PL |
| Current / cooling | 10 A RMS continuous phase; 20 A peak for 30 s (waveform/repetition still to be defined); 40 °C max ambient; forced air |
| Inverter | Six 100 V BSC040N10NS5 MOSFETs; **non-inverting DRV8300DPWR** with internal bootstrap diodes |
| Current sensing | Three motor-phase 5 mΩ / 3 W inline shunts with INA240A1DR (20 V/V); separate positive DC-bus 2 mΩ / 3 W shunt with INA240A1DR |
| Hardware OCP | LM393LVDDFR positive-bus comparator, nominal +25 A trip; hardware fault latch and six gated PWM inputs; **not reverse-current protection or a guaranteed maximum fault current** |
| ADC | ADS8588S, eight simultaneous 16-bit channels; three phase currents, VBUS, two board-mounted NTC inputs |
| Encoder | Differential 5 V ABZ interface using AM26LV32E; cable termination and power fault behavior still to qualify |
| Auxiliary power | LM5164 DC bus → 12 V; TPS62901 12 V → nominal 5.1 V; VIO 3.3 V from AX7010 |
| Power input | On-board 0456025.ER 25 A fuse, LM74502 + MOSFET polarity-protection stage (source fault-current coordination unqualified) |
| PCB intent | Two-layer, candidate 2 oz copper; real stack-up, thermals, clearances and mechanical land patterns require manufacturer approval |

The driver is the **DRV8300D** non-inverting PW20 variant, **not** the older FD6288T or the DRV8300DI. The current-sense amplifiers are **INA240A1**, not INA241A2. The unused AX7010 J2 connector and old phase-window OCP have been removed. The LM74502 input circuit does not establish reverse regeneration blocking; there is no fitted brake or verified sink for regenerated motor energy.

## Review, cost and qualification

- [Rev.A simplified architecture and production review](docs/rev_a_simplified_design_production_review_2026-10-11.md): retain/replace/remove decisions, fault-coverage boundaries, cost tradeoffs, ECO sequence and G0–G5 release requirements.
- [68-group Rev.A sourcing-cost/ECO matrix](hardware/reva_cost_eco_2026-10-11.csv): selected manufacturer part numbers, LCSC codes, extended cost, production concerns and priorities. Based on **2026-10-10 snapshot**, approximately **CNY 164.67 per board** for 148 purchased fitted references, excluding PCB/assembly/tax/shipping. Supplier stock and prices must be refreshed before any order.
- [Current sourcing selection](docs/lcsc_sourcing_review_2026-10-10.md), [architecture](docs/architecture.md), [design calculations](docs/design_calculations.md), [fabrication gates](docs/release_gates.md), and [hardware handoff](hardware/README.md).

**Release blockers:** re-synchronize PCB and physical-pin mapping against current schematic; close any new ERC/DRC/unconnected/parity findings without waived checks; qualify L1 inductor current/saturation/thermal data, shunts and connector lands, gate-driver and fault-to-VGS-off worst-case timing, supply sequencing/ADC validity, 10 A thermal soak and the upstream DC source's reverse-energy handling.

## Repository layout

- `hardware/`: KiCad 10 native eight-sheet schematic, unreleased PCB baseline, project-local symbol/footprint libraries, BOM, and procurement candidates.
- `fpga/`: AX7010 XDC constraints for the proposed PL connector mapping (not evidence of validated HDL functionality).
- `docs/`: architecture, sizing calculations, schematic/PCB reviews, procurement evidence and release checklist.
- `tools/`: repository checks, layout review, native KiCad audit helpers and qualification scripts.
- `.github/workflows/`: static/native review workflows. **Passing CI/ERC alone is not a manufacturing or electrical safety release.**

See [AGENTS.md](AGENTS.md) before making an electrical edit. Implement all hardware ECOs on a separate branch with fresh native KiCad netlist/physical-pin comparison, ERC, DRC and bench qualification; do not replace the current board based on a document-only review.
