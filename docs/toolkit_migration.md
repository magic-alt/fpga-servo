# PCB 工具迁移记录

状态：实施完成，保留主题分支供审阅。设计与计划见 docs/superpowers 对应 2026-10-17 文件。

## 迁移前基线

Python 3.12.4；原生工具不在 PATH，后续使用显式本机参数验证，不把安装路径写入公共文档。

| 检查 | 退出码 |
| --- | --- |
| check_native_schematic | 0 |
| check_kicad_grid | 0 |
| check_schematic_layout | 0 |
| check_schematic_connectivity | 0 |
| check_power_wiring | 0 |
| check_adc_serial_contract | 0 |
| check_ad7606c_fast_profile | 0 |
| check_design | 0 |
| check_legacy_pcb_baseline | 0 |
| check_public_paths | 0 |
| tests | 1 |

旧测试发现 104 项，6 failures、3 errors、26 skipped；其中 ADC validity 缺少新鲜 XML。完整日志保存在本次本地临时证据中，不把这些失败当作迁移后引入。

## 入口迁移映射

完整映射以 [实施计划](superpowers/plans/2026-10-17-pcb-toolkit-docs.md#文件与迁移映射) 为准，交付时补充最终状态。

## 当前实施结果

顶层日常 Python 入口由 43 个文件收敛为 `tools/pcb.py`；实际逻辑迁入配置、共享解析、原理图、PCB、导出、验证、开发及五个领域规则模块。旧包装入口已移除，旧测试进入 tools/tests，七个一次性生成/修板/布线工具进入 tools/archive。

30 份被替代的修复记录、旧计划和技能过程记录移入 docs/archive，旧门禁完整快照另行保留。采购/审查原始证据未移动。当前 Markdown 链接（含归档）已核对；当前技能与 CI 使用统一入口，历史记录中的原执行命令按历史事实保留。

两个工程的源静态检查均通过。实际 KiCad 10.0.3 新鲜 XML：ADS8588S 159 系统对象/135 网络，AD7606C 181/162；两工程全严重度 ERC 都是 0 errors/0 warnings/0 exclusions。原有四类项目 ignore 设置未改变。AD7606C 完整原理图工作流通过；ADS8588S 原生检查通过，但所需 ngspice 可执行程序不可用，理想模型阶段明确未执行，完整工作流非零退出。

主解释器 Python 3.12.4；KiCad 自带 Python 3.11.5 单独执行 pcbnew 几何回归。未执行 Linux CI、实物上电、台架、热与动态资格；它们不属于本次脚本重构通过证据。

最终回归：主套件发现 157 项，143 通过、14 明确 skipped；另用实际 pcbnew 解释器运行 39 项 PCB 几何回归，39/39 通过。主套件通过不将 skipped 算作已执行。旧测试方法清单对比无丢失。电气源、BOM、封装及 FPGA 定义按迁移前 SHA-256 逐文件核对，未发现变化；hardware README 与工具目录的迁移是本次授权的说明/结构变化。

## 完整旧入口去向

| 原入口 | 当前实现或历史归档 |
| --- | --- |
| `hardware/ad7606c_servo/tools/build_levelshift.py` | `tools/archive/ad7606c_2026_10/build_levelshift.py` |
| `hardware/ad7606c_servo/tools/build_project.py` | `tools/archive/ad7606c_2026_10/build_project.py` |
| `hardware/ad7606c_servo/tools/check_project.py` | `tools/pcbtools/rules/adc.py` |
| `hardware/ad7606c_servo/tools/run_checks.py` | `tools/pcbtools/verification.py` |
| `tools/check_ad7606c_fast_profile.py` | `tools/pcbtools/rules/adc.py` |
| `tools/check_adc_serial_contract.py` | `tools/pcbtools/rules/adc.py` |
| `tools/check_adc_validity.py` | `tools/pcbtools/rules/adc.py` |
| `tools/check_design.py` | `tools/pcbtools/rules/servo.py` |
| `tools/check_kicad_grid.py` | `tools/pcbtools/schematic.py` |
| `tools/check_legacy_pcb_baseline.py` | `tools/pcbtools/rules/servo.py` |
| `tools/check_native_schematic.py` | `tools/pcbtools/rules/servo.py` |
| `tools/check_pcb_constraints.py` | `tools/pcbtools/rules/power_layout.py` |
| `tools/check_pcb_corners.py` | `tools/pcbtools/board.py` |
| `tools/check_pcb_escape.py` | `tools/pcbtools/rules/power_layout.py` |
| `tools/check_pcb_kelvin.py` | `tools/pcbtools/rules/power_layout.py` |
| `tools/check_pcb_parity.py` | `tools/pcbtools/board.py` |
| `tools/check_power_wiring.py` | `tools/pcbtools/schematic.py` |
| `tools/check_public_paths.py` | `tools/pcbtools/rules/repository.py` |
| `tools/check_schematic_connectivity.py` | `tools/pcbtools/schematic.py` |
| `tools/check_schematic_layout.py` | `tools/pcbtools/schematic.py` |
| `tools/check_selection_contract.py` | `tools/pcbtools/rules/servo.py` |
| `tools/check_vendor_lands.py` | `tools/pcbtools/rules/power_layout.py` |
| `tools/complete_pcb_connections.py` | `tools/archive/layout_2026_10/complete_pcb_connections.py` |
| `tools/export_bom.py` | `tools/pcbtools/export.py` |
| `tools/export_procurement.py` | `tools/pcbtools/export.py` |
| `tools/gate_ab_verify.py` | `tools/pcbtools/rules/protection.py` |
| `tools/kicad_native.py` | `tools/pcbtools/kicad.py` |
| `tools/repair_layout_entry_pcb.py` | `tools/archive/layout_2026_10/repair_layout_entry_pcb.py` |
| `tools/repair_legacy_pcb_routes.py` | `tools/archive/layout_2026_10/repair_legacy_pcb_routes.py` |
| `tools/route_residual_pcb.py` | `tools/archive/layout_2026_10/route_residual_pcb.py` |
| `tools/run_gate_ab.py` | `tools/pcbtools/verification.py` |
| `tools/simulate_layout_entry.py` | `tools/archive/layout_2026_10/simulate_layout_entry.py` |
| `tools/test_ad7606c_fast_profile.py` | `tools/tests/test_ad7606c_fast_profile.py` |
| `tools/test_adc_serial_contract.py` | `tools/tests/test_adc_serial_contract.py` |
| `tools/test_adc_validity.py` | `tools/tests/test_adc_validity.py` |
| `tools/test_ci_scope.py` | `tools/tests/test_ci_scope.py` |
| `tools/test_gate_ab_verify.py` | `tools/tests/test_gate_ab_verify.py` |
| `tools/test_pcb_checks.py` | `tools/tests/test_pcb_checks.py` |
| `tools/test_pcb_corners.py` | `tools/tests/test_pcb_corners.py` |
| `tools/test_pcb_escape.py` | `tools/tests/test_pcb_escape.py` |
| `tools/test_pcb_kelvin.py` | `tools/tests/test_pcb_kelvin.py` |
| `tools/test_pcb_kelvin_review.py` | `tools/tests/test_pcb_kelvin_review.py` |
| `tools/test_public_paths.py` | `tools/tests/test_public_paths.py` |
| `tools/test_run_gate_ab.py` | `tools/tests/test_run_gate_ab.py` |
| `tools/test_vendor_lands.py` | `tools/tests/test_vendor_lands.py` |

## 最终原生与导出结果

- AD7606C 完整原理图流程：PASS；181 系统对象/162 网络/672 物理脚，ERC 0/0/0。
- ADS8588S：159 系统对象/135 网络/592 物理脚，ERC 0/0/0；ngspice 不可用，所需理想模型 NOT_RUN，完整流程退出 1。
- 严格 ADS8588S release 实际运行到原生 DRC：一般 violations 0 errors/0 warnings、unconnected 0、schematic parity **222**。严格规则另有 J2、驱动器/分流器/封装/网络类等已知差异，发布 BLOCKED；缺少 RSH4 的 Kelvin 审计明确 FAIL。没有修板或降低严重级别。
- 两工程真实 BOM 导出分别为 159/181 行且唯一位号数相同；多单元 AD7606C 未重复计数。采购导出通过，未更新库存快照或覆盖原始表。
- 两工程验证及严格 release 的前后源摘要相同；电气源全量 SHA-256 对比未改变。当前及归档 Markdown 本地链接检查无缺失。

本地完整执行日志及原生报告在 `artifacts/toolkit-validation/`，该目录按仓库策略忽略，不是已发布或随仓库提交的证据。复现命令见工具说明；本次未执行 GitHub/Linux CI 或硬件测试。

## 独立审阅与处理

完成一次独立只读审阅。四项 Important（PCB 路径导入、显式 native 通道误跳过、重复层次 BOM 漏件、无物理节点网表误通过）分别先用失败测试复现，再修复并通过最终全套。审阅提出的本地库快照遗漏按恢复可靠性提升为 Important，同样通过 RED→GREEN；无延期的小问题。

实施取舍：按用户确认在现有主题分支原地完成，保留原未跟踪目录；历史版本合同保留在显式选用的领域规则中，公共层不依赖伺服位号；主 Python 使用 3.12，pcbnew 使用匹配 KiCad 的 3.11.5 解释器；测试增加 static/all/native 通道，依赖缺失显式报告。若不使用 native 通道，几何回归只能算未执行。

审阅未判断的部分分别处理为：Linux/GitHub Actions 与实物资格未执行；原生 ERC/DRC 已由实际本机工具执行；历史断言保留通过源码迁移和原有负向测试清单核对；审阅后修改用对应失败回归及全套验证，不再追加第二轮审阅。未来新电路仍需自己的物理合同和实测资格，不能把现有伺服合同套用到任意板卡。
