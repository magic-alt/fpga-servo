# 文档入口

当前维护两套独立 KiCad 工程。先通过 [硬件入口](../hardware/README.md) 选择 ADS8588S 原方案或 AD7606C 开发方案；两者都未获制造放行。

| 内容 | 当前文档 |
| --- | --- |
| 架构与电气目标 | [架构](architecture.md)、[计算](design_calculations.md)、[热/风冷输入](brake_thermal_design_basis_2026-10-10.md) |
| FPGA 与 ADC | [AX7010 接口](ax7010_interface.md)、[ADS8588S 时序合同](adc_fpga_timing_and_freeze_2026-10-12.md)、[高速 ADC 选型依据](adc_high_performance_reselection_2026-10-12.md) |
| 原理图和采购 | [选型证据说明](lcsc_sourcing_review_2026-10-10.md)、[冻结矩阵](reva_schematic_component_freeze_matrix_2026-10-12.md)、[生产复审](rev_a_simplified_design_production_review_2026-10-11.md) |
| 开发与验证 | [工具使用](pcb_toolkit.md)、[新 PCB 接入与规则扩展](pcb_toolkit_extension.md)、[迁移记录](toolkit_migration.md)、[CI 范围](ci_schematic_scope.md) |
| 资格与放行 | [当前发布门禁](release_gates.md)、[OCP 锁存协议及历史实施边界](ocp_latch_review_2026-10-09.md)、[动态资格程序](layout_followup_qualification_2026-10-10.md)、[低能量上电](bringup.md) |
| PCB 审阅依据 | [布局规则及适用边界](pcb_layout_rules_2026-10-10.md)、[2026-10-10 审计及未关闭风险](schematic_layout_entry_audit_2026-10-10.md) |
| 文档规范 | [公开路径规则](public_path_policy.md) |
| 历史过程 | [归档索引](archive/README.md) |

## 当前与历史的区别

ADS8588S PCB 保留未同步开发基线；AD7606C 只有原理图、BOM 与独立接口定义，没有 PCB/RTL/STA/实物资格。不得把旧修复报告的零 DRC 或某次 ERC 计数当作当前放行证据。

带日期但仍有适用技术合同、采购依据或未关闭资格步骤的文件留在当前区，并注明适用工程。已被替代的修复过程、旧计划和矛盾的发布勾选沿革移入 archive。`reviews/` 和 `sourcing/` 原始证据保持原位置，库存/价格只代表对应日期的快照。
