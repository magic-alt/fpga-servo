# 后续修复与图板同步审查

## 已完成的确定性修复

U19 TPD6E05U06RVZR 原有符号错误地只定义了 7 个引脚。已按 TI RVZ 数据手册修正为完整 14 引脚：六个通道使用 14/13/12/11/9/8，接地使用 5/10，NC 为 1/2/3/4/6/7。两个接地脚在原理图同节点显式堆叠，不使用隐式全局电源网络。补齐 `Package_SON:Texas_R-PUSON-N14` 封装并同步库、嵌入符号和 BOM。

新增真实引脚映射回归检查：先在旧网表观察到失败，修复后通过。网表现为 **137 个器件 / 169 条网络**；新增 6 条网络均为 U19 明确 NC 的引脚网络。旧审查中的 163 是本次修复前的历史值。

## 不能直接沿用的 PCB 内容

当前 PCB 有 32 个封装，原理图有 137 个器件：

- PCB 缺少 115 个当前位号。
- 22 个同位号器件的封装标识均不匹配，旧板使用 `fpga-servo:*` 简化封装。
- PCB 独有 CBUS1/CBUS2、RSHU/RSHV/RSHW、U14 等旧位号；H1..H4 为机械孔，不能当作普通多余电气器件直接删除。
- 已移除的本地 LDO、旧并行信号、PGND/Kelvin 伪网络仍在旧板中。
- 老板 20 段走线及铜区存在 54 项短路和 2 项交叉，不能凭原坐标保留就宣称连接有效。
- 全部 DRC 分类：tracks_crossing=2、shorting_items=54、clearance=24、solder_mask_bridge=118、track_dangling=3、silk_edge_clearance=7、lib_footprint_issues=32、silk_overlap=6、silk_over_copper=112；未连接 129 项。

同步应先保存旧板快照，再用真实库封装和当前网表逐焊盘重建一致性；旧铜只能在端点、净距和网络均重新验证后保留。不能通过删除线路或取消未连接检查制造“DRC 清零”。差异详情：`artifacts/pcb_sync_audit.json`。

## 新确认的功率器件问题

- 现用 GMSTBA 2.5/3-G-7.62 型接线端子的制造商额定电流为 **12A**，低于项目 15A 连续相电流和 25A 峰值目标。更换功率端子会改变间距、孔径和板边空间，需先冻结替代型号再摆放。
- 原描述 BVB-I-R005 的制造商额定为 **3W（70°C条件）/2W（高温条件）**，并非项目要求的 >=5W。5mΩ 在 25A 时耗散 3.125W，不能把此型号当作 5W 分流器闭合。三个分流器封装仍未分配，不能用通用封装冒充。
- LM74502 无反向电流阻断，OV 仅检测输入侧，不能单独处理母线再生能量。其 65V 输入限制与 55V 连续上限之间的浪涌裕量必须进行最坏钳位分析。

来源：

- [TI TPD6E05U06 数据手册](https://www.ti.com/lit/ds/symlink/tpd6e05u06.pdf)
- [Phoenix Contact 1766246](https://www.phoenixcontact.com/en-us/products/pcb-header-gmstba-25-3-g-762-1766246)
- [Isabellenhuette BVB 数据手册](https://www.isabellenhuette.com/hubfs/Files/Data-sheets/BVB.pdf)
- [TI LM74502 数据手册](https://www.ti.com/lit/ds/symlink/lm74502.pdf)

## 下一步电路方案

优先闭合独立 OCP 硬件锁存，具体可审阅方案见 `docs/superpowers/specs/2026-10-09-ocp-latch-design.md`。

母线保护有两个分支：可吸收再生的电源允许保留双向回流但须验证源端吸能与输入保护；普通单向电源需要反向阻断和独立制动斩波器/外接制动电阻。TVS 只承担规定浪涌，不能承担未限定的制动能量。

制动电阻按 `R <= V_clamp^2 / P_regen_peak` 选吸收功率，再验脉冲能量、平均功率和失效状态。电阻/斩波器的最终 MPN 依赖最大制动能量、周期、环境温度及实际电源容差；在这些参数未知时不能声称闭合热设计。

AX7010 实物版本和制动工况已向用户询问。机械板框保留现状作为约束，功率端子变化需要验证可容纳性。最终 ERC、图板逐焊盘一致性、布局检查、DRC 和 bench 门槛分别验收，不能互相替代。

本轮尚未改变 OCP 恢复策略、母线功率通路或 PCB；DRC 基线仍未闭合。

## 本文之后的锁存实施

以上 137/169 和未改变 OCP 的表述为 U19 修复阶段快照。用户确认后已新增 U20..U26 硬件锁存和整形，当前为 158 器件 / 183 网络。最新状态以 `ocp_latch_review_2026-10-09.md` 与 `release_gates.md` 为准，PCB 仍未同步。
