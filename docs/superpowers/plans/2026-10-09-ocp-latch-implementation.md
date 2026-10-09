# OCP 硬件锁存实施计划

> For agentic workers: 当前会话执行；按用户要求进入 fix/ocp-latch-industrial-review 并保留已有未提交硬件修订；完成后独立复核。

Goal: 将经用户确认的 ARM 锁存接入真实 KiCad 层级与网表。
Architecture: 新增 ocp_latch A4 页；U20 SN74LVC1G74DCUR，U21 SN74LVC1G17DBVR 清除整形，U22 SN74LVC1G14DBVR 使能反相，U23 SN74LVC1G11DCKR 健康条件门，U24/U25 TPS3808G33/G50DBVR 监控 VIO/VA5。两监控器均由 VIO 供电，RESET 开漏并联；CT 悬空选择 20ms 典型恢复延迟。
Tech Stack: 原生 KiCad 10 / Python / kicad-cli。
Spec: ../specs/2026-10-09-ocp-latch-design.md（用户 2026-10-09 确认并继续）。
Global Constraints: 不降低 ERC；不修改 FPGA 引脚分配；不把数字逻辑验证当作实物安全认证；不覆盖已有 PCB；浪涌再生和功率器件额定仍需闭合。
Review Focus: Q=pin5、反相 Q=pin3；TPS3808 DBV 引脚；故障优先；清除卡高；供电次序；实际网表连接。

## Task 1: RED 网表安全约束
- [x] 修改 tools/check_netlist_safety.py，要求真实 J1.10 清除路径、ARMED 接 U11.6、异步清零、监控器和去耦；对当前网表运行必须失败。
## Task 2: GREEN 电路与层级
- [x] 新建 hardware/ocp_latch.kicad_sch；同步本地符号库；新器件独立去耦和明确默认偏置。
- [x] 修改顶层、gate_inverter、原理图文件清单；导出 BOM、网表；通过安全连接检查。
## Task 3: 时序与验收
- [x] 记录数据手册阈值/延迟/最小脉宽及清除竞争限制；运行基于实际网表的数字行为场景（不冒充模拟/台架验证）。
- [x] 运行全部仓库检查和 severity-all ERC；导出并检查 PDF。
## Task 4: 审阅与交付
- [x] 独立审阅并修复发现；更新审查报告和 release gates，明确尚缺的台架/浪涌/封装/PCB 门槛。

自审：供电与复位为专用监控器，清除 RC 不放在故障路径；VIO 低于器件工作范围的模拟行为不由布尔模型证明。用户已授权实施，不再重复请求确认。

执行记录：初始网表约束 RED；初次接入156/180 GREEN；独立审查发现开漏慢边沿和驱动器端点测试遗漏；新增U26三通道施密特/C93，最终158/183，531稳定场景通过。FD6288断线副本由旧测试PASS转为新测试FAIL。顶层采用局部追加锁存页，未执行整页重写；本轮PCB未改。U26时序规格限制85C，已写入release gate。
