# AD7606C 四层 PCB 审查 — 2026-10-18

状态：原生同步及布局候选；未布线，PCB 发布阻断。原理图/BOM 电气方案没有改变。

## 已完成

- 用户确认沿用原板外形、安装孔和外部接口位置，新建四层板。130 × 95 mm 板框和 H1-H4/J1/J3/J4/J5 原点/角度保持一致；J2 不属于当前原理图。
- KiCad 项目原生 F8 完成导入，预览/应用均为 0 errors / 0 warnings。独立检查随后捕获 U12.6/U13.1 的 PWR_GOOD、U5.2/U5.4 的 GND 共四个不同网归属；用新鲜 CLI 原生网表经 KiCad Import Netlist 修正。没有手工编造 PCB 网络归属。
- 最终逐焊盘一致性通过：180 个电气封装 + H1-H4，完整封装 ID、值、DNP 和每个编号焊盘的网络一致。J6 在原生 XML 中明确 exclude_from_board。
- 新工程的复制顶层文件名/UUID 元数据已修复；新增回归先失败后通过。缺板回归改用独立外部工程 fixture，新 AD7606C 配置登记真实 PCB。
- 本地原生布局运算保持所有位号、器件值、完整封装 ID、属性和焊盘网络不变；ADC 参考/去耦、电平转换器、电阻优先靠实际服务引脚。标号保持可见，未隐藏元件或删除连接。
- 已输出 [PCB 布局 PNG](pcb_placement_2026-10-18.png)、[逐元件位置](pcb_placement_2026-10-18.json) 和 [机械约束](pcb_mechanical_constraints_2026-10-18.json)。

## 规则依据

外部 Default/ANALOG/GATE/POWER 间距、线宽、全局规则及 ERC/DRC 严重级设置保持原值。
POWER 的旧页名模式改为实际 power_input 页路径，并把新增 VBUS_BRIDGE 纳入原 0.8 mm/3 mm 类。
继承原有 14 条仅限同一器件 Pad-Pad 的封装内部规则；U5 与 U2-U4 为相同 INA240 SOIC-8，增加对应 0.65 mm 内部规则。
U15 为 LM393LVDDFR 的 DDF0008A，增加同封装 U18 已使用的 0.2 mm 内部规则。
[TI LM393LV 原厂手册](https://www.ti.com/lit/ds/symlink/lm393lv.pdf) 第 56 页推荐焊盘 1.05 × 0.45 mm、节距 0.65 mm，净距 0.20 mm，与实际封装相符。
这些 16 条规则仅作用于同一位号的两个 Pad；没有 trace/via/zone 或跨器件例外，没有新增 ERC/DRC exclusion。

## 本轮验证

实际结果见 [机读摘要](pcb_acceptance_2026-10-18.json)、[原生 ERC](native_erc_2026-10-18.json) 和 [原生 DRC](native_drc_2026-10-18.json)。仅规范化 source 路径元数据，发现与未连接列表不变。

| 检查 | 实际结果 |
| --- | --- |
| 新/旧原理图对象/网络/物理脚归属 | 181/162/672；159/135/592 |
| 两工程原生 ERC | 均 0 errors / 0 warnings / 0 exclusions |
| 新板逐焊盘一致性 | PASS；180 电气封装 + 4 安装孔 |
| 原生全严重度 DRC | FAIL：0 errors / 0 warnings / 0 exclusions；499 未连接；0 图板差异 |
| 主回归 | 158 项：144 通过、14 明确跳过，退出码 0 |
| 独立 pcbnew 几何回归 | 39/39 通过；工具/保留板 fixture，不是新板布线验收 |
| 热、动态、实物、制造 | NOT_RUN / OPEN |

实际执行 `verify --project ad7606c --scope pcb` 及完整 `test --kicad-cli ... --pcb-python ...`；解释器为 Anaconda Python 3.12.4，KiCad 10.0.3。原生验证期间源摘要不变。
原生 SVG 保留于本地 artifacts；版本控制交付 PNG 和原生 PCB。
PCB 尚无走线；未连接必须作为失败保留。几何零违规不表示完整 DRC 或制造门禁通过。
原项目原理图、BOM、库、旧 PCB 和历史阻断保留，不能用旧板回归冒充新版发布验收。

## 待确定与后续工作

12 V 辅助电源的总连续/峰值负载仍需确定。现有 L1 的厂家 Irms/Isat/热资料未闭合，68 µH 不能直接保证最差条件下 1 A；0.5 A 开发限制与保证 1 A 是两种设计输入。
负载/电感封装确定后，完成电源区和关键回路评审，再按 DC-link、门极/bootstrap、Kelvin/OCP、ADC/接口、普通信号顺序布线。
没有授权自动布线关键大电流、高 dv/dt 或安全路径。最终仍要求实际全严重度 DRC 0违规/0未连接/0图板差异及独立回路/热审阅。
母线再生、OCP 到 VGS-off、快速欠压、分流器/连接器温升、接口时序和实物资格保持开放。
