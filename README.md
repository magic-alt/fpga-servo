# fpga-servo

FPGA-based single-axis PMSM/BLDC servo-drive daughterboard for the ALINX AX7010 / Zynq-7000 (2022 board, active PL connector J10).

> **Four-layer engineering CAD — 2026-10-19; manufacturing hold.** Both ADC variants now have synchronized schematics and four-layer PCBs, independent BOMs and portable local libraries/models. Current candidates have zero native ERC/DRC violations, unconnected items and schematic-parity differences; eight Kelvin paths, bounded package escapes, free-corner checks and maximum ADC-body digital-copper exclusion pass. These are CAD results. Human engineering reviews and exact material/manufacturing-process acceptance remain open; neither board is approved for fabrication or full-power operation. See the [dual-board review](docs/reviews/dual_prototype_2026-10-18/README.md) and [release gates](docs/release_gates.md).

## 两种 ADC 方案

原方案使用 **ADS8588SIPM**；新方案使用 **AD7606C-16BSTZ**，采用四路 DOUT、电平转换和独立 XDC。AD7606C 的 1 MSPS、0–5 V 高速模式典型相位延迟及读取预算见[选型与迁移规格](docs/adc_high_performance_reselection_2026-10-12.md)和[FPGA 接口草案](hardware/ad7606c_servo/ad7606c_fast_candidate_profile_2026-10-12.json)。这些是器件及接口设计依据，实际闭环带宽仍须由 RTL、时序和整机测量验证。

**当前双方案：** [ADS8588S 原方案](hardware/ads8588s_servo/README.md) 与 [AD7606C 新方案](hardware/ad7606c_servo/README.md) 分目录维护，各有原理图、BOM、XDC 和 PCB。两方案新增独立 DC-link 子页，并修正编码器接收器引脚、栅极电阻和辅助电源；本轮电气 ECO 后的 PCB 同步及整板布线验收尚未闭合。通过[硬件入口](hardware/README.md)选择工程。

## Rev.A-P prototype design basis

| Item | Current design (not yet qualified) |
| --- | --- |
| Input / switching | DC 24–48 V; 20 kHz six-command PWM from AX7010 PL |
| Current / cooling | 10 A RMS continuous phase; 20 A instantaneous phase amplitude for 30 s, balanced sine (14.142 Arms); repetition/cooldown still to be qualified; 40 °C max ambient; forced air |
| Inverter | Six 100 V BSC040N10NS5 MOSFETs; **non-inverting DRV8300DPWR** with internal bootstrap diodes |
| Current sensing | Three motor-phase 5 mΩ / 3 W inline shunts with INA240A1DR (20 V/V); separate positive DC-bus 2 mΩ / 3 W shunt with INA240A1DR |
| Hardware OCP | LM393LVDDFR positive-bus comparator, nominal +25 A trip; hardware fault latch and six gated PWM inputs; **not reverse-current protection or a guaranteed maximum fault current** |
| ADC | Separate ADS8588S / AD7606C-16 projects; eight simultaneous 16-bit channels; three phase currents, VBUS, two board-mounted NTC inputs |
| Encoder | Differential 5 V ABZ interface using AM26LV32E; cable termination and power fault behavior still to qualify |
| Auxiliary power | LM5164 DC bus → 12 V, total continuous 1 A; TPS62901 → nominal 5.1 V, reviewed effective-capacitance budget and external soft start; VIO 3.3 V from AX7010 |
| DC-link / external sink | Ten individually damped 100 µF / 100 V branches; J7 protected-bus sink interface; no onboard brake; fixture qualification open |
| Power input | On-board 0456025.ER 25 A fuse, LM74502 + MOSFET polarity-protection stage (source fault-current coordination unqualified) |
| PCB | Both variants: four layers, 130 × 95 mm; JLC041621-3313 / NP-155F Tg155 candidate, outer 70 µm / inner 30 µm copper; material acceptance, paid Type VII POFV and controlled finished-hole processes remain open |

The driver is the **DRV8300D** non-inverting PW20 variant, **not** the older FD6288T or the DRV8300DI. The current-sense amplifiers are **INA240A1**, not INA241A2. The unused AX7010 J2 connector and old phase-window OCP have been removed. The LM74502 input circuit does not establish reverse regeneration blocking; there is no fitted brake or verified sink for regenerated motor energy.

## Review, cost and qualification

- [Rev.A simplified architecture and production review](docs/rev_a_simplified_design_production_review_2026-10-11.md): retain/replace/remove decisions, fault-coverage boundaries, cost tradeoffs, ECO sequence and G0–G5 release requirements.
- [68-group Rev.A sourcing-cost/ECO matrix](hardware/ads8588s_servo/reva_cost_eco_2026-10-11.csv): selected manufacturer part numbers, LCSC codes, extended cost, production concerns and priorities. Based on **2026-10-10 snapshot**, approximately **CNY 164.67 per board** for 148 purchased fitted references, excluding PCB/assembly/tax/shipping. Supplier stock and prices must be refreshed before any order.
- [Current sourcing selection](docs/lcsc_sourcing_review_2026-10-10.md), [architecture](docs/architecture.md), [design calculations](docs/design_calculations.md), [fabrication gates](docs/release_gates.md), and [hardware handoff](hardware/README.md).
- [ADS8588S AX7010 dual-serial timing contract](docs/adc_fpga_timing_and_freeze_2026-10-12.md) and [schematic/part freeze status](docs/reva_schematic_component_freeze_matrix_2026-10-12.md). For 20 kHz PWM the selected ADC uses 8-channel simultaneous sampling, two serial data lanes, 64 SCLK per frame, and a proposed 10 MHz initial SCLK; **data-rate and analog filter latency are independent concerns**.

**Release blockers:** complete source-bound component/footprint/electrical/thermal/layout/mechanical/DFM reviews and exact material/process acceptance. Physical qualification remains NOT_RUN: hot-inductance/startup and total 12 V/1 A loading, shunts/connectors/cooling, gate-driver and fault-to-VGS-off timing, supply sequencing/ADC validity, 10 Arms thermal soak and external regeneration containment. Historical CAD passes never replace fresh checks after an ECO.

## Repository layout

- `hardware/`: separate `ads8588s_servo/` and `ad7606c_servo/` KiCad projects with their own hierarchy, libraries, BOM and four-layer PCB. Original board/source snapshots are preserved; both current boards remain unreleased.
- Interface XDC and ADC configuration files live beside their hardware projects; this repository contains no HDL implementation.
- `docs/`: architecture, sizing calculations, schematic/PCB reviews, procurement evidence and release checklist.
- `tools/`: repository checks, layout review, native KiCad audit helpers and qualification scripts.
- `.github/workflows/`: static/native review workflows. **Passing CI/ERC alone is not a manufacturing or electrical safety release.**

See [AGENTS.md](AGENTS.md) before making an electrical edit. Implement all hardware ECOs on a separate branch with fresh native KiCad netlist/physical-pin comparison, ERC, DRC and bench qualification; do not replace the current board based on a document-only review.

## 开发与验证入口

当前工具统一为 `python tools/pcb.py`，按工程配置执行检查、原生验证、导出和开发预览。新增板卡优先增加配置和领域规则，不新建一套独立检查脚本。

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py test --lane static
```

详见 [文档索引](docs/README.md)、[使用说明](docs/pcb_toolkit.md)、[新 PCB 接入](docs/pcb_toolkit_extension.md)；已替代的过程文档见 [归档](docs/archive/README.md)。
