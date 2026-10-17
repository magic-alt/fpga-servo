# 通用 PCB 工具与文档整理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline implementation, or superpowers:subagent-driven-development only if the user selects delegation. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将当前工具整合为可配置、多工程复用的 KiCad 开发验证工具，并整理当前文档和历史归档。

**Architecture:** 一个 CLI 调用领域模块，工程配置提供路径、能力和规则参数。公共解析及原生工具执行不依赖伺服元件；工程规则按声明加载。文档和 CI 迁移与旧入口退役作为同一交付的一部分。

**Tech Stack:** Python 3.12 标准库、unittest、JSON、KiCad 10 CLI；pcbnew/ngspice 按工作流需要使用。

**Spec:** [2026-10-17-pcb-toolkit-docs-design.md](../specs/2026-10-17-pcb-toolkit-docs-design.md)，用户已于本次对话确认书面设计。

## Global Constraints

- 本轮支持 KiCad 10 与 Python 3.12，以标准库为默认依赖。
- 支持 Windows 和 Linux，工具路径由命令参数或 PATH 提供。
- 不修改原理图、PCB、符号库、封装、BOM 选型或 FPGA 引脚定义。
- 保留现有未跟踪文件。
- 单项状态包括 PASS、FAIL、NOT_RUN、NOT_APPLICABLE；发布决策另外记录 BLOCKED。
- 必需检查失败、工具缺失、异常或超时必须导致总体非零退出。
- 默认只读检查。开发操作默认预览，写入需要显式 apply 参数；修改前备份并报告目标路径、前后摘要及差异。
- 已确认主题分支为 `refactor/docs-tools-maintenance`；仅提交本任务文件，不推送或合并。
- 后续修改仓库根 docs/tools 等目录需使用受限环境允许的提权方式；当前默认可写目录仅为 hardware，不能以此改变项目文件位置。

## Review Focus

- 仓库外工程和含空格路径：按配置位置解析，不能误用仓库工程或 shell 拼接（Task 1、4）。
- 重复实例与循环层次：同一源页允许合法多实例；不重复执行文件级规则，循环和重复实例路径须诊断（Task 2）。
- 原生工具退出零但报告残缺：空网表、缺少计数/必需字段不能 PASS（Task 4）。
- 新板卡没有 PCB 或只选择通用规则：不得引入伺服要求，也不能把请求的 PCB 检查静默略过（Task 1、3）。
- 历史哈希和采购证据：不改写历史执行事实、不用旧证据代替新运行；重构不得造成无关硬件哈希变化（Task 5、6）。

## 锁定的接口与命令

配置 `schema_version=1`；字段为 `id`、`root`、`schematic`、可选 `board`、`libraries`、`bom`、`output`、`rule_sets`、`parameters`。所有路径按配置所在目录解析 root，再按 root 解析其余路径；仅 root 可引用外部工程目录。output 不得是源文件或其父路径的覆盖目标。规则名白名单解析，不支持配置执行任意 shell/Python 字符串。

数据模型在 `project.py`：`Project`（冻结 dataclass，路径与规则参数）、`ProjectError(ValueError)`、`load_project(path: Path) -> Project`、`resolve_project(name: str) -> Project`。

数据模型在 `report.py`：`Finding(rule_id: str, status: str, message: str, details: dict)`；`RunReport(project_id: str, findings: list[Finding], evidence: dict, release_status: str)`；`exit_code(report: RunReport) -> int`。退出码为 0 自动检查通过、1 检查失败/必需项未执行、2 严格门禁阻断、64 配置或用法错误；同时失败和门禁阻断时返回 1，报告保留 BLOCKED。

领域接口：`check_schematic(project: Project) -> list[Finding]`、`check_board(project: Project, netlist: Path | None) -> list[Finding]`、`run_rules(project: Project, scope: str, inputs: dict) -> list[Finding]`、`verify(project: Project, scope: str, output: Path | None, tools: dict[str, str]) -> RunReport`。

日常入口 `python tools/pcb.py`：

- `check (--project ID | --config FILE) --scope {schematic,pcb} [--netlist FILE] [--output DIR]`
- `verify (--project ID | --config FILE) --scope {schematic,pcb,release} [--output DIR] [--kicad-cli EXE] [--ngspice EXE]`
- `export (--project ID | --config FILE) --kind {bom,procurement,netlist,pdf} [--output DIR] [--kicad-cli EXE]`
- `develop (--project ID | --config FILE) --operation {snapshot,sync} [--preview | --apply] [--output DIR]`
- `test [--pattern PATTERN]`，默认发现全部迁移测试及参考教程测试。

