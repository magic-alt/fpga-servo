# 双方案原理图审核与修复 — 2026-10-23

结论：**原理图静态拓扑与当前物理引脚合同自洽；已修复本轮确认的信息/库定义缺陷。工程性能与制造放行仍为 BLOCKED。** 本轮没有发现证据充分、需要新改铜路的电气连接错误，也没有以零 ERC 推导完整电气安全。

范围为当前 ADS8588S 的 9 页与 AD7606C 的 11 页原理图、本地库、BOM、接口约束及对应 PCB。以根 AGENTS.md、项目门禁和所选器件原厂资料为依据；这不是对未指定版本的 IPC/IEC 标准作完整合规认证。工作分支为 `codex/full-schematic-audit-20261023`，起始提交 `7465e6ec2d88df90197d9960c535f58cb227e420`。原有未跟踪文件保留。

## 本轮确认并修复的问题

| 严重性 | 位置 | 根因及修复 | 电气影响 |
| --- | --- | --- | --- |
| P2 | 两工程 U1、本地库及嵌入符号 | 实际 Value/MPN 为 DRV8300DPWR，但库身份仍为 FD6288T、脚名沿用旧器件。统一为 DRV8300D，按 TI PW20 表更正 INHx/INLx、GVDD/GND、GLx/SHx/GHx/BSTx；补充默认封装和原厂资料链接 | 不改变物理脚号、连接、实例 MPN、封装、值或采购身份 |
| P2 | 两工程 R92 | Description 仍写 0.05%/10 ppm，而既定主料字段和预算为 0.1%/25 ppm。说明改为当前主料参数及已有 0.702% 总预算，保留老化/动态未资格边界 | 不改变电阻值、选型或阈值预算 |
| P2 | 架构及硬件总入口 | 修正仍写两层 PCB、AD PCB 未完成、底层地平面的旧描述；AD 实际清单更新为 182/162/674、171 项实装；明确峰值为瞬时正弦幅值 | 文档一致性修复 |

两块 PCB 使用 pcbnew 原生接口同步 U1 的 20 个 pad pinfunction 和 R92 Description。独立白名单文本核对与对象令牌核对均确认：其余焊盘、器件位置、角度、网络、走线、过孔、铺铜及机械内容精确保持。没有直接改写 PCB 网络以伪造图板一致。

新增 `gate_driver_symbol_errors` 检查实际实例身份、可复用库和嵌入库的全部 20 个物理引脚。测试覆盖旧器件身份、嵌入相脚错误、仅可复用库错误，以及合法换行。独立审阅发现的 lib_id 空白误报已复现并修正，最终 5 项测试通过。

AD 的保留 ADS 来源清单只更新本轮授权的四个 ADS 文件摘要；原清单逐字节归档在 `hardware/ad7606c_servo/evidence/source_manifest_before_full_schematic_audit_2026-10-23.json`。没有删除保留原方案检查。

## 功能块审阅

| 功能块 | 本轮核查及边界 |
| --- | --- |
| 输入、反接和 DC-link | 核对 LM74502 物理脚、反接管连接、F1、RSH4 与 J7 位置。ADS 保留十路阻尼电容；AD 维持用户确认的外置电容/泄放接口。外部支路保护及再生吸能尚未资格化，不能将 F1 或泄放电阻作为完整回灌保护。 |
| 12 V / 5.1 V | 核对 LM5164 引脚、反馈、RON、bootstrap 与 TPS62901 VIN/EN/MODE/VOS/FB/SS/TR。150 µH 的 12 V 总负载 1 A 条件与现有预算一致。满载启动、有效容量及温升仍须实测。 |
| 三相桥与门控 | 按 DRV8300D PW20 物理脚审查六路独立封锁、bootstrap、33 Ω 栅阻、栅源泄放和公共回路。外部与门只封锁，不生成死区；受控周期恢复没有 RTL 实现。dv/dt、SOA、实际 VGS-off 仍开放。 |
| 相电流与母线 OCP | INA240A1 相电流 REF1=VA5/REF2=GND、5 mΩ/20 V/V 对应 0.1 V/A；母线 2 mΩ/20 V/V 对应 0.04 V/A，正向名义 +25 A。核对比较器极性与独立 ARM 异步清零；不把母线电流当相电流上限，也不宣称有反向 OCP。 |
| 监督与重新武装 | 核对 U20/U23/U24/U25/U26 物理脚、开漏上拉、施密特处理、VA5 分压及故障解除不自动重武装合同。POR_OK 尚无实际 J1 反馈，快速掉电、竞争与 recovery/removal 不能用稳态模型关闭。 |
| ADS8588S | 核对串行绑带、双 DOUT、参考及 REGCAP、量程、所有物理引脚和 FPGA 约束。两路每帧 64 clocks；实际 FPGA 往返时序、滤波相移及控制环路未资格化。 |
| AD7606C | 核对 AVCC/VDRIVE 同源 VA5、三颗 TXU0204 方向/供电/OE、软件模式、四 DOUT、参考及 ADC 输入量程合同。单器件 REFIN/OUT 100 nF 与短接 REFCAPA/B 10 µF 符合原厂要求。 |
| 编码器及 FPGA | AM26LV32E 的真实引脚及 3.3 V 供电、U19 ESD、DNP 终端、5 V 编码器 PTC、J10/XDC 约定一致。实物 AX7010 2022 版本、逐针导通、线缆及终端/启动电流仍须验证。 |
| 图面与电源地 | 已查看 20 页导出图及 ADC、门驱和监督密集区域；原生图面、网格和忽略标签跳接的可见电源/GND 检查通过。全部导线、端口、连接点与实例几何保持，修改页放大复看。 |

