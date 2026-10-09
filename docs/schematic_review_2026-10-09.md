# 原理图优化与 layout 准入审查（2026-10-09）

## 实测结论

KiCad 10.0.3 对当前原生七页层级原理图执行 `sch erc --severity-all --exit-code-violations`，结果为 **0 错误、0 警告、0 豁免项**。未新增忽略规则或 ERC 排除项。网表为 **137 个功能器件 / 163 条网络**；包含显式未连接引脚网络，此数量用于防止导出不完整，不能单独证明电气功能。

五项仓库检查和新增网表安全检查均通过。当前 PCB 未修改，实测 DRC 仍有 **358 项违规、129 项未连接**，32 个封装与 137 个原理图器件尚未恢复一致。

## 本轮修复

1. 修复迁移遗留的层级实例根 UUID：原理图顶层 UUID 与器件实例路径不一致，曾导致导出仅有 79 条网络、ERC 产生 9 项悬空导线；修复后真实网络完整恢复。新增实例根一致性检查。
2. 将项目相对路径 `sym-lib-table` 纳入设计源，消除本机缺少全局映射产生的 130 项符号库警告。CI 使用空全局符号表，验证项目自身能解析库。
3. R80..R86：六路原始 PWM 和 GATE_EN 各加 10k 下拉，限定 FPGA 配置期间高阻输入的默认状态。R56..R61 继续下拉门控后的 FD6288 输入。
4. C80..C83：U8/U9/U10/U11 各加 100nF 本地去耦。C84/C85：U15/U16 各加 100nF 本地去耦。
5. 修复 C43/C44/C45 两端均接 GND 的功能错误，改为 VA_5V–GND；同时移动电容、压缩 INA 符号高度并同步项目库，减少相邻电源标注重叠。
6. 缩短可见器件值，详细规格保留在隐藏 Description 字段；主要 IC/MOSFET/电感记录 MPN。BOM 按实际 137 个位号重新生成，删除旧缓冲器、LDO、锁存器等不存在的项目。
7. D1、R32、RT1..RT3 设为实际 DNP 装配状态，避免仅在文本中写 DNP。
8. 网表回归检查覆盖输入下拉、去耦、栅极串阻/下拉、INA–ADC 采样路径、RUN_OK 扇出，以及双端元件被同网旁路的问题。BOM 检查覆盖位号、器件值、封装、MPN 和 DNP 一致性。

## 设计依据

- [TI SN74LVC1G11 数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf)：逻辑输入不得悬浮。
- [TI SN74LVC2G08 数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf)：每个 VCC 配本地旁路，单电源推荐 0.1uF。
- [TI TLV9024 数据手册](https://www.ti.com/lit/ds/symlink/tlv9024.pdf)：每颗比较器电源直接以低 ESR 0.1uF 旁路至地。

这些资料支持本轮偏置和去耦修改，不代表已完成所有器件的逐脚/温度/容差/封装认证。

## layout 准入边界

当前可开展封装核对、图板同步和初步分区摆放。**尚不能宣称达到工业级或冻结最终布局**，必须继续关闭：

- **故障恢复策略**：当前 OCP 是组合关断，故障解除且 GATE_EN 仍高时会自动恢复 PWM。FAULT_CLEAR 尚无硬件消费者。需确定并实现硬件锁存/手动重新使能策略。
- **上电及失电安全**：配置期下拉不等同于安全认证。需验证 AX7010 VIO、VA_5V、VDRV_12V 不同上电顺序、缺电和拔线时的实际门极波形及反向灌电流。
- **母线能量与浪涌**：D1 默认不装，LM74502 OV 未启用；需确定上游保护、浪涌钳位和再生能量吸收方案。
- **物理接口及功率封装**：真实 AX7010 版本和逐脚核对、四端分流器、接线端子、保险器件的确切 MPN/载流/封装必须冻结。已填 IC 订货号仍需核对制造商封装图。
- **功率验证**：OCP 阈值容差、故障关断延迟、bootstrap、死区、开关过冲、EMC 和目标电流热验证仍需计算/样机证据。

现有原理图没有本地 3.3V LDO或独立数字缓冲阵列；VIO_3V3 来自 AX7010，供安全逻辑、编码器接收器及 ADC DVDD。接口表中 J2 的并行/辅助信号只是预留分配，当前为 NoConn。相关文档已更正。

## 本地证据与复现

证据目录：`artifacts/`（生成物，不纳入 Git）：

- `ax7010_servo_reva.net`：真实导出网表。
- `ax7010_servo_reva_erc.json`、`ax7010_servo_reva_erc.rpt`：ERC 报告。
- `schematic_review.pdf`、`schematic_svg/`：七页原理图导出。
- `pcb_drc.json`：现有 PCB 的未闭合 DRC 基线。
- `baseline/`：本轮修复前及中间阶段诊断证据。

从根目录执行五项 `tools/check_*.py` 仓库检查；原生语法检查为 `check_native_schematic.py`，旧 `check_legacy_schematic.py` 已不存在。导出网表后运行：

```sh
kicad-cli sch export netlist -o artifacts/ax7010_servo_reva.net hardware/ax7010_servo_reva.kicad_sch
python tools/check_netlist_safety.py artifacts/ax7010_servo_reva.net
kicad-cli sch erc --severity-all --exit-code-violations -o artifacts/ax7010_servo_reva_erc.rpt hardware/ax7010_servo_reva.kicad_sch
```

BOM 通过 `python tools/export_bom.py` 从原理图字段生成。本轮未提交、推送或修改 PCB。
