# CI、原理图交付与 PCB 发布

当前交付是两套独立原理图/BOM。ADS8588S 保留未同步旧板；AD7606C 尚无 PCB。统一工具、配置和工作流说明见 [工具使用](pcb_toolkit.md)。

| 工作流 | 范围 |
| --- | --- |
| hardware-sanity | 两工程静态检查、仓库规则、静态回归；不要求 KiCad |
| kicad-erc | KiCad 10 原生库解析、两工程新鲜网表/ERC/图纸和完整回归 |
| gate-ab-electrical | 同一 verify 入口的 ADS8588S 电气证据；手动 pcb_release 请求严格 PCB/DRC/工程门禁 |

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py test --lane static
python tools/pcb.py verify --project ad7606c --scope schematic
python tools/pcb.py verify --project ads8588s --scope release
```

原理图作用域运行原理图、BOM、接口/选型和明确启用的规则。ADS8588S 的旧 PCB 使用原封装/规则/设计失败清单及源摘要做精确基线回归；差异集合一旦变化即失败，不能借此豁免新错误。新鲜网表存在时还比对归档基线的物理差异明细。

严格 PCB 作用域保留旧板未同步问题；release 还要求新鲜全严重度 DRC 和 Gate A/B。AD7606C 请求 PCB/release 会因缺板报配置错误。没有 CI、原生工具、仿真或硬件条件时报告未执行，不可记作通过。

退出 0 只表示请求的自动检查通过；Gate A/B、PCB 和制造资格独立保留 BLOCKED。CI 生成的证据使用 artifacts 下独立运行目录，不覆盖硬件目录中的历史报告或 BOM。实际版本和未关闭条件以 [发布门禁](release_gates.md) 为准。