check 原理图作用域也运行项目声明的仓库/选型/接口静态规则；verify 在 check 基础上生成新鲜原生证据。release 始终包含严格 PCB 检查与项目定义的资格门禁。procurement 未配置采购来源时返回配置错误。snapshot 在预览时只列备份计划，apply 才生成不可覆盖的备份及清单；不修改源板。sync 在本轮只生成原生 F8 差异审阅计划，无可用同步接口时返回 NOT_RUN/1，apply 明确拒绝，不能调用旧手写修板逻辑。

## 文件与迁移映射

| 现有文件 | 目标与处理 |
| --- | --- |
| `tools/kicad_native.py` | `tools/pcbtools/kicad.py`，保留解析 API，添加原生调用封装 |
| `check_native_schematic.py`、`check_kicad_grid.py`、`check_schematic_layout.py`、`check_schematic_connectivity.py`、`check_power_wiring.py` | 公共部分进 `tools/pcbtools/schematic.py`，特定二极管/ADC/接口断言进对应 rules |
| `check_pcb_parity.py`、`check_pcb_constraints.py`、`check_pcb_corners.py` | 通用部分进 `tools/pcbtools/board.py`，板卡专属约束分离 |
| `check_vendor_lands.py`、`check_pcb_escape.py`、`check_pcb_kelvin.py` | `tools/pcbtools/rules/power_layout.py`，参数化并保留现有厂商与铜连通约束 |
| `check_design.py`、`check_selection_contract.py`、`check_legacy_pcb_baseline.py` | `tools/pcbtools/rules/servo.py`，保留原理图/严格板级作用域与历史基线判定 |
| `check_adc_serial_contract.py`、`check_ad7606c_fast_profile.py`、`check_adc_validity.py` | `tools/pcbtools/rules/adc.py`，明确两个工程规则差异 |
| `check_netlist_safety.py`、`check_ocp_behavior.py`、`gate_ab_verify.py` | `tools/pcbtools/rules/protection.py`，保留物理引脚断言、状态行为、门禁与仿真 |
| `check_public_paths.py` | `tools/pcbtools/rules/repository.py`；继续禁止输出敏感内容和本机路径 |
| `export_bom.py`、`export_procurement.py` | `tools/pcbtools/export.py`；工程/来源显式传入，默认写独立输出目录 |
| `run_gate_ab.py` | `tools/pcbtools/verification.py`；保留新鲜证据、源摘要、失败隔离与门禁语义 |
| 顶层 `tools/test_*.py` | 移至 `tools/tests/`，改为包导入，不减已有断言，不保留平行实现 |
| `repair_layout_entry_pcb.py`、`repair_legacy_pcb_routes.py`、`complete_pcb_connections.py`、`route_residual_pcb.py`、`simulate_layout_entry.py` | 移至 `tools/archive/layout_2026_10/`，记录原分支/提交与依赖；不导入日常执行图 |
| `hardware/ad7606c_servo/tools/check_project.py`、`run_checks.py` | 通用编排进 verification，AD7606C 合同进 adc/servo；更新原工程全部实际调用 |
| `hardware/ad7606c_servo/tools/build_project.py`、`build_levelshift.py` | 一次性生成工具归入 `tools/archive/ad7606c_2026_10/`，保留来源说明，不运行重生成设计 |
| `tools/ai_pcb_guide/` | 保留独立来源；更新引用公共 API，测试加入统一 test 入口 |

所有新增包建立 `__init__.py`；规则注册放在 `tools/pcbtools/rules/__init__.py`。`development.py` 管理快照和同步审阅计划。`tools/projects/{ads8588s,ad7606c,template}.json` 提供配置；模板清楚标明需替换项，不被默认测试当成有效工程。

## Task 1：配置、报告与统一入口

**Files:** 创建 `tools/pcb.py`、`tools/pcbtools/{__init__,cli,project,report}.py`、`tools/projects/{ads8588s,ad7606c,template}.json`、`tools/tests/test_toolkit_core.py`；创建 `docs/toolkit_migration.md` 记录基线与完整映射。

**Interfaces:** 产出上述 Project/Finding/RunReport API；`cli.main(argv: list[str] | None = None) -> int`。暂未迁移的命令明确失败，不返回空成功。

- [x] 先记录 Python 解释器和可用工具版本，运行现有六项检查、hardware-sanity 对应检查及旧测试；输出写临时证据目录，不修改源。依赖缺失和已知严格 PCB 失败分别记录，不作为迁移引起的失败。
- [x] 添加 `test_config_relative_to_file`、`test_unknown_key_rejected`、`test_space_and_external_root`、`test_missing_board_requested`、`test_required_not_run_is_failure`、`test_blocked_and_failed_precedence`。断言精确路径、64/1/2 退出语义及无输出覆盖；先运行确认因 API 缺失失败。
- [x] 实现冻结配置模型、严格 schema、输出冲突校验、状态归并和 CLI 参数互斥。两个配置声明真实工程能力，AD7606C 不虚构 PCB。
- [x] 运行 `python -m unittest discover -s tools/tests -p test_toolkit_core.py -v`，要求全部通过；验证 `python tools/pcb.py --help` 返回 0。
- [x] 仅暂存本任务文件并提交 `refactor(tools): add project configuration and unified CLI`。

