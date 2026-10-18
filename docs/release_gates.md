# 当前硬件发布门禁

状态：**SCHEMATIC/BOM AND FOUR-LAYER CAD VALIDATED / ENGINEERING REVIEWS OPEN / PCB RELEASE BLOCKED / NOT FOR FABRICATION**。本页整理当前适用条件，不把历史勾选或零 DRC 结论沿用到当前设计。当前源哈希与审核资料见[双方案入口](reviews/dual_prototype_2026-10-18/README.md)。

| 工程 | 当前交付 | PCB 状态 |
| --- | --- | --- |
| ADS8588S Rev.A | 独立 9 页原理图、BOM、原 FPGA 接口 | 已采用修复后的四层板；原生 DRC/未连接/parity 均为 0，制造审核未关闭 |
| AD7606C 开发版 | 独立 12 页原理图、BOM、四路接口与电平转换 | 电气 ECO、关键回路及逃线组已修复并采用；原生 DRC/未连接/parity 均为 0，制造审核未关闭 |

当前流程见 [工具使用](pcb_toolkit.md) 与 [CI 范围](ci_schematic_scope.md)。完整旧门禁勾选及过程计数保存在 [历史快照](archive/release_gates_before_toolkit_2026-10-17.md)，不作为当前完成项。

本轮双方案审核发现两板 U7 AM26LV32E 物理引脚映射错误，已修正库和嵌入符号；此前零 ERC/DRC 不能证明该错误不存在，也不能沿用到 ECO 后铜路。2026-10-19 完成独立阻尼 DC-link/J7、5 V 有效容量/软启动和装配焊盘 ECO 后，新鲜原生网表为 ADS8588S 180 元件 / 145 网络 / 634 引脚归属，AD7606C 202 / 172 / 714；两板全部 ERC 检查启用，均为 0 errors / 0 warnings / 0 exclusions。修复后的四层板已采用；八路 Kelvin、局部逃线范围、自由直角和 ADC 最大本体数字铜路检查通过。器件/封装、热预算、关键布局、机械和 DFM 的人工审核，以及实际材料/工艺接受仍未关闭。

用户授权的是工程首板。`prototype_ready` 与完整 `pcb_release` 分开验收；首板必须先关闭静态设计、布线和制造问题，台架项目保持 NOT_RUN。具体界限见 [首板证据要求](reviews/dual_prototype_2026-10-18/first_board_boundary.md)，不得用首板身份豁免错误电路或缺失 DFM 证据。

2026-10-18：AD7606C 已按确认的原板框/孔/接口建立四层 PCB；见 [当前 PCB 审查](../hardware/ad7606c_servo/evidence/pcb_review_2026-10-18.md)。布局候选不关闭未连接、器件定版、关键回路、热和实物门禁。

2026-10-18 后续：已落实 AD7606C 12 V 总负载 1 A 电源 ECO，见 [电源与原生验证](../hardware/ad7606c_servo/evidence/aux_power_review_2026-10-18.md)。GUI 保存网表漂移已修复，最终原生保存回读精确一致；当时 PCB 有 499 未连接。后续该历史版本完成布线、未连接为 0；当前 ECO 后须重新验收；满载启动、热和动态实测保持 OPEN。

2026-10-18 电气 ECO 前的历史布线收尾：见 [历史 CAD 验收](../hardware/ad7606c_servo/evidence/pcb_routing_acceptance_2026-10-18.md)。AD7606C 全部 ERC/DRC 类别启用，0 errors / 0 warnings / 0 exclusions / 0 unconnected / 0 schematic parity；原生几何及图板检查通过。1 A 台架状态仍为 NOT_RUN，不宣称实物连续输出保证。

## 当前选型和边界

公共功率级使用 DRV8300DPWR、INA240A1DR，三路 5 mΩ 相内采样和独立 2 mΩ 母线采样；母线 OCP 为正向标称 +25 A，不是反向保护或故障最大电流保证。F1 为板载 0456025.ER，无外置保险座；J2 已从当前原理图取消。旧 FD6288、INA241、外置 F1 和相窗口 OCP 描述属于历史。

工作输入仍为 24–48 V 母线、10 Arms 连续相电流、20 kHz PWM、20 A 峰值 30 s、40°C 环境、目标温升不超过 50 K、强迫风冷、5 V ABZ 编码器。峰值重复间隔、实际风量/风扇失效和编码器启动电流仍待限定。制动电路已取消，不假定电源能吸收回馈能量。来源见 [选型](lcsc_sourcing_review_2026-10-10.md)、[热设计输入](brake_thermal_design_basis_2026-10-10.md)、[冻结矩阵](reva_schematic_component_freeze_matrix_2026-10-12.md)。

## 自动检查能证明什么

2026-10-17 工具迁移中，实际 KiCad 10.0.3 新鲜 XML：ADS8588S **159 个系统对象 / 135 个网络**，AD7606C **181 / 162**；两工程 ERC 均 **0 errors / 0 warnings / 0 exclusions**。原有四类项目 ignore 设置未改动；这不等于没有被禁用的 ERC 类别，更不等于生产批准。执行与未执行边界见 [迁移记录](toolkit_migration.md)。

