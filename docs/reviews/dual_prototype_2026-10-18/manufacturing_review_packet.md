# 最终双方案工程审阅包

**制造状态：BLOCKED。两个 ZIP 均为 REVIEW_ONLY_NOT_FOR_FABRICATION_OR_ORDER。** 本轮已完成源设计修复、自动门禁和独立代理 CAM 审阅；这些记录不替代真实工程师签核或板厂接单确认。

冻结设计提交：`9f9b70cfb622c29919243b8b49e4078a175a1bf9`。后续文档提交不改变该批 EDA 输入。ZIP 是本机 `artifacts/` 证据，未提交二进制到 Git、未上传、未下单。逐文件清单及归档 SHA256 见[机器索引](manufacturing_review_packet.json)。

| 方案 | 本地 ZIP | 镀孔 / 电气过孔 | 原生输出 / 冻结输入 | 采购实装数 |
| --- | --- | --- | --- | --- |
| ads8588s | `artifacts/dual-servo/final-review-v3/ads8588s-engineering-review-only.zip` | 551 / 468 | 21 / 100 | 169 |
| ad7606c | `artifacts/dual-servo/final-review-v3/ad7606c-engineering-review-only.zip` | 594 / 511 | 21 / 208 | 191 |

每包包含 11 层实际 Gerber、PTH/零 NPTH 钻孔、原生 ERC/DRC、BOM/CPL 及精确实装对照、STEP/装配图/21 页中的对应原理图、只读输入快照、本地模型与授权、独立 CAM 图及逐孔对照、全部电气过孔的 POFV 选择 CSV/三页孔位图、53 个受控成品孔的位置表、工艺审阅 PDF、源验证记录和七份未签署的 NOT_RUN 模板。最终原理图 PDF 与已审阅修正版本逐页像素一致；旧工程包络图保留原始哈希，并附完整封装/模型等价证明。

在允许原型投板前，仍须完成：

- 器件、焊盘、电气、热预算、关键布局、机械及 DFM 七项真实工程签核。模板没有代签；所有签核必须绑定实际源哈希与制造规格。
- 确认接受 NP-155F/Tg155 候选与原先未证实 Tg170 目标的差异；确认精确 JLC041621-3313 叠构。
- 取得同一订单可组合四层外 70/内 30 µm 铜、ENIG、全部电气过孔付费 Type VII 非导电环氧填充/整平/铜帽、J1/J5 的 1.02±0.05 mm 及 J4 的 1.85±0.05 mm 成品孔保证。普通通孔公差、塞油或仅盖油不能直接替代。
- 复核实际 AX7010/J10 版本、通用焊盘的装配公差、引脚成形/座高及对插/工具/模块/外壳边界，核实电流、热、故障与外部吸能夹具假设。电流损耗计算中的 18 µm 孔壁铜仍是待厂家证实的假设。

投板后的低能量启动、VGS/OCP 延迟、独立电源时序、回馈、温升、EMC/ESD 和电机资格全部为 **NOT_RUN**。这些实板试验按[首板边界](first_board_boundary.md)在制造后执行，不被当作已有通过证据；当前生产发布门禁 Gate A/B 仍然阻断。

执行证据：[自动验收](final_cad_validation.json)、[独立 CAM](final_cam_review.md)、[功率预算/孔位图](final_power_review.md)、[模型边界](final_model_envelope_review.md)、[原理图逐页等价](final_schematic_export_equivalence.json)。

停止制造放行的依据是项目 [kicad-release 技能](../../../.agents/skills/kicad-release/SKILL.md)中的 “unsigned power/thermal review” 停止条件及人工工程审核前置条件，以及[仓库发布门禁](../../release_gates.md)。当前审核未签署，不能将自动检查通过改写为制造批准。
