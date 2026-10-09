# 全工程原理图表达优化与复查

日期：2026-10-09。分支：`fix/ocp-latch-industrial-review`。原生 KiCad 10.0.3，A4 横向，一张总览和七张子页。此记录接续已有 Gate Driver / Current Sense 重排，保留并提交本次任务开始时已有的相关原理图修改。

## 最终图面

[八页原理图 PDF](reviews/schematic_full_review_2026-10-09.pdf)。每页标题栏显示 `Id: 1/8` 至 `Id: 8/8`，总览功能框补充对应页码导航。

- System：统一短线标签朝向和外侧留白；两段靠标签连接的 GND 短线补上可见导线，消除重复文字而保持原有网络。
- DC Input：将 VBUS_DIV_MID 标签引到分压电阻上方，缩短页脚，避开标题栏。
- AX7010 Interface：左侧层次端口向内移动并调整字体，改善页框余量和密集信号文字。
- Auxiliary Power：减少与层次端口相邻的重复标签；将 PWR_GOOD 引到 U13 上方的空白区。
- Current Sense 与 Gate Driver：保留上一轮统一的三相/三通道排列、本地自举/栅极/滤波导线；普通电阻隐藏数字引脚名称以减少拥挤，物理编号和网络映射保留。
- Encoder：缩短侵入标题栏的注释；U19 的 5、10 接地物理脚分开绘制并用原生导线相连，库与嵌入定义同步。
- OCP Latch：移开与顶部电源文字拥挤的 CT 注释，页脚保持在安全区域。

已逐页查看最终渲染，以及总览端口、输入分压、接口端口、PGOOD、ESD、复位监控、ADC 引脚、栅极回路和 OCP 页脚放大图。MOSFET 同功能封装叠放焊盘保留原符号表达及映射；此审查关注功能可读性和连接保持。

## 页码与图标

KiCad 10 工程管理器的绿色勾表示 Git 已跟踪文件没有修改，红色空心圈表示未提交修改；这不是电气/ERC 状态。提交后可以刷新工程管理器确认图标。

源文件的根页实例为 1，各子页实例为 2–8，页数和顺序完整。本次原生全层次 PDF 八页页码全部正确。没有检查或修改用户正在运行的编辑器本地显示偏好，因此不能宣称编辑器的显示问题已复现或修复。

从 `.kicad_pro` 打开工程根图，再通过层次导航进入子页。编辑器内页框/标题栏不可见时，检查 Appearance 面板的 Drawing Sheet 可见性；层次树不可见时检查 View → Panels → Hierarchy Navigator。绘图导出时启用 Plot drawing sheet。若仍有问题，应根据实际 UI 区分页框显示、层次导航、缩放或打开上下文，不应盲目重写已正确的页码。

官方说明：[Project Manager Git integration](https://docs.kicad.org/10.0/en/kicad/kicad.html)、[Schematic hierarchy / appearance / plotting](https://docs.kicad.org/10.0/en/eeschema/eeschema.html)。

## 新鲜验证

- 原生 XML 前后：159 元件、180 网络、648 项物理引脚网络归属，身份/数值/封装/网名/每项 ref-pin 精确一致。
- 面向 PCB 的原生网表：157 元件、179 网络；系统 BOM 159 元件，已重新导出。
- 原生 ERC：0 错误、0 警告、0 排除；修改前后 ignored_checks 一致，未降低严重级别。继承的四项 ignored checks 为 single_global_label、four_way_junction、simulation_model_issue、footprint_filter；零违规仅指当前策略下的结果。
- 五项仓库回归全部通过：check_native_schematic、check_kicad_grid、check_schematic_layout、check_schematic_connectivity、check_design。
- check_netlist_safety 通过；check_ocp_behavior 通过 531 个稳态数字场景。
- 项目符号库所有物理脚号、脚名、电气类型和形状保持一致；U19 仅修改 pin 10 图形位置，新增导线由网表精确比较验证。
- PCB SHA-256 未变：`581f590151e439a771ab280e0449887680f917d3f7b9451c74a67d4b1b849eec`。

机器证据：[视觉记录](../.pcba-workflow/schematic-visual-audit.json)、[源文件/网表/PDF/ERC 哈希和页码证明](../.pcba-workflow/schematic-presentation-proof.json)。基线快照、网表、ERC 及 PNG 位于本地忽略目录 `artifacts/schematic_full_review/`；最终 PDF 已纳入 Git，可远端审阅。

## Skill 沉淀

采用项目本地 [schematic-humanizer](../.agents/skills/schematic-humanizer/SKILL.md)，新增 [配线与页码实践](../.agents/skills/schematic-humanizer/references/practical-wiring-and-pages.md)，覆盖重复通道节距、局部导线与标签边界、近邻线岛反例、文字完整范围、页码与 Git 状态诊断。[验证记录](schematic_humanizer_skill_validation_2026-10-09.md)。

参考 [TI TIDA-00913 原理图](https://www.ti.com/lit/pdf/TIDROJ7) 的功能分组画法；没有移植其参数。Skill 来源及原许可证保留：[upstream](https://github.com/Keitark/pcba-design-skills/blob/main/.agents/skills/schematic-humanizer/SKILL.md)。

本次不改变电气方案，不执行 PCB 同步或布线，未运行新的 PCB DRC。已有 PCB 外置熔断器同步差异、OCP 模拟时序、再生能量、热设计和实物验证仍按 [release_gates.md](release_gates.md) 保持开放；本次通过不等于制造发布。