静态图面、物理引脚、数字稳态 OCP 和 ADC 阈值检查可发现对应合同的回归；不能证明完整保护延迟、MOSFET SOA、抗扰度、模拟恢复、热设计或真实 PCB 铜路。未同步旧板的精确基线回归只能证明已知差异未变，不能证明 parity 或 DRC 合格。

## Gate A：电气输入和静态设计冻结 — BLOCKED

- [ ] 实际 AX7010 2022/J10 逐脚核对；复核 LVCMOS33、在用 PL 功能冲突和 VIO 最小值。新 ADC 接口还需实际 RTL/STA 与启动配置证据。
- [ ] 固定所有器件订购号、厂商封装焊盘图和装配资格；不能把采购候选或相似封装当作合格替代品。
- [ ] 资格化分流器、焊点、连接器、电源铜路的电流和温升；10 Arms/20 A 目标不等于已有热证明。
- [ ] AD7606C 已确认 12 V 总连续负载 1 A，采用 150 µH Wurth 电感及精密反馈/纹波 ECO；[静态计算与假设](../hardware/ad7606c_servo/evidence/aux_power_review_2026-10-18.md)已明确，满载启动、温升和瞬态实测仍待完成。旧 0.5 A 开发限制仅为原方案历史边界。
- [ ] 确认 25 A 保险适用的前瞻故障电流不超过 500 A、包络不超过 72 V，并完成浪涌、环境降额和 I²t 协调。
- [ ] 限定 U26、F2 局部环境不超过 85°C；整体 40°C +50 K 目标不能扩展其额定值。
- [ ] 按原始 JILN 图纸核实主选 J1/J5 的 1.02 ±0.05 mm 成品镀孔及可保证该窗口的制造工艺；旧双厂商 ±0.03 mm 约束不代表常规工艺能力，也不授权 BOOMELE 直接替换。完成每脚电流和实际装配资格。NTC2 是板载温度，不代表远端电机绕组温度。

## Gate B：动态和台架资格 — BLOCKED

- [ ] 证明最快 VA5 下跌时，在 ADC AVDD 低于 4.75 V 前所有实际 VGS 已关闭；静态阈值裕量不等于关断延迟保证。
- [ ] 覆盖 VIO、VA5、VDRV 独立上/下电、部分供电、转换器 OE、复位和恢复；ADC 配置/新帧未有效前保持 GATE_EN=0。
- [ ] 实测母线分流器到 VGS-off 的完整最坏延迟、PWM 抑制、窄脉冲、clear/fault 竞争及故障后禁止自动重启。
- [ ] 资格化驱动器 dv/dt、INA240 共模暂态、bootstrap 有效容量、MOSFET 开关 SOA、死区和过冲；理想 SPICE 或栅电荷比值不关闭该门禁。
- [ ] 在不假定上游吸能的条件下处理浪涌和再生能量，明确系统过压包络。
- [ ] 完成 ADC 三相增益/偏置、动态恢复、ABZ 极限频率及新 ADC 时序/噪声验证。
- [ ] 在明确重复周期、风量、环境和装配条件下完成 10 Arms 热浸及 20 A 峰值资格。

OCP 协议和未关闭试验条件见 [锁存说明](ocp_latch_review_2026-10-09.md) 及 [动态资格程序](layout_followup_qualification_2026-10-10.md)。旧程序中的器件/计数按当前工程核对，不能重用历史完成结论。

## PCB 与制造 — BLOCKED

- [x] 已修复厂商物理引脚和已确认焊盘缺陷，并完成原生图板同步；机械锚点、旧板快照和来源转换记录保留。
- [x] 本轮两套采用 PCB 的引用、值、DNP、完整封装 ID、每个物理焊盘和网络通过新鲜图板一致性检查。
- [x] 两套采用 PCB 全部类别、全严重度原生 DRC：0 violations、0 unconnected、0 schematic parity；无新增排除或降低严重级别。此项只对当前记录哈希有效。
- [ ] 审阅实际板框/机械、两方案四层外层 2 oz/内层 1 oz 实际叠构（已核实候选 JLC041621-3313、NP-155F/Tg155，非初始 Tg170 目标）、回流、功率/门极环路、Kelvin、ADC/编码器及热铜/过孔。
- [ ] 完成厂商封装与热/电流/连接器/动态资格后，再审阅 Gerber、钻孔、BOM/CPL 一致性及低能量首件记录。

ADS8588S 历史双层板已归档，当前采用四层修复板；不能复用旧板或中间候选的零 DRC 结论。两板当前 CAD 项通过，不关闭人工工程审核、材料与特殊工艺接受、机械装配、动态/热实测、制造批准和首件门禁。首板前的静态审核与投板后的物理资格按[首板条件](reviews/dual_prototype_2026-10-18/first_board_boundary.md)分开记录，不能把尚未制造的实板试验写成通过。
