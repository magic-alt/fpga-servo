# PCB 工具使用

从仓库根目录运行 `python tools/pcb.py --help`。主工具使用 Python 3.12 标准库；原生流程需要 KiCad 10。没有额外 pip 依赖。工具路径通过 PATH 或显式命令参数提供，公共文档不保存本机安装路径。

## 选择工程与工作流

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope pcb
python tools/pcb.py verify --project ads8588s --scope schematic
python tools/pcb.py verify --project ads8588s --scope release
```

`--project` 选择仓库配置；`--config path/to/project.json` 接入其他工程，二者互斥。路径相对配置文件解析，支持仓库外工程及空格。项目配置见 [tools/projects](../tools/projects)。

check 运行静态源检查和启用的领域规则；pcb 作用域需要 `--netlist` 提供新鲜 KiCad S-expression 网表。verify 自行导出新鲜 XML/原生网表，运行全严重度 ERC、物理引脚规则并导出 PDF；pcb/release 还要求实际 PCB、原生 DRC 和严格规则。板卡缺失不会被静默跳过。

AD7606C 配置明确指定 ADS8588S 参考配置，验证保留电路等价性、原方案回归和两工程 ERC。ADS8588S 自动证据还要求 ngspice 运行已有理想模型，程序缺失会返回非零。理想模型和数字稳态场景不是模拟动态或台架资格。

原生命令参数示例：`--kicad-cli <executable>`、`--ngspice <executable>`。参数是可执行文件路径，不是 shell 命令串。

## 导出与开发辅助

```sh
python tools/pcb.py export --project ads8588s --kind bom
python tools/pcb.py export --project ads8588s --kind procurement
python tools/pcb.py export --project ad7606c --kind netlist
python tools/pcb.py export --project ad7606c --kind pdf
python tools/pcb.py develop --project ads8588s --operation snapshot
python tools/pcb.py develop --project ads8588s --operation snapshot --apply
python tools/pcb.py develop --project ads8588s --operation sync --preview
```

BOM 通过 KiCad 新鲜 XML 按已注释的实际元件实例导出，正确处理重复层次和多单元器件；因此 BOM 导出也需要 KiCad 10。导出默认写独立证据目录，不更新受版本控制的 BOM。采购导出要求工程声明采购数据目录和 BOM；输出保留日期、未资格替代品与未解决物料。它不刷新供应商库存，也不代表可下单批准。

snapshot 默认预览；apply 只生成不覆盖的项目源副本和 SHA-256 清单，包括本地符号/封装、库表及显式配置的附加源文件。系统安装库、远端依赖和未声明文件不包含在快照中。sync 当前输出原生 F8 审阅步骤，状态为 NOT_RUN，退出非零；没有自动同步后端，apply 被拒绝。历史修板/布线工具在 [tools/archive](../tools/archive/README.md)，不属于当前工作流。

## 回归测试

```sh
python tools/pcb.py test --lane static
python tools/pcb.py test --kicad-cli kicad-cli --ngspice ngspice
python tools/pcb.py test --pattern test_toolkit_core.py
python tools/pcb.py test --lane native --pcb-python <KiCad-python-executable>
```

默认 all 通道导出新鲜 XML，再运行全部迁移测试和独立参考教程测试；必需原生输入不能生成时返回非零。static 通道运行不依赖新鲜 XML 的检查，原生依赖以 skipped 明示。native 通道运行 pcbnew PCB 几何回归；未指定解释器时要求当前解释器有 pcbnew。也可以在 all 通道追加 `--pcb-python` 执行独立几何通道。KiCad 自带 Python 的版本可能不同于主 Python，只用于匹配 pcbnew 的几何通道。

`--pattern` 选择测试文件，不用于禁用工程必需规则。ngspice/POSIX 专属测试在条件不满足时标记 skipped；输出必须保留实际执行边界。

## 证据与退出码

`--output DIR` 覆盖证据根目录。每次运行产生独立时间戳目录，`manifest.json` 保存规则状态、组件/网络数量、工具版本、原生命令日志、工件摘要及验证前后源摘要。原生报告和失败日志留在同目录；旧文件不能作为新执行结果使用。

| 退出码 | 意义 |
| --- | --- |
| 0 | 请求的自动检查通过；不代表制造放行 |
| 1 | 检查失败，或必需项 NOT_RUN，包括工具缺失/超时 |
| 2 | 自动检查完成，但严格发布资格门禁 BLOCKED |
| 64 | 配置/参数错误或请求缺失板卡能力 |

单项状态为 PASS、FAIL、NOT_RUN、NOT_APPLICABLE；不适用必须给出配置依据。既有失败优先返回 1，报告仍保留发布 BLOCKED。当前两个工程的 PCB 发布状态都为 BLOCKED。详见 [发布门禁](release_gates.md)。
