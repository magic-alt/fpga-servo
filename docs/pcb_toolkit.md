# PCB 工具使用

从仓库根目录运行 `python tools/pcb.py --help`。主工具使用 Python 3.12 标准库；原生流程需要 KiCad 10。没有额外 pip 依赖。工具路径通过 PATH 或显式命令参数提供，公共文档不保存本机安装路径。

## 选择工程与工作流

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope pcb
python tools/pcb.py verify --project ad7606c --scope prototype
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
python tools/pcb.py export --project ad7606c --kind fabrication
python tools/pcb.py develop --project ads8588s --operation snapshot
python tools/pcb.py develop --project ads8588s --operation snapshot --apply
python tools/pcb.py develop --project ads8588s --operation sync --preview
```

BOM 通过 KiCad 新鲜 XML 按已注释的实际元件实例导出，正确处理重复层次和多单元器件；因此 BOM 导出也需要 KiCad 10。导出默认写独立证据目录，不更新受版本控制的 BOM。采购导出要求工程声明采购数据目录和 BOM；输出保留日期、未资格替代品与未解决物料。它不刷新供应商库存，也不代表可下单批准。

snapshot 默认预览；apply 只生成不覆盖的项目源副本和 SHA-256 清单，包括本地符号/封装、库表及显式配置的附加源文件。系统安装库、远端依赖和未声明文件不包含在快照中。sync 当前输出原生 F8 审阅步骤，状态为 NOT_RUN，退出非零；没有自动同步后端，apply 被拒绝。历史修板/布线工具在 [tools/archive](../tools/archive/README.md)，不属于当前工作流。

## 工程首板与制造文件

`verify --scope prototype` 增加工程首板门禁：新鲜 XML/原生网表、全部严重度 ERC、补铜后 DRC、图板物理引脚一致性，以及器件、封装、电气、电流/热预算、关键布局、机械和 DFM 审阅。原生 `.kicad_pro` 的 ERC/DRC 类别不得为 ignore/禁用，排除列表必须为空，自定义 DRC 规则也不能忽略或排除检查。原生报告的错误、警告、排除、未连接及图板差异必须全部为零。必需输入、工具或审阅缺失时返回非零。

项目 `parameters.fabrication_profile` 声明仓库根目录相对的 JSON 文件；不把它或审阅文件加入 `source_files`，以免形成循环摘要。其结构为：

冻结流程会将制造配置作为单独绑定的输入复制并校验，供快照中的制造意图检查使用；这不将审核注册表加入设计哈希。Windows 下运行测试建议明确使用 `python -X utf8`，并用带 `pcbnew` 的解释器执行原生几何通道。制造复审的 PDF/CAM 依赖也须在实际执行它们的解释器中可用，缺失依赖会明确失败。

```json
{
  "schema_version": 1,
  "project_id": "ad7606c",
  "manufacturer": "实际制造商",
  "stackup": {
    "profile_id": "已核实可下单的实际叠构编号",
    "copper_layers": 4,
    "thickness_mm": 1.6,
    "copper_oz": [2, 1, 1, 2],
    "copper_thickness_mm": [0.070, 0.030, 0.030, 0.070],
    "dielectric_material": "与原生叠构一致的实际材料",
    "dielectric_layers": [
      {"name": "dielectric 1", "type": "prepreg", "thickness_mm": 0.092, "epsilon_r": 4.1},
      {"name": "dielectric 2", "type": "core", "thickness_mm": 1.230, "epsilon_r": 4.42},
      {"name": "dielectric 3", "type": "prepreg", "thickness_mm": 0.092, "epsilon_r": 4.1}
    ],
    "evidence": {"path": "证据文件相对路径", "sha256": "文件实际SHA256"}
  },
  "reviews": {}
}
```

上例是待填结构，不能通过门禁。制造商证据必须对应所选叠构、铜厚、介质和板厚；通用宣传页不能替代实际工艺确认。`copper_oz` 是四层标称铜重，`copper_thickness_mm` 是该制造工艺的四层实际铜厚，两者分别记录，不能用固定 oz 换算推定实际铜厚。示例数值对应 JLC041621-3313 的制造商实际层厚，应用时必须提供其已哈希的工艺证据。板文件必须显式保存原生 stackup，四个铜层厚度必须与实际工艺值相符（误差不超过 0.001 mm）；每层介质必须有材料和厚度，总厚度必须与板厚相符。工具检查文件和参数一致性，工程人员仍负责确认制造商证据内容及介质电气参数。

`reviews` 必须包含 `component`、`footprint`、`electrical`、`thermal_budget`、`critical_layout`、`mechanical`、`dfm`，每个值都是 `{"path": "审阅JSON相对路径", "sha256": "实际SHA256"}`。各审阅 JSON 必须有 `schema_version: 1`、当前 `project_id`、对应 `subject`、`status`、非空 `reviewer`、带时区且不在未来的 `reviewed_utc`、`source_hashes` 和非空 `evidence` 数组。每个附件也采用上述 path/sha256 结构，必须是存在、非空、未篡改的仓库内实际文件。只有已完成、由责任审阅者明确填写的 `status: "PASS"` 才接受；待执行保持 `NOT_RUN`。工具不生成通过审阅，不验证审阅者身份，也不以 JSON 字段代替工程判断。

`source_hashes` 必须与 `pcbtools.manufacturing.design_source_hashes(project)` 的完整映射精确相同，覆盖当前层次原理图、PCB、BOM、配置、原生工程/规则、本地库/模型及显式附加源；有 `baseline_config` 时也覆盖其设计。审阅完成后任何输入改变都使该审阅过期。审阅文件、附件和制造 profile 分别保存摘要，并在验证/导出结束时重新检查。冻结后的审阅不能复用于另一工程。

每份审阅还必须有 `fabrication_spec_sha256`，等于 `pcbtools.manufacturing.fabrication_spec_sha256(profile)`：对 profile 排除 `reviews` 注册表后的全部内容作规范 JSON 摘要，避免自引用，同时绑定制造商、逐层介质/Dk、孔公差、填孔、钢网等工艺要求。只改制造规格也会使原审阅过期。逐层 `dielectric_layers` 必须与原生叠构逐项相符，不能用相同总厚度替代各层参数。

prototype 验证及制造导出复制已核对摘要的设计输入到独立 `frozen-design`，将层次页、库表及模型引用限定在该副本内；原生 ERC/DRC、几何、Gerber、钻孔、STEP 和 BOM 均读取同一副本，并检查副本摘要。实际板上引用的模型必须是存在、随项目保存的本地文件，纳入设计摘要；不读取环境变量去猜测模型路径。副本同时记录原文件摘要和引用重定位后的摘要。不得从正在编辑的板文件分别导出互不一致的制造文件。

工程参数 `native_manufacturing_minima` 可声明必须保存到原生 `.kicad_pro` 的制造下限；缺少、非有限值或低于声明值均阻断。当前两板要求 `min_silk_clearance: 0.15`、`min_text_height: 1.0`、`min_text_thickness: 0.15`（mm）。只启用检查类别却保持零间距不能证明制造间距合格。`forbid_footprint_clearance_overrides` 同时拒绝板上宽泛的封装/焊盘 clearance 覆盖；特定封装必要例外须用已审核的同实例规则限定，不能放宽其他铜路。

`prototype_ready` 与 `pcb_release` 独立：首板自动门禁通过可记录 `prototype_ready: PASS`，实物 Gate A/B 和 `pcb_release: BLOCKED` 保留。`verify --scope release` 继续执行完整发布门禁，不能用首板结果关闭未完成的动态、热浸或实物资格。

`export --kind fabrication` 每次重新执行 prototype 验证，不接受历史 manifest 作为批准。通过后才在同一独立目录用 KiCad 原生导出四个铜层、阻焊、钢网、丝印、板框 Gerber X2、分离 PTH/NPTH Excellon 钻孔及钻孔图/报告、双面非 DNP 位置表、STEP、装配/机械 PDF 和新鲜 XML BOM。每个必需文件必须存在且非空；所有命令、工具版本、源摘要和输出摘要写入 manifest。设计/审阅在执行中变化会阻断结果，失败目录仅供诊断。该命令不上传、不下单；输出状态仍明确要求独立 CAM/制造包复核，不能把导出成功当作制造包视觉审核或安全额定运行批准。

`bom.csv` 保留完整设计清单；`assembly-bom.csv` 与 `assembly.csv` 仅列实际购买、装配的器件，位号集合必须精确一致。工程显式 `copper_only_refs` 按完整封装身份声明 TP1–5 裸铜，不将其作为购买件或贴装项；若该位号变成有实际 MPN 的器件则阻断，不能静默过滤。保留原始 `assembly-native.csv`，逐行核对新鲜 XML 及实际板上的值、封装、有限坐标、角度和面，结果写入 `assembly-consistency.json`。自动角度核对不替代器件 pin1、极性及装配工艺人工复核。

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

### 全板保留地层与 ADC 本体守卫

选择 `power_layout` 的工程必须明确配置 `reserved_ground_layers`，本仓库两方案均保留 `In1.Cu` 给 `/GND`。原生检查覆盖所有网络的直线、圆弧、板级及封装内铜区；空网铜也拒绝。贯穿过孔造成反焊盘，真实规则区是约束而非铜，分别记录。此规则不等于连续电流截面、回流阻抗或噪声资格；不能用只检查 ADC 数字网的规则代替。负向回归见 `tools/tests/test_pcb_reserved_ground_layers.py`，包含保存并重载的封装铜区案例。

`adc_body_digital_exclusion` 独立选择准确 MPN、厂商封装和完整数字接口网，最小包络采用已核对的 10.2 mm 最大本体，包含原生轨迹端帽、圆弧、过孔铜及旋转。缩小本体或遗漏真实 ADC 数字网会失败。保留地层检查与本体检查均在 `pcb`、`prototype`、`release` 的原生几何检查中执行。

`.gitattributes` 对硬件和本轮机器证据禁用文本换行转换，保持 CAD、厂商模型、原始快照与 SHA256 记录逐字节一致。首次采用该属性时暂存区可能出现仅换行的差异；不得据此重写已保存的原始证据或放宽来源检查。
