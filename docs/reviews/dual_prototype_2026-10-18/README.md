# 双方案审核与修复记录

本轮从提交 `b0172a2f65902c7281cf4a8454f192dc791a9ef9` 开始，工作分支为 `feat/dual-servo-fabrication-readiness`。审核对象包括原理图、精确订购号与厂商引脚/焊盘、四层布局、局部回流、制造工艺及交付文件。

**两套修复后的四层 CAD 已采用，制造放行仍为 BLOCKED。** 原生 ERC/DRC、仓库几何规则、独立 CAM、工程师审核和实板资格分别记录；其中一项通过不能替代其余项目。早期零 DRC 候选曾被独立几何审核发现逃线组过宽和 ADC 本体下数字走线，均已实际修复，失败证据保留。当前采用记录和哈希如下，制造资料只能用于审核，禁止直接下单。

| 工程 | 原生元件 / 网络 / 引脚归属 | 实际采购实装数 | 当前采用证明 |
| --- | --- | --- | --- |
| ADS8588S | 180 / 145 / 634 | 169 | [采用记录](ads8588s_pcb_adoption.json)，PCB `e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226` |
| AD7606C | 202 / 172 / 714 | 191 | [最终采用记录](ad7606c_pcb_adoption_final.json)，PCB `dc0fb0a39529daa627db700bc2f53dd435f776633b9bd93aa8b1f0053b5f2134` |

原生系统对象包含 DNP 和外部 J6；五个测试点是 PCB 铜图形，不采购、不进入装配 BOM/CPL。原始 ADS 双层板及所有电气 ECO 前来源清单均已保留；[明确的来源转换](layout_adoption_transition.json)记录当前接受的布局/封装/模型变化，未删除历史保存检查。

两板采用候选的全严重级别原生 DRC 均为 0 violations / 0 unconnected / 0 parity；8/8 Kelvin、严格局部逃线组、自由直角、ADC 最大 10.2 mm 本体的数字铜线/过孔包络检查通过。In1 保持 GND，无非 GND 走线或铜区；贯穿过孔的反焊盘仍存在。24 条 SW/GH/GL/BST 网络还独立核对了真实物理引脚、原生有效 netclass 与精确名称匹配，POWER 为 0.8 mm、GATE 为 0.25 mm；没有用展示名称替代原生转义名称。以上均为静态 CAD 证据，不代表动态、噪声或热资格。

ADS 的最终 [VA5 供电桥 ECO](ads8588s_in1_supply_bridge_eco.json)移除旧 In1 分支并以 4.8926 mm、0.5 mm 宽的 F.Cu 桥接两块真实供电铜岛；[含覆铜的连通证明](ads8588s_in1_zone_connectivity.json)确认 32 个实际 VA5 引脚仍在同一连通组件。仅删除旧分支曾产生 1 个未连接项，该版本已否决并保留。新增全板保留地层检查覆盖任意网络走线、圆弧以及板级/封装内铜区；过孔反焊盘和真实规则区分别处理。

| 范围 | 可审阅证据 |
| --- | --- |
| 需求与首板边界 | [首板条件](first_board_boundary.md)、[发布门禁](../../release_gates.md)、[低能量上电程序](../../bringup.md) |
| 器件完整性 | [逐器件库存与覆盖](component_coverage.md)、[器件审核](component_audit.md)、[问题清单](findings.csv) |
| 电气修复 | [U7 物理引脚](u7_post_eco_verification.json)、[DC-link/J7](dc_link_eco_verification.json)、[5 V 容量/软启动](5v_eco_verification.json)、[栅极电阻](gate_resistor_review.md) |
| 焊盘与装配 | [焊盘审核矩阵](footprint_land_matrix.md)、[装配 ECO 精确网表证明](assembly_land_eco_verification.json)、[填孔工艺候选](q_via_process_candidate.md) |
| 电源与热预算 | [母线、损耗和分阶段夹具](power_static_budget.md)、[最终候选静态铜路审查及适用哈希](final_power_review.md)、[5 V 预算](tps62901_capacitor_review.md) |
| 历史布局基线 | [修复前布局审核](layout_audit.md)，保留原始阻断和旧计数，不代表当前修复结果 |
| 原理图证据 | [新鲜导出/ERC/回归记录](latest_schematic_validation.json)，以文件所列输入哈希与时间为准 |

两方案的设计输入均为 24–48 V、20 kHz、10 Arms 连续相电流、20 A 瞬时正弦相电流幅值持续 30 s（14.142 Arms）、40°C 强迫风冷、12 V **总**连续负载 1 A。没有板载制动；任何电机操作前都需要独立验证的外部吸能/钳位。J7 绕过输入 F1，外部夹具必须自行提供协调的支路保护。

已查证的制造候选为 JLC041621-3313、NP-155F/Tg155、四层外 70 µm/内 30 µm 铜、ENIG。Tg155 与原先未证实的 Tg170 目标不同，材料接受尚未关闭；电气过孔采用付费四层 Type VII 树脂填充/整平/铜帽工艺候选，J1/J5 与 J4 需要指定的成品孔公差。公开工艺能力不代表厂家已接受实际订单。所有物理启动、示波器、温升、故障注入和电机试验均为 **NOT_RUN**。

最终冻结源的[自动验收总表](final_cad_validation.json)记录两工程各自的新鲜原理图、原型及完整发布验证；两板所有自动项通过，原型门禁仅缺七项真实人工签核，完整发布仍受 Gate A/B 资格阻断。主回归 315 项中 272 通过、43 明确跳过；另一次使用 KiCad Python 的原生回归 81 项全部通过，这两个运行的计数不作为不重复用例求和。

[页码及全物理网表等价证明](page_metadata_native_verification.json)和[局部电源/地可见连线修复](schematic_visible_returns_verification.json)记录原理图最终消歧；[最终模型与工程包络](final_model_envelope_review.md)、[独立 CAM](final_cam_review.md)及[最终功率/孔位图](final_power_review.md)各有明确适用哈希。原生 ERC/DRC 均无忽略项或排除项。审阅包的工程师签核、板厂实际工艺接受及所有物理资格继续开放。
