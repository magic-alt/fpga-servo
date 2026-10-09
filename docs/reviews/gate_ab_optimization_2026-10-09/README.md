# Gate A/B 验证流程优化 — 2026-10-09

基于远端 `feat/gate-ab-electrical-verification-20261009` 的 `389fbb5`；被测实现提交 `80512b5`。优化分支 `fix/gate-ab-evidence-integrity-20261009`。未修改硬件、FPGA、BOM 或库；原 main 工作区未提交配置和 history 保留。

## 修复与复核

- 清除预期波形后才执行模拟器；旧波形 + 空操作程序不再 PASS。
- 拒绝损坏、非有限值、时间倒序和覆盖不完整的波形。
- 缺失输入、畸形 XML、模拟器失败均输出 FAILED，覆盖旧资格 JSON。
- 网表脚本 ERC 明确 NOT_RUN；统一入口原生 ERC 报告才构成 ERC 证据，校验 metadata、完整层次 UUID、显式 violations 数组。
- 每次创建独立运行目录，保存源码前后哈希、产物哈希、工具版本、Git SHA/工作区状态、各步退出码和日志；CI 复用入口。
- 独立代码审查指出的畸形 XML/不完整 ERC 报告问题，均先通过 CLI 回归复现后修复，并通过复审。

## 本机新执行结果

macOS、Python 3.12.15、KiCad 10.0.3、ngspice 47。

| 验证 | 新结果 |
|---|---|
| 六项仓库检查 | 全部 PASS |
| 原生 ERC | 0 错误 / 0 警告 / 0 排除；4 类继承 ignored checks 如实保留，未改变规则 |
| 新原生板级网表 | 157 元件 / 166 网络 |
| 安全连接、PCB parity、PCB constraints | PASS |
| OCP 稳态数字回归 | 531 场景 PASS；不代表模拟链路响应验证 |
| Gate A/B 回归 | 18 项 PASS，无跳过；包含新鲜网表 mutation 和真实 ngspice |
| 入口失败隔离回归 | 2 项 PASS |
| PCB / 教程审计回归 | 11 / 4 项 PASS |
| 理想被动模型 | 回馈电容规律与 OCP RC 门限越过互检 PASS；无主动器件模型资格声明 |
| 源码哈希 | 各次运行前后精确一致 |
| 普通入口 | 自动证据 PASS，退出 0（提交前同一实现执行） |
| `--strict-gates` | 自动证据 PASS，Gate A/B BLOCKED，退出 2 |
| `--with-drc` | FAILED，退出 1；DRC 进程退出 -5，没有新 DRC 报告 |

DRC 日志：`Swift/SwiftNativeNSArray.swift:78: Fatal error: Array index out of range`。带 parity/refill 与最简原生命令均复现；根因尚未确定。未安装/升级工具或更改全局配置进行规避，未用历史 271/478 计数替代新执行结果。制造状态保持未放行。

## 证据

- [严格门禁 manifest](strict/manifest.json)、[本次 ERC](strict/erc.json)、[资格计算](strict/qualification.json)
- [Gate A/B 回归日志](strict/gate_ab_regressions.log)、[PCB 回归](strict/pcb_regressions.log)、[教程回归](strict/tutorial_regressions.log)
- [DRC 失败 manifest](drc/manifest.json)、[原生崩溃日志](drc/drc.log)

此目录保存精选原始报告，manifest 中保留完整运行全部产物的哈希。完整原始运行（含新导出网表与 SPICE 波形）分别位于隔离工作区的 `artifacts/gate-ab/20261009T153147Z-ys3wvk8b` 与 `artifacts/gate-ab/20261009T153206Z-k4xtcjo3`；可用 `python3.12 tools/run_gate_ab.py` 重新生成独立证据。入口失败隔离回归另用 `python3.12 -m unittest discover -s tools -p test_run_gate_ab.py -v` 执行。

Gate A/B 工程门禁仍 BLOCKED；主动器件动态模型、ADC 欠压许可、回馈策略、总关断时间及台架实测等清单见 [资格说明](../../gate_ab_verification_2026-10-09.md) 和 [release gates](../../release_gates.md)。远端 CI 尚未运行本地优化提交。
