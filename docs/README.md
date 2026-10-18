# 文档入口

当前维护两套独立 KiCad 工程。先通过 [硬件入口](../hardware/README.md) 选择 ADS8588S 原方案或 AD7606C 开发方案；两者都未获制造放行。

| 内容 | 当前文档 |
| --- | --- |
| 架构与电气目标 | [架构](architecture.md)、[计算](design_calculations.md)、[热/风冷输入](brake_thermal_design_basis_2026-10-10.md) |
| FPGA 与 ADC | [AX7010 接口](ax7010_interface.md)、[ADS8588S 时序合同](adc_fpga_timing_and_freeze_2026-10-12.md)、[高速 ADC 选型依据](adc_high_performance_reselection_2026-10-12.md) |
| 原理图和采购 | [选型证据说明](lcsc_sourcing_review_2026-10-10.md)、[冻结矩阵](reva_schematic_component_freeze_matrix_2026-10-12.md)、[生产复审](rev_a_simplified_design_production_review_2026-10-11.md) |
| 开发与验证 | [工具使用](pcb_toolkit.md)、[新 PCB 接入与规则扩展](pcb_toolkit_extension.md)、[迁移记录](toolkit_migration.md)、[CI 范围](ci_schematic_scope.md) |
| 资格与放行 | [当前发布门禁](release_gates.md)、[OCP 锁存协议及历史实施边界](ocp_latch_review_2026-10-09.md)、[动态资格程序](layout_followup_qualification_2026-10-10.md)、[低能量上电](bringup.md) |
| 本轮双方案审核 | [审核总入口](reviews/dual_prototype_2026-10-18/README.md)、[逐器件覆盖](reviews/dual_prototype_2026-10-18/component_coverage.md)、[器件审核](reviews/dual_prototype_2026-10-18/component_audit.md)、[首板边界](reviews/dual_prototype_2026-10-18/first_board_boundary.md)、[母线及损耗预算](reviews/dual_prototype_2026-10-18/power_static_budget.md)、[5 V 有效容量及软启动](reviews/dual_prototype_2026-10-18/tps62901_capacitor_review.md) |
| 最终制造审阅资料 | [双方案审阅包与剩余接受项](reviews/dual_prototype_2026-10-18/manufacturing_review_packet.md)、[冻结 CAD 总表](reviews/dual_prototype_2026-10-18/final_cad_validation.json)、[独立 CAM](reviews/dual_prototype_2026-10-18/final_cam_review.md)；仅供审阅，未制造放行 |
| 最新原理图验证 | [双方案原生导出、ERC、回归及证据哈希](reviews/dual_prototype_2026-10-18/latest_schematic_validation.json)；PCB 与制造状态单独验收 |
| PCB 审阅依据 | [布局规则及适用边界](pcb_layout_rules_2026-10-10.md)、[2026-10-10 审计及未关闭风险](schematic_layout_entry_audit_2026-10-10.md) |
| 文档规范 | [公开路径规则](public_path_policy.md) |
| 历史过程 | [归档索引](archive/README.md) |

## 当前与历史的区别

两方案均已采用修复后的四层 PCB，原始 ADS 双层未同步基线另行保留。本轮 U7、DC-link/J7 及电源/焊盘 ECO 已完成同步、布线和完整原生 DRC/图板一致性验收；历史候选的零计数不适用于当前源。当前冻结源的 [自动验收](reviews/dual_prototype_2026-10-18/final_cad_validation.json)、[独立 CAM](reviews/dual_prototype_2026-10-18/final_cam_review.md)及[最终工程审阅包](reviews/dual_prototype_2026-10-18/manufacturing_review_packet.md)分别记录适用哈希与剩余接受项；原[首板计划](superpowers/plans/2026-10-18-dual-servo-fabrication.md)保留任务沿革。两方案均未完成制造、RTL/STA和实物资格；不得把 CAD 通过当作制造或额定运行批准。

带日期但仍有适用技术合同、采购依据或未关闭资格步骤的文件留在当前区，并注明适用工程。已被替代的修复过程、旧计划和矛盾的发布勾选沿革移入 archive。`reviews/` 和 `sourcing/` 原始证据保持原位置，库存/价格只代表对应日期的快照。
