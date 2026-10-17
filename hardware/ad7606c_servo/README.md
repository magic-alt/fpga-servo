# AX7010 + AD7606C-16 独立开发工程

本工程把已有高速 ADC 迁移规格落实为新的 KiCad 10 原理图，保留原 `hardware/ads8588s_servo/ax7010_servo_reva.*` / ADS8588S 方案。源基线为 `17166bc`，开发分支为 `feat/ad7606c-independent-project`。所有新增文件均在本目录；未把旧 PCB 复制成新版 PCB。

用 KiCad 打开 [ax7010_servo_ad7606c.kicad_pro](ax7010_servo_ad7606c.kicad_pro)。直接查看完整图纸可打开 [11 页原理图 PDF](evidence/schematic.pdf)。[开发板方案与调试流程](development_board.md) 说明接口、启动、配置、时序和后续 PCB 工作。

## 已实现

- 独立顶层和 10 个功能子页；从旧工程复制电源、逆变器、编码器和 OCP 保护，保留已有位号及元件身份。复用页保留 Rev.A 标题以便追溯，新增/修改页标为 B-DEV。
- U6 使用新建的、完整 64 物理脚的 `AD7606C_16_SERIAL` 本地符号，拆为输入、串行、模式、供电及参考五个单元。
- AD7606C-16BSTZ，软件模式 OS[2:0]=111，四路 DOUT；CH1–3 为 0–5 V，CH4–8 为 0–10 V，CH1–4 高带宽。CH7/8 输入及所有负输入接地。
- 两个 REGCAP 分别 1 µF；REFCAPA/B 短接并接 10 µF；REFIN/REFOUT 接 100 nF；四个 AVCC 引脚各有 100 nF，本地另加 C100 10 µF。
- **AVCC 与 VDRIVE 在图上直接接同一 VA_5V。** U27–U29 为 TXU0204PWR，隔开 ADC 5.1 V 和 AX7010 3.3 V；OE 接 `PWR_READY`。这修复了直接把独立 FPGA 电源接到 VDRIVE 时的绝对最大额定风险。它不是电气隔离器，也没有替代原 OCP。
- J1/J10.29、.30、.31 分别接 DOUTC、DOUTD、SDI；独立 XDC 包含 U12、T12、T10，原 XDC 不变。
- ADC 端 RESET/CS 上拉、CONVST/SCLK/SDI 下拉；R110/R111 在转换器 A 端另设 3.3 V 上拉，FPGA 高阻且 OE 已启用时仍保持 RESET/CS 高。转换器启用后由 FPGA 经过转换器驱动，必须执行完整复位和配置。

器件引脚/模式依据 [ADI AD7606C-16 Rev.A，Table6/9、Figures106/124/125](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf)；转换器依据 [TI TXU0204 SCES936A，Table6-1、§9.3、§11](https://www.ti.com/lit/ds/symlink/txu0204.pdf)。封装分别选用标准 KiCad LQFP-64 10×10/P0.5 和 TSSOP-14 4.4×5/P0.65；装配/制造资格仍需审核。

## 文件入口

| 文件 | 用途 |
|---|---|
| `ax7010_servo_ad7606c.kicad_pro/.kicad_sch` | 新工程与顶层 |
| `current_adc.kicad_sch` | 保留的三相 INA240、NTC、母线 OCP |
| `adc_core.kicad_sch` | ADC 输入、串行和启动偏置 |
| `adc_power.kicad_sch` | 同源 AVCC/VDRIVE、参考和去耦 |
| `adc_levelshift.kicad_sch` | 三颗 TXU0204 与本地旁路 |
| `ax7010_interface.kicad_sch` | J10 四路接口 |
| `bom.csv` | 从真实 KiCad XML 导出的每位号 BOM，包含 DNP |
| `adc_profile.json` / `*.xdc` | 本工程独立配置和 FPGA 引脚约束；尚无驱动 RTL/STA |
| `evidence/adc-physical-pins.csv` | 64 脚与实际网表所有相连端点 |
| `source_manifest.json` | 原方案基线和原文件 SHA-256，防止意外覆盖 |
| `tools/` | 有范围的原生结构生成和独立验收工具 |

`sym-lib-table` 和 `fp-lib-table` 都使用 `${KIPRJMOD}`；项目本地符号和 `fpga-servo.pretty` 已复制。标准 KiCad 元件封装库仍需随 KiCad 安装。

## 实际验证与边界

本机 KiCad 10.0.3，`python` 3.12.4。最终执行记录见 [verification.json](evidence/verification.json) 和 [静态结果](evidence/static-checks.json)。新旧 XML 均为本轮原生导出，不使用历史计数代替。

新工程验证包括：完整物理脚和模式检查、层次一致性、50 mil 网格/A4 布局、可见电源连线、18 项错误注入、531 项 OCP 稳态数字场景、ADC 供电静态阈值和原生全严重度 ERC。最新网表为 **181 个系统元件对象 / 162 个网络**，其中板载元件对象 180 个，另 1 个为外部 J6；DNP 另列于 BOM。原工程保留为 159 元件/135 网络。

原理图交付模式已完整通过新旧工程检查、旧 ADC 串行/候选规格/选型/供电/安全/OCP 回归、两工程 ERC 及旧板精确差异回归。默认严格 `check_design.py` 仍因旧 PCB 中 J2、旧驱动器/分流器/封装及规则不一致而失败。旧板没有修改，也没有获得 parity/DRC/制造批准；记录中明确区分交付范围和 PCB 发布状态。

沿用原项目四类 ERC ignore 设置：`footprint_filter`、`four_way_junction`、`simulation_model_issue`、`single_global_label`；未增加忽略项或 ERC exclusions。ERC0 不代表动态供电、环路性能或制造验收完成。

本次没有新 PCB、DRC、布线、Vivado STA、FPGA 实机测试、闭环性能或高功率试验。原 [release_gates.md](../../docs/release_gates.md) 中 OCP、母线再生、热与连接器等门禁继续适用。

## 复现

在仓库根目录执行：

```powershell
python -X utf8 hardware/ad7606c_servo/tools/run_checks.py --schematic-only
```

如 KiCad 路径不同，追加 `--kicad-cli <kicad-cli.exe路径>`。完整输出在 `evidence/logs/`，逐步骤退出码在 `evidence/verification.json`。显式原理图模式返回 0 只表示本次原理图交付及旧板回归通过。省略 `--schematic-only` 的默认严格模式仍会因旧 PCB 门禁返回 1。

`tools/build_project.py` 是可重复生成入口，固定读取 `17166bc` 的原始图纸；**重跑会覆盖本目录内生成的原理图/库/配置，应先把新增手工修改纳入生成器或另行保存。** 它拒绝在 main/master 或 detached HEAD 上生成。日常验收只运行 `run_checks.py`，不需要重新生成。

CI 范围与严格 PCB 发布入口见[检查说明](../../docs/ci_schematic_scope.md)。原理图模式需显式指定；默认严格模式仍会报告旧 PCB 阻塞。
