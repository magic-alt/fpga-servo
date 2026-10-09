# OCP 硬件锁存实施与验收

## 当前状态

工作分支 `fix/ocp-latch-industrial-review`。在保留既有页面布局的前提下新增 `hardware/ocp_latch.kicad_sch`，接入原先未使用的 FAULT_CLEAR；当前八页原理图、158 个器件、183 条网络。旧审查文件中的 137/163 或 137/169 为相应历史阶段的结果。

U20 SN74LVC1G74DCUR：CLK=1、D=2、反相 Q=3（NC）、GND=4、Q=5、/CLR=6、/PRE=7、VCC=8。D 来自 U22 对 GATE_EN 的反相，CLK 来自 U21 对清除信号的施密特整形。/PRE 固定为 VIO，/CLR 为 U23 输出 `OCP_OK & PWR_READY & POR_OK`。U11 第三输入改为 ARMED，原始 OCP_N 保留 J1.23 诊断。TP5 引出 ARMED。

R87=10k 清除下拉，R88=1k 与 C92=1nF 构成约 1us 标称整形 RC；R89=100k 为并联开漏复位上拉；R90/R91=10k 分别下拉 ARMED 和 /CLR。C86..C91/C93 为 U20..U26 独立 100nF 去耦。所有这些器件必须装配。

## 复位监控与条件

U24 TPS3808G33DBVR 监控 VIO；U25 TPS3808G50DBVR 监控 VA5，两个监控器的 VDD 均接 VIO。DBV 引脚为 RESET=1、GND=2、MR=3、CT=4、SENSE=5、VDD=6。MR 接 VIO，CT 明确 NC，两 RESET 开漏并联。VA5 监控器没有由被监控的 VA5 自身供电，避免失电后输出直接悬空而失去 VA5 监督。

G33 下降阈值为 3.07V，按全温 ±1.5% 为 3.024..3.116V；G50 为 4.65V，按 ±2% 为 4.557..4.743V。CT 悬空的恢复延迟为 12..28ms。计入最高 2.5% 阈值迟滞，保守恢复电压上界约 VIO=3.194V、VA5=4.862V。**必须确认实际 AX7010 3.3V 最低电压满足该恢复条件**；3.3V±5% 的假设不能保证释放。SENSE 与 VDD 独立电压范围允许该监控接法，实际部分供电漏电仍需台架检查。[TI TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)

## 开漏信号边沿修复

独立复核发现普通 SN74LVC1G11 在 3.3V 要求输入边沿 <=10ns/V，开漏 RESET、OCP_N、PWR_GOOD 上拉不能保证这一条件。U26 采用 SN74LVC3G17DCUR（三通道施密特缓冲），1→7 为 POR_N/POR_OK，3→5 为 OCP_N/OCP_OK，6→2 为 PWR_GOOD/PWR_READY，VCC=8、GND=4；C93=100nF。三路开漏先整形再进入 U23，PWR_READY 同时送 U11。原始 J1 诊断网络及 R54/R55 上拉保留。[TI SN74LVC3G17 引脚表](https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf)

## 清除协议与竞争限制

1. GATE_EN=0、FAULT_CLEAR=0；等待电源和 OCP 正常且稳定至少 1ms（该稳定时间从监控复位释放后计算，上电应先等最长 28ms 恢复延迟）。
2. FAULT_CLEAR 拉高至少 10us，再拉低至少 10us。
3. 清除操作结束至少 10us 后才允许 GATE_EN=1。

故障期间的清除无效；GATE_EN=1 时清除会解除武装；清除保持高跨越故障及恢复，不会再次产生重武装边沿。异步清零释放与 CLK 几乎同时发生仍存在恢复/移除窗口，不能宣称任意相位竞争都被该电路消除。U20 在 3.3V 下 /CLR 最小低脉宽 2.7ns、释放至时钟最小 1.2ns、D 建立 1.3ns、保持 1.2ns；必须遵守上面的宽裕协议，并进行相位扫描台架测试。[TI SN74LVC1G74](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf)

## 关断时间预算

在 VIO=3.0..3.6V、-40..85°C、规定输入边沿和输出负载不超过数据手册条件时，原始 OCP_N 到 FD6288 命令输入的数字链为 U26→U23→U20 异步清零→U11→U8/U9/U10。最大传播延迟预算：6.4+6.2+7.9+6.2+5.3=**32.0ns**。U26 Rev.F 的时序表只给到 85°C；125°C 的典型图不能提供最大时序保证，需厂家确认或更换有对应上限的器件。[TI SN74LVC3G17](https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf)

该数字不包含走线、输入边沿、比较器、模拟前端或功率栅极放电；不等于电流故障到 MOSFET 截止时间。[TI 1G11](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf)、[TI 2G08](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf)

建议以原始 OCP_N 低脉宽至少 100ns 作为首轮数字注入验收条件；更短脉冲不作保证。监控器 SENSE 短暂欠压检测也不能当作无限带宽故障检测。总预算仍为 `t_INA + t_filter + t_comparator(overdrive) + t_logic + t_driver + t_gate_discharge`。必须在六个比较器实际输入过驱量、温度、阈值容差和布线负载条件下测量，并以 gate-to-source 波形验收；当前不声称总延迟已闭合。[TI TLV9024](https://www.ti.com/lit/ds/symlink/tlv9024.pdf)

## 自动验证与未闭合项

真实网表检查先对旧电路失败，接入后通过。额外在网表副本断开 FD6288 pin1：旧测试误通过，新物理端点约束明确失败；正确网表通过。六路门输出和 FD6288 pin1..6 的路径均被检查。`check_ocp_behavior.py` 对物理引脚网络执行 531 个稳定电平数字场景，包括故障锁存、清除保持高、故障中清除、高使能清除、六种已合格电源域次序和全部 64 种 PWM 组合。模型不模拟 RC、传播延迟、亚稳态、模拟上电或 MOSFET，电源合格条件由外部输入给定。

五项仓库检查、网表安全检查及数字行为检查通过。最新 ERC 为 0 错误 / 0 警告 / 0 豁免；保留项目已有四项忽略检查，未新增忽略项。PDF 导出八页并检查顶层、新增锁存页和改动的门控页。

本轮未修改 PCB；原板快照及原理图快照保存在 `artifacts/ocp_before/`。PCB 仍为 32 个封装，本轮重新运行 DRC 为 358 违规 / 129 未连接，不能视作新网表已同步。剩余原理图位号缺口为 136 个（22 个共同位号，10 个 PCB 独有位号，其中含 4 个机械孔）；现存共同封装也需按真实库重建。浪涌/再生、电流额定不合格的功率端子、分流器型号与封装、AX7010 实物接口仍阻止布局冻结。该单通道锁存不构成安全认证 STO。

独立审查提出的慢边沿与 FD6288 端点覆盖问题均已修复并复验。32ns 预算仅为上述限定条件下的数字链上界估算，完整关断仍待台架和温度工况闭合。