## 新鲜证据与执行边界

设计未改变：ADS **180 元件 / 145 网络 / 634 引脚归属**；AD **182 / 162 / 674**。逐引脚比较证明所有网名、物理引脚归属、元件值、封装、MPN 和采购字段精确一致；唯一的库身份变化为已声明的 U1 FD6288T → DRV8300D。不能将此描述为库身份也完全不变。

两工程原生 ERC 均为 **0 错误 / 0 警告 / 0 排除**；原生补铜 DRC 均为 **0 错误 / 0 警告 / 0 排除 / 0 未连接 / 0 图板差异**。板级 Kelvin、保留地层、ADC 本体数字铜路、逃线与自由直角检查通过。原生版本为 KiCad 10.0.3。

全量回归：**366 项、0 失败、46 跳过**，另 pcbnew 原生 **96 项全部通过**；独立复核后新增的空白/仅库变异用例与原 3 项合并为 **5 项，全部通过**。46 跳过明确包括主解释器缺少 pcbnew、缺少 ngspice、POSIX 专用条件；原生 96 项补充的是几何通道，不补充 ngspice 或实物试验。首次测试受沙箱系统临时目录清理权限影响，已用工作区内专用临时目录复跑；没有据此修改验收规则。

ADS 的完整 verify 因缺少 ngspice 保持 `protection.qualification: NOT_RUN`，因此不能将完整 verify 写成通过。AD 的严格发布仍返回 BLOCKED，不能把零 ERC/DRC当作制造批准。中途旧清单及检查时改动硬件入口文档导致的失败记录保留；稳定源后的最终验收另行输出，不复用中途失败结果。

可随 Git 保留的 [结果摘要](full_schematic_audit_2026-10-23/summary.json)、[逐引脚核对](full_schematic_audit_2026-10-23/connectivity-proof.json)、[图面几何证明](full_schematic_audit_2026-10-23/schematic-geometry-proof.json)、[PCB 元数据限定证明](full_schematic_audit_2026-10-23/pcb-metadata-proof.json)、[ADS 修改页](full_schematic_audit_2026-10-23/ads-gate.png)、[AD 修改页](full_schematic_audit_2026-10-23/ad-gate.png)及同目录的原生 ERC/DRC 与源摘要已独立保存。

本机完整证据在 `artifacts/full-schematic-audit-20261023/`：含 `final-regression.log`、`final-current-ads/`、`final-current-ad/` 和分别导出的新鲜 BOM。它们是审核证据，**不是可直接下单的制造包**。该 artifacts 目录为忽略目录，需移交完整过程文件时应另行保存。

## 仍需关闭的条件

1. **AD 接口性能**：20 MHz 相反边沿采样的原始预算 `25−(9+15.7+10)=−9.7 ns`，还未包含负载、布线、FPGA setup/hold。5 MHz 仅为初始调试设置。须通过实际 RTL/STA、采样相位/协议设计与测量实现闭合；本次未凭空加入未经验证的高速接口改版。
2. **静态系统条件**：确定供电源阻抗与前瞻故障电流、F1 协调、外部电容/支路保护及母线 60 V（含过冲）包络；确认实际 AX7010/线束、精确器件封装、电流/热/冷却假设。缺少这些输入不能变成制造 PASS。
3. **工程首板制造**：七类源绑定责任审核、Tg155/叠构接受、Type VII 过孔填充盖帽、J1/J5 与 J4 成品孔窗口、同源 Gerber/钻孔/BOM/CPL/极性独立复核仍需闭合。旧制造包不可沿用。
4. **投板后的实物资格**：完整 OCP→VGS-off、独立供电/棕断、重武装、噪声/校准、热浸和额定电流维持 NOT_RUN。允许按工程首板边界安排制造后的测量，不将尚未造板的试验要求伪装为已完成，也不豁免制造前静态问题。

## 原厂资料

- [DRV8300 Rev.D，表 6-2 与应用/布局](https://www.ti.com/lit/ds/symlink/drv8300.pdf)
- [LM74502](https://www.ti.com/lit/ds/symlink/lm74502.pdf)、[LM5164](https://www.ti.com/lit/ds/symlink/lm5164.pdf)、[TPS62901](https://www.ti.com/lit/ds/symlink/tps62901.pdf)
- [INA240](https://www.ti.com/lit/ds/symlink/ina240.pdf)、[LM393LV](https://www.ti.com/lit/ds/symlink/lm393lv.pdf)、[TPS3890](https://www.ti.com/lit/ds/symlink/tps3890.pdf)
- [ADS8588S](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)、[AD7606C-16 Rev.A](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf)、[TXU0204](https://www.ti.com/lit/ds/symlink/txu0204.pdf)
- [嘉立创当前工艺能力](https://www.jlc.com/portal/vtechnology.html)

自动检查与独立代理复核均不能代替责任工程师的制造签核；本轮未填写任何虚假签名或厂家接受记录。
