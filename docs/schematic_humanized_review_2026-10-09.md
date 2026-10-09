# Gate Driver / Current Sense 原理图重排复查

日期：2026-10-09。分支：`fix/ocp-latch-industrial-review`。

本轮修改原生 `hardware/gate_inverter.kicad_sch`、`hardware/current_adc.kicad_sch` 和项目符号库。保留已有未提交工作，不修改 PCB。

## 网上参考与 Skill

- [TI TIDA-00913 原理图](https://www.ti.com/lit/pdf/TIDROJ7)：参考其重复三相功能块、局部去耦和清晰电源/地表达。只借鉴画法，没有移植其电路参数。
- [KiCad KLC S4.2](https://klc.kicad.org/symbol/s4/s4.2/)：按逻辑功能分组引脚。
- [schematic-humanizer](https://github.com/Keitark/pcba-design-skills/blob/main/.agents/skills/schematic-humanizer/SKILL.md)：已安装到 `.agents/skills/schematic-humanizer/`，采用其原始快照、局部完整连线、放大审图和精确网表比对流程。

## 图面调整

Gate Driver：PWM 互锁三路纵向对齐；FD6288T 输入在左、驱动输出在右；U/V/W 三相功率级采用相同方向与间距。各相自举、栅极电阻、栅源下拉、MOSFET 和四端分流电阻在块内直接连接，长距离驱动信号使用匹配标签。修正标签压到下拉电阻、栅极电阻字段及开关节点附近文字拥挤。

Current Sense：三个 INA241 通道统一排列，输出电阻与滤波电容直接连接。窗口比较器上下分组，阈值电阻相邻放置，移开压到电阻的阈值标签。ADS8588S 按模拟输入在左、数字接口在右、电源在上、地与接地配置脚在下重画符号；参考电容贴近对应引脚，REFCAPA/B 保留两个独立物理引脚并分开显示。

电源箭头和地标记是项目库中的图形标记（可见连接点为被动引脚），配合明确的本地网络标签；它们不引入隐含全局电源合并，且不进入 BOM/PCB。跨页仍保留当前层次端口，本轮没有执行全工程 global label 迁移。

## 验证结果

- KiCad 10.0.3 原生 XML 网表：前后均为 **159 元件 / 180 网络 / 648 项引脚网络归属**，元件身份、数值、封装、网名与每项 ref/pin 归属精确一致。
- 面向 PCB 的原生网表：**157 元件 / 179 网络**。与 XML 的统计口径不同，系统包含外置连接对象。
- 修改前和修改后的原生 ERC：**0 错误 / 0 警告**；忽略检查列表一致，没有新增排除或降低严重级别。
- 五项仓库检查全部通过：native schematic、grid、schematic layout、schematic connectivity、design。
- 原生网表安全检查通过；OCP 稳态数字行为 **531 场景通过**。
- 两页功能块物理导线检查通过：Gate Driver 82 个块内网络组、157 个已连接物理引脚；Current Sense 66 个组、159 个引脚。该检查不通过标签合并局部导线岛，确认附近无源器件实际接入所属局部电路。
- 原元件属性、实例 UUID、引脚 UUID、DNP/板载标记保持一致；符号物理引脚编号、名称、电气类型和形状不变；修改符号的嵌入定义与项目库定义一致。
- PCB SHA-256 保持 `581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`。

## 阅读与证据

- 两页阅读 PDF：`artifacts/schematic_humanized/Gate_Driver_Current_Sense_review.pdf`
- 全八页 PDF：`artifacts/schematic_humanized/final.pdf`
- 修改前 PDF/原生快照：`artifacts/schematic_humanized/before.pdf`、`before/`、`before_project/`
- 精确比对输入：`before.xml`、`final.xml`；ERC：`before_erc.json`、`final_erc.json`
- 属性/符号保护证明：`presentation_proof.json`；局部导线证明：`local_wiring_proof.json`
- 视觉记录及证据哈希：`.pcba-workflow/schematic-visual-audit.json`

以上证据位于本地忽略的 `artifacts/`，并非已提交到 Git。渲染全部八页并检查两页的七处密集区域；两页目标区域通过本轮视觉检查，美观程度仍供用户复核。其他未修改页面已有的重复文字、局部标签拥挤及页脚触及标题栏等问题在视觉 JSON 中记录，全工程视觉验收尚未关闭。

本轮只调整表达与图形，不代表新增电气设计批准。OCP 时序、功率/热设计、封装和实际 AX7010 接口验证继续遵循 `docs/release_gates.md`。未运行 PCB 布局、布线或制造发布。
