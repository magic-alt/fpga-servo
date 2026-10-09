# Gate Driver / Current Sense 页内完整连线

日期：2026-10-09。分支：`fix/ocp-latch-industrial-review`。图纸保持 A4 横向；PCB 未修改。

## 已应用的两页优化

`hardware/gate_inverter.kicad_sch` 重新排布为使能与三路 PWM 门控、FD6288、并列的三个半桥及电机输出。门控输出、六个输入下拉、bootstrap、栅极电阻、栅源电阻、分流电阻、供电和去耦均通过实际导线连接。

`hardware/current_adc.kicad_sch` 重新连通三路 INA241/RC、上下窗口比较器、阈值分压、开漏故障汇流、温度分压、ADS8588S 模式配置、参考/REGCAP 以及电源和地。

本轮验收不再只看 ERC：对两页分别检查 **42 / 33 个页内网络**，每个网络的全部元件引脚及其标签都位于同一个物理导线连通分量内。同名标签不参与这个物理连通检查。修改前的页面作为负对照，能检出地、门控、驱动、采样和电源等网络的多个导线孤岛；修改后为零。

## 验证

- 前后原生网表的物理引脚分组完全相同：157 板载元件、179 网络；系统 BOM 为 159 项。
- 所有器件属性值、器件 UUID、引脚 UUID 不变。
- 五项仓库检查、网表安全检查及 531 项 OCP 稳态场景全部通过。
- 当前工作工程原生 ERC：0 错误、0 警告、0 排除违规。
- BOM、PCB、符号库、工程规则、顶层及其余五张子图与本轮开始前逐字节一致。
- PCB SHA-256：`581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`。

## Global label 候选版

按用户提出的跨页 global label 方案，已在 `artifacts/schematic_complete/candidate/` 形成隔离候选工程。35 个跨页名称逐一确认对应唯一的原有根网络；候选工程 179 个网络的物理引脚分组与修改前完全相同，原生 ERC 为 0 违规，两页物理导线检查同样通过。

正式迁移需要同步其他子图的跨页标签、顶层接口和原有“禁止 global label”的检查规则。自动审批拒绝了这项工程范围的迁移和检查规则修改。目前等待用户明确确认，候选版尚未应用；工作工程暂保留原有层级接口和所有检查规则，避免留下不能通过验收的中间状态。

## 本地可审阅文件

- 已应用的完整连线两页 PDF：`artifacts/schematic_complete/Gate_Driver_Current_Sense_wired.pdf`。
- Global label 候选两页 PDF：`artifacts/schematic_complete/Gate_Driver_Current_Sense_candidate.pdf`。
- 当前工程完整 PDF：`artifacts/schematic_complete/wired.pdf`。
- 快照、前后网表、ERC、物理导线检查脚本、负对照与验证清单：`artifacts/schematic_complete/`。

这次不涉及 PCB 同步、布局、布线或制造放行。电气动态和实物验证仍按 `docs/release_gates.md` 执行。
