# 新 PCB 接入与领域规则扩展

## 只增加工程配置

复制 [配置模板](../tools/projects/template.json)，把占位路径换成实际文件。root 相对配置文件，其余路径相对 root；root 可指向仓库外工程。输出必须位于单独目录，不能覆盖原理图、PCB、库、BOM 或其源目录。

```json
{
  "schema_version": 1,
  "id": "sensor-board",
  "root": ".",
  "schematic": "sensor.kicad_sch",
  "board": "sensor.kicad_pcb",
  "libraries": ["sensor.kicad_sym"],
  "output": "evidence",
  "rule_sets": [],
  "parameters": {"grid_mm": 1.27}
}
```

无 PCB 时省略 board；原理图检查照常可用，请求板级验证会报错。库和 BOM 按工程需要声明；空 rule_sets 不引入任何伺服板器件或引脚要求。当前公共图面约束采用 A4 横向；其他图幅需要增加并测试对应几何边界后使用，不能假定 A4 检查适用于所有页面。

附加 FPGA/profile 等源输入可在 `parameters.source_files` 声明相对 root 的路径数组；快照和输入摘要包含这些文件，不扫描任意相邻 JSON 或读取环境变量。系统安装库保持外部依赖。

运行 `python tools/pcb.py check --config path/to/project.json --scope schematic`，然后用 verify 生成新鲜证据。递归层次从顶层 Sheetfile 枚举；合法重复源页实例允许，循环、缺失页和重复实例路径会报错。传入的所有源路径必须位于工程 root。

## 共享能力与专属规则

| 模块 | 责任 |
| --- | --- |
| project / report / cli | 严格配置、稳定状态、统一入口 |
| kicad / schematic / board | 数据解析、层次、网格、可见连线、原生执行、物理网表一致性 |
| verification / export / development | 证据编排、独立导出、预览与快照 |
| rules/servo、adc、protection、power_layout、repository | 当前工程的已审阅电气/布局/来源约束 |

现有领域工厂显式接收 Project，返回局部作用域的规则 API；不修改模块全局路径，不执行旧脚本源码。完全通用的纯解析家族不需要 Project。新增领域优先向合适模块增加规则函数，避免一个规则一个文件；家族过大时按独立领域拆分，不把所有规则拼成巨型入口。

规则通过 `run_rules(project, scope, inputs)` 注册；返回 `Finding(rule_id, status, message, details)`。新领域加入白名单 KNOWN_RULES，并为适用工程配置 rule_sets。通用规则不能依赖 RSH1、J10、U6 等固定器件；专属合同只能在对应规则集执行。新规则必须包含一个真实错误输入的回归，确认先失败再通过。

原生数据必须来自本次导出，XML 需有非空组件、网络及物理引脚；ERC/DRC 报告字段残缺不能通过。需仿真或 pcbnew 的规则明确声明依赖，失败或缺失返回 FAIL/NOT_RUN，不能删掉检查来适配新板卡。

扩展 EDA 适配器时以现有 Project/RunReport 为边界；当前只实现 KiCad 10，不宣称支持其他 EDA。未来机械尺寸、封装或新电路要求须有相应参数和回归，不复制当前伺服合同冒充通用检查。

## 不变量

新工程接入应通过临时第三工程回归，证明无需复制检查脚本。验证命令默认只读；开发修改功能必须先提供预览、独立备份、差异报告和新的电气审阅依据。自动通过不能替代厂商数据、热/电流、动态波形或制造资格。
