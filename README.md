# fpga-servo

FPGA-based single-axis PMSM/BLDC servo-drive daughterboard for the ALINX AX7010 / Zynq-7000 (2022 board, active PL connector J10).

> **Design / manufacturing hold — 2026-10-17.** The repository contains separate ADS8588S and AD7606C schematic/BOM projects. The retained ADS8588S PCB is unsynchronized with the current selection; AD7606C has no PCB. Historical zero-DRC results do not qualify either current design. There is no fabrication release, qualified OCP fault-off delay or full-power approval.

## 高速电流环 ADC 重新选型（2026-10-12）

**新性能目标首选ADI AD7606C-16BSTZ（LCSC C5371769）**，8通道16位同时采样/1MSPS、0–5V高速模式典型1.7µs相位延迟，建议使用J10的四路DOUT并行串行读取（20MHz下32clk=1.6µs）；要新增J10针脚29、30、31的DOUTC、DOUTD及SDI。此选择面向未来3–5kHz及更高电流环，不等于当前硬件已更换：**原Rev.A工程U6及BOM仍是ADS8588SIPM，FPGA原XDC保持原定义**；应在新KiCad与PCB同步ECO中进行替换。详见[高速ADC选型与迁移规格](docs/adc_high_performance_reselection_2026-10-12.md)、[6种真实器件候选及报价币种](hardware/ad7606c_servo/adc_fast_candidates_2026-10-12.csv)和[可验证的FPGA寄存器/IO分配草案](hardware/ad7606c_servo/ad7606c_fast_candidate_profile_2026-10-12.json)。

**2026-10-17 独立工程与目录整理：** [ADS8588S 原方案](hardware/ads8588s_servo/README.md) 与 [AD7606C 新方案](hardware/ad7606c_servo/README.md) 分目录保留。新方案已建立11页原理图和独立BOM/XDC，新增同源 ADC 供电及 TXU0204 电平转换；PCB、RTL/STA和硬件实测仍未完成。通过 [硬件入口](hardware/README.md) 选择工程。上面的2026-10-12段落保留选型沿革。

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
- [68-group Rev.A sourcing-cost/ECO matrix](hardware/ads8588s_servo/reva_cost_eco_2026-10-11.csv): selected manufacturer part numbers, LCSC codes, extended cost, production concerns and priorities. Based on **2026-10-10 snapshot**, approximately **CNY 164.67 per board** for 148 purchased fitted references, excluding PCB/assembly/tax/shipping. Supplier stock and prices must be refreshed before any order.
- [Current sourcing selection](docs/lcsc_sourcing_review_2026-10-10.md), [architecture](docs/architecture.md), [design calculations](docs/design_calculations.md), [fabrication gates](docs/release_gates.md), and [hardware handoff](hardware/README.md).
- [ADS8588S AX7010 dual-serial timing contract](docs/adc_fpga_timing_and_freeze_2026-10-12.md) and [schematic/part freeze status](docs/reva_schematic_component_freeze_matrix_2026-10-12.md). For 20 kHz PWM the selected ADC uses 8-channel simultaneous sampling, two serial data lanes, 64 SCLK per frame, and a proposed 10 MHz initial SCLK; **data-rate and analog filter latency are independent concerns**.

**Release blockers:** re-synchronize PCB and physical-pin mapping against current schematic; close any new ERC/DRC/unconnected/parity findings without waived checks; qualify L1 inductor current/saturation/thermal data, shunts and connector lands, gate-driver and fault-to-VGS-off worst-case timing, supply sequencing/ADC validity, 10 A thermal soak and the upstream DC source's reverse-energy handling.

## Repository layout

- `hardware/`: separate `ads8588s_servo/` and `ad7606c_servo/` KiCad projects; each has its own hierarchy, libraries and BOM. The original PCB remains unreleased.
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