## Task 2：原理图与公共 KiCad 解析

**Files:** 创建 `tools/pcbtools/{kicad,schematic}.py`、`tools/tests/test_toolkit_schematic.py`；迁移映射表中五项原理图检查的公共逻辑，旧入口暂留到 Task 6 统一移除。

**Interfaces:** 消费 Project/Finding；产出 `discover_sheets(project: Project) -> list[Path]`、`check_schematic(project: Project) -> list[Finding]`；保留 extract_forms、property_value 等解析函数签名供后续迁移。

- [x] 测试 `test_nested_hierarchy`、`test_missing_child_fails`、`test_cycle_fails`、`test_repeated_source_instance_allowed`、`test_duplicate_instance_path_fails`。临时第三工程不使用伺服命名；测试坏括号、偏格连接和悬空电源图例必须失败。先确认新增 API 缺失导致失败。
- [x] 抽取原检查实际逻辑，参数化尺寸/网格和工程输入。顶层执行代码改为显式函数，导入无读取设计、写文件或执行工具的副作用。
- [x] 将特定 ADC/器件断言暂注册到对应规则接口，记录每一条旧约束去向；不能借通用化删除原有物理引脚要求。
- [x] 运行新原理图测试；对两个实际工程运行原理图公共检查，并与 Task 1 的适用检查结果逐项比对。
- [x] 提交 `refactor(tools): share schematic parsing and validation`。

## Task 3：PCB 与工程规则迁移

**Files:** 创建 `tools/pcbtools/board.py`、`tools/pcbtools/rules/{__init__,servo,adc,power_layout,protection,repository}.py`；迁移相关 `tools/test_*.py` 至 `tools/tests/`，新增 `tools/tests/test_toolkit_rules.py`。

**Interfaces:** 消费 Project、Finding 和公共解析；产出 check_board/run_rules；规则注册包含稳定标识、适用作用域和必需输入，未注册规则报配置错误。

- [x] 写 `test_generic_project_has_no_servo_rules`、`test_unknown_rules_fail`、`test_explicit_adc_profiles_do_not_leak`、`test_missing_netlist_not_pass`；对旧测试改导入后先确认相应模块缺失失败。
- [x] 按映射迁移纯函数和断言，取消全局 ROOT/HW、脚本互相导入、runpy、临时修改模块常量等复用方式。把引用名、物理引脚合同和来源放入工程参数或具名规则集。
- [x] 保留旧故障注入测试：错引脚、错误分流器/封装、Kelvin 铜误接、无效 ADC、OCP 违规恢复、历史 PCB 内容变化均须被拒绝。原生依赖按需导入，普通规则不要求 pcbnew。
- [x] 运行 `python -m unittest discover -s tools/tests -v`，逐项记录尚待后续迁移的依赖；本任务拥有的规则测试全部通过。严格旧板 PCB 检查须继续报告既有阻断。
- [x] 提交 `refactor(tools): separate generic board checks from project rules`。

## Task 4：原生验证、导出与证据编排

**Files:** 创建 `tools/pcbtools/{verification,export}.py`；扩展 kicad/report/cli；迁移 `test_run_gate_ab.py`、`test_gate_ab_verify.py` 至 tools/tests；新增 `tools/tests/test_toolkit_workflows.py`。

**Interfaces:** `run_native(command: list[str], cwd: Path, timeout: float) -> dict` 返回退出码/输出/异常诊断；verify 使用已定义签名；`export_project(project: Project, kind: str, output: Path, tools: dict[str, str]) -> RunReport`。

- [x] 先添加失败测试：缺失 EXE、超时、退出零但空网表/残缺 ERC、旧输出污染、含空格程序路径、重复运行目录隔离、导出覆盖源文件。通过注入执行器测试跨平台逻辑，不把模拟结果写作真实 KiCad 通过。
- [x] 迁移 Gate A/B 和 AD7606C 新鲜导出/验收逻辑；要求非空组件/网络及完整原生结果。源摘要范围排除本次输出、缓存和敏感文件；不得读取 .env 或环境变量值用于日志。
- [x] 迁移 BOM、采购、网表和 PDF 导出；不回写受版本控制的 BOM。未配置采购输入明确报错；日期和未资格替代品的限制继续出现在采购结果。
- [x] verify schematic 对无 PCB 项目有效；pcb/release 不跳过必需板级输入；release 的 Gate A/B 与硬件证据仍为独立阻断，0 ERC 不覆盖它们。
- [x] 运行新工作流测试与已迁移门禁测试；对实际可用原生工具运行两个项目验证，逐项报告未执行条件。提交 `refactor(tools): unify native verification and evidence export`。

