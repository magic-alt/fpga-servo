# AI PCB 本地技能与验证环境 — 2026-10-09

后续更新：用户已确认 AX7010 2022 / J10，F1 已选择外置 KLKD025.T + LPSM0001Z；新增原理图优化后的板级网表为 157/179，PCB 暂不修改。下文 158/180 和 parity PASS 是部署当时的历史基线；当前结论见 [原理图优化记录](schematic_optimization_2022_j10_2026-10-09.md)。

## 安装结果

从用户提供的 `AI_PCB_fpga_servo_engineering_guide_V1.0.zip` 安装四个项目技能到 `.agents/skills/`：`kicad-audit`、`kicad-schematic`、`kicad-layout`、`kicad-release`。保留现有 `fpga-servo-kicad-repair`；根目录 AGENTS.md 与用户指示优先。技能下轮会话可被自动发现，也可显式指定名称。

教程辅助脚本、测试和评审模板位于 `tools/ai_pcb_guide/`，来源及原始/安装后 SHA256 见其中的 `source_manifest.json`。ZIP CRC 完整性检查通过。不覆盖根 AGENTS.md、全局 MCP 配置、教程 HTML/PDF 或 hardware/.history/。

实际可用工具：

- KiCad CLI：`D:/Software/KiCad/10.0/bin/kicad-cli.exe`，10.0.3。
- KiCad Python：`D:/Software/KiCad/10.0/bin/python.exe`，已验证 `import pcbnew` 与版本 10.0.3。
- 默认 `python`：3.13.9。本次所有检查在它上面通过；CI 固定 3.12，本次没有验证本地 3.12。`py` 启动器不可用。
- 现有 KiCad MCP 可读取本工程 Windows 路径，`get_pcb_statistics` 调用成功。当前工具集合包含分析、ERC/DRC、报告/渲染/制造导出及部分原理图编辑能力；不能把工具包提及的另一 MCP 的同步或自动布线能力视为已安装。同步可使用 KiCad GUI F8，编辑可使用经验证的原生 pcbnew。

Windows 受限命令工具当前出现 `helper_unknown_error: setup refresh had errors`；只读与项目内部署/验证通过受审查的沙箱外命令完成。这是执行环境问题，未修改沙箱设置，也未读取环境变量或 .env。

## 可重复执行

在仓库根目录 PowerShell 中执行：

```powershell
& .\tools\ai_pcb_guide\scripts\run_kicad_qa.ps1
```

可用 `-KiCadCli`、`-PythonExe`、`-ProjectRoot` 显式覆盖路径；默认 KiCad 路径已适配本机。入口运行原生 ERC、XML 与原生网表导出、教程静态审计、五项仓库检查、11 项 PCB 回归、安全连接、531 项 OCP 稳态场景、逐焊盘 PCB 一致性和机械/网络类约束，再运行全部严重级别的原生 DRC（含一致性检查与内存铺铜更新）。无 `--save-board`，不保存 PCB；不改严重级别或排除项。

报告位于 `artifacts/pcb-qa/`，每步退出码见 `step_exit_codes.json`。存在违规时整体应失败，不能当作部署失败忽略，也不能将辅助静态审计当作制造资格。导出失败时不使用历史网表继续证明通过。Bash 脚本仅是补充 ERC/DRC 入口，路径已调整，本机未执行验证。

四个技能的格式验证命令（Windows 需 UTF-8）：

```powershell
python -X utf8 C:/Users/GCB002/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/kicad-audit
```

对另外三个技能分别运行相同命令。四项均通过；这只验证技能格式，不能证明任何自动布线或制造能力。

## 工具包兼容性修复

真实工程端到端验证发现教程审计只能读取旧版顶层 `(net code "name")` 表。本工程 KiCad 10 使用焊盘/走线/区域内嵌 `(net "name")`，因此原脚本误报 PCB 0 网络。另有 XML 与 PCB 对层级名中的 `/` 和 `{slash}` 表示差异，导致 27 个网络误报缺失。

增加两个回归测试，分别先验证旧代码失败，再修正遍历与名称规范化。原两项测试保留，共四项通过。遍历尊重引号，避免将封装描述字符串当网络。实际静态审计现在无缺失位号、无空封装、无多余电气位号、无缺失网络名。

静态脚本计 194 个非空 PCB 网络名称；MCP 的 195 包括空网络。原理图的 180 网络不同于 PCB 的名称集合：板上仍保留旧铜网络。逐焊盘一致性与原生 DRC 才是同步的主证据，较大的 PCB 网络数不是修复完成的证据。

## 本轮继续修复的实际基线

分支 `fix/ocp-latch-industrial-review`；源提交 `fb23c912807207f4ac4d6655744e02e941d80c5e`。本轮未改电气设计文件，未切换分支、提交、推送或合并。

| 检查 | 最新结果 |
|---|---|
| 原生网表 | 158 元件 / 180 网络 |
| PCB | 158 电气 + 4 机械封装，20 段走线，0 过孔，5 区域定义 |
| ERC | 0 错误 / 0 警告 / 0 排除 |
| 逐焊盘及原生同步检查 | PASS；原生一致性问题 0 |
| 仓库五项检查、安全/OCP/PCB 约束 | PASS |
| 既有 PCB 回归 / 教程回归 | 11 / 4 项通过 |
| 原生 DRC | 271 违规（220 错误 / 51 警告），另有 466 项未连接 |

DRC 类型：113 clearance、88 solder_mask_bridge、43 isolated_copper、17 shorting_items、8 track_dangling、2 tracks_crossing。五项继承的忽略检查仍需发布前审查，没有新增忽略项。

教程的 124 元件、32 封装、102 缺失位号是旧基线，不能据此重新替换当前已修复的 U19、分流器或 BOM。Gate 1/2 的同步部分已有通过证据；封装生产资格、Gate 3/4 布线和 Gate 5 制造验收仍未关闭。

## 下一阶段

继续沿用 `docs/pcb_repair_progress_2026-10-09.md` 与 `docs/release_gates.md`，不得把本次环境部署当作全部硬件修复完成。

1. 明确实物 AX7010 板卡版本/接口位号与逐针验证、F1 外置还是板载及其实际型号。这两个输入已向用户请求，未假设答案。
2. 核定剩余器件制造尺寸、铜厚/电流温升与细间距焊盘间隙冲突规则；保持板框和机械特征。
3. 保存板级快照，逐一审计旧铜的真实起止焊盘，只以验证过的同网替代路径替换。按 DC-link/半桥、栅极/bootstrap、Kelvin、OCP、ADC/编码器顺序推进，保留新鲜 DRC 与两面视觉证据。不能仅删旧铜来降低错误数。
4. 未连接和阻塞 DRC 清零且所有释放门禁关闭后，才评审制造输出与样机验证。

本轮实际修复对象是 AI 审计工具的两处兼容性缺陷，并建立可重复的本地检查入口；完整 PCB 布线仍未完成。
