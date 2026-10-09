# 原理图连续电路与可读性整理

日期：2026-10-09。工作分支：`fix/ocp-latch-industrial-review`。

本轮处理元件散落、过度依赖标签和部分文字遮挡线路的问题。只整理原理图的排布、连线表达和注释，不改变电气设计，也不进行 PCB layout。

## 页面调整

| 页面 | 调整内容 |
| --- | --- |
| Auxiliary Power | 连出 U12 的输入电容、RON 电阻、bootstrap、电感、输出电容、反馈分压和纹波注入；连出 U13 的输入、输出 LC 和 VOS 回授；两路 PG 输出显式相连。 |
| AX7010 Interface | R80–R86 分别从 J1 的六路 PWM 和 GATE_EN 引出下拉支路，共用可见的 GND 回路；将未使用的 J2 移到独立区域。保留 AX7010 2022 / J10 标识和 pin 2 NC。 |
| Current Sense / OCP / ADC | 三路 INA241、输出 RC 与 ADC 电流输入直接连线；窗口比较器分为上下两组，阈值分压与参考母线直接相连；连接开漏故障汇流线和 R54；ADC 参考电容直接接到相应引脚；去耦银行移到标题栏以外。 |
| Gate Driver / Inverter | 补出六个 RGS 到对应 MOSFET 栅极节点的线路；U1 的 C69/C46 接入实际供电；R55 接入 PWR_GOOD/VIO 端口；六个输入下拉与四个逻辑去耦电容分别整理成共地/共电源母线组。隐藏遮挡线路的数据手册字段。 |
| Differential ABZ Encoder | J5、三组终端电阻、U19 ESD 分支与 U7 接收器形成连续差分通路；连出编码器供电保险和接收器电源去耦。J5 镜像、U19 旋转仅用于图面表达，物理引脚号不变。 |
| OCP Hardware Latch | 连出清故障 RC 滤波、Schmitt 缓冲、使能反相、锁存、下拉和 ARMED 测试点；两个 supervisor 共用 POR_N，经过 U26 接入保护逻辑；对应去耦电容就近绘制在各 IC 电源旁。 |

顶层与 DC Input 页原有主要电路已经连续绘制，本轮保持这两张源文件不变。所有子图仍使用原有层级端口。电源/地和部分跨功能区信号仍保留标签，例如驱动输入偏置组到 U1 的 HIN/LIN 链路，避免长线穿过其他功能块。

## 验证结果

- 新导出的前后网表：644 个引脚的网络名逐一比对，差异为 0。
- 系统 BOM：159 项；板载网表：157 元件、179 网络。外置 F1/J6 的处理保持不变。
- 所有器件的位号、UUID、引脚 UUID、属性值、封装及 BOM/on-board/DNP 状态一致。
- `check_native_schematic.py`、`check_kicad_grid.py`、`check_schematic_layout.py`、`check_schematic_connectivity.py`、`check_design.py` 全部通过。
- `check_netlist_safety.py` 通过；`check_ocp_behavior.py` 的 531 项稳态场景通过。
- KiCad 10.0.3 原生 ERC，`--severity-all --exit-code-violations`：0 错误、0 警告、0 排除违规。工程规则文件逐字节不变。
- BOM、项目符号库与 PCB 均逐字节不变。PCB SHA-256：`581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`。
- 导出并逐页查看 8 页 PDF；`git diff --check` 通过。

本地检查证据保存在 `artifacts/schematic_readability/`：`before/` 源文件快照、`before.net`、`after.net`、`before.pdf`、`after.pdf`、`erc.json`、`verification.json` 和逐页 PNG。该目录按仓库规则不纳入 Git。

## 交付边界

这是保持电气网表不变的原理图表达整理。未执行 PCB 同步、布局、布线或制造导出，因此没有新增 DRC 通过结论。原有 OCP 动态时序、浪涌/再生、电流热额定值和 PCB 制造验收要求仍以 `docs/release_gates.md` 为准。