## Task 5：开发辅助与历史工具隔离

**Files:** 创建 `tools/pcbtools/development.py`、`tools/tests/test_toolkit_development.py`、`tools/archive/README.md`，移动映射表中历史工具；补齐 toolkit_migration 说明。

**Interfaces:** `develop(project: Project, operation: str, apply: bool, output: Path) -> RunReport`；默认 preview，snapshot/apply 创建独立快照，sync 仅提供原生审阅计划。

- [x] 写 `test_preview_changes_no_source_bytes`、`test_snapshot_is_non_overwriting`、`test_sync_apply_rejected`、`test_check_does_not_import_pcbnew_or_archive`；先执行确认失败。
- [x] 实现源/输出冲突拒绝、快照 manifest 与前后摘要；不引入未验证的自动修板或布线功能。
- [x] 将历史工具移入归档目录并记录原路径、来源提交、适用旧设计和依赖。保留历史源码作为证据，不尝试通过执行它们验证当前板卡。
- [x] 运行开发辅助测试，在临时工程上验证 apply 只产生快照，原设计摘要精确不变；提交 `refactor(tools): isolate historical board repair utilities`。

## Task 6：文档归档、CI 切换与最终验收

**Files:** 创建 `docs/{README,pcb_toolkit,pcb_toolkit_extension}.md`、`docs/archive/README.md`、`tools/tests/test_toolkit_integration.py`；更新根 README/AGENTS、docs/release_gates.md、docs/ci_schematic_scope.md、两个 hardware 项目 README、三份 .github/workflows、.agents/skills 中实际调用引用；移除已迁移旧入口。

**Interfaces:** 消费全部 CLI/API；test 默认发现 tools/tests 和 ai_pcb_guide/tests，--pattern 用于筛选，运行异常和测试发现失败非零退出。

- [x] 添加端到端测试：两个工程配置解析且不串用规则、外部第三工程通用检查、CLI 子命令退出码、工作流必需检查集合不缩减。添加当前 Markdown 本地链接与有效入口引用检查，历史执行事实不强制改写。
- [x] 在 docs/toolkit_migration.md 完成逐文件归档映射。优先归档已被替代的 2026-10-09/10 修复过程和完成的旧计划；当前采购/接口/时序/冻结/门禁说明保留。引用先确认再移动，不按日期批量归档。
- [x] 保留 reviews/sourcing 原始证据路径与内容；历史报告移动后修复相对链接，并加历史标识及当前入口。release_gates 当前区移除与新选型矛盾的历史勾选展示，将原记录链接到归档，开放门禁不改为完成。
- [x] 所有 CI 和当前文档改用统一入口。CI 保留 schematic 与严格 release 区别；完整 test 执行所有原有回归及新增通用性测试。更新技能引用只修调用路径，不改其电气审批要求。
- [x] 删除重复旧实现和临时包装入口，检查源码及配置实际引用无旧路径；仅历史档案允许保留旧命令并标明历史语义。
- [x] 执行 `python tools/pcb.py test`、两个项目 `check --scope schematic`、可用原生 `verify --scope schematic`；严格 ADS8588S release 单独记录既有失败和 BLOCKED，不以通过为预期。
- [x] 比较 Task 1 基线清单、检查发现项及输入哈希。运行 `git diff --check`，检查原理图/PCB/库/封装/BOM/XDC 未改动、hardware/.history 未纳入，记录实际工具版本与每项未执行边界。
- [x] 提交 `docs(tools): migrate CI and document reusable PCB workflows`；交付分支、迁移统计、实际检查结果与剩余发布阻断，不推送或合并。

## 计划自审与执行交接

设计的配置、通用检查、规则隔离、原生证据、导出、开发保护、文档归档和完整验收分别落在 Task 1–6。上面的五类 Review Focus 均有具名失败测试。计划中的临时不完整模块只存在于实现过程，最终交付不保留空壳命令或并行旧入口。

推荐由当前代理在本会话顺序实施：各任务共享模型和迁移接口，顺序推进可减少并行修改冲突。用户也可选择分任务代理实施与审阅；未选择前不启动子代理。计划审阅通过并选定方式后再执行。

## 执行完成

全部六项任务完成；实际验证、独立审阅修复和环境边界见 [迁移记录](../../toolkit_migration.md)。按已批准范围保留本地主题分支，不推送或合并。
