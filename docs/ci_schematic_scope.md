# 原理图交付与 PCB 发布检查

当前交付范围为原理图与 BOM，见 [发布门禁](release_gates.md)。保留的 ADS8588S PCB 没有同步最终器件及正向母线 OCP；新 AD7606C 工程尚无 PCB。

## PR 自动检查

- `hardware-sanity`：原理图语法、网格、可见电源连线、连接、ADC 合约、BOM、检查器回归及公开路径扫描。
- `kicad-erc`：两套工程的新鲜原生 XML/网表、全严重级别 ERC、物理引脚/供电/配置、OCP 数字场景、保留电路及旧板差异回归；报告和逐步日志作为 artifact 上传。
- `gate-ab-electrical`：`run_gate_ab.py --schematic-only` 收集原方案新鲜 ERC/网表、ADC 静态边界、ngspice 理想源场景及旧板差异回归。Gate A/B 与 PCB 发布状态仍为 BLOCKED。

`--schematic-only` 必须显式指定。`check_design.py` 和 `run_gate_ab.py` 默认仍执行严格 PCB 检查，旧板仍会失败。原理图模式继续检查分流器符号及本地封装的物理引脚。

## 保留旧板的回归边界

[固定基线](../hardware/ads8588s_servo/evidence/pcb_ci_baseline.json) 保存源板/工程/规则的统一换行文本哈希、13 项设计阻塞、封装及内部间距问题，以及从新鲜原生网表得到的逐项 parity/网络类差异。基准板来源是 `17166bc`，本轮未修改原板或其规则。

CI 验证旧板与这份记录精确一致，不将 parity 失败标为通过；原生网表检查还比较元件、物理引脚、网络名称和每个差异的内容，不能只凭相同错误数量通过。空导出、缺失检查、新增/改变的阻塞或源板变化都会失败。基线没有自动更新入口，任何后续板级修复都需要重新评审。

仅 Python 的 `hardware-sanity` 不导出网表，其基线检查明确记录 `fresh_parity_evaluated=false`。另外两个原生工作流必须以本次导出的网表检查完整差异。

## 严格发布检查

```sh
python tools/check_design.py
python tools/run_gate_ab.py --with-drc --strict-gates
```

也可手动运行 `gate-ab-electrical` 工作流并勾选 `pcb_release`。该模式执行严格 parity、网络类、全严重级别 DRC 和工程门禁，不降低严重级别、不增加排除项，也没有 continue-on-error。它目前应失败，直到旧板同步、布线和实际工程证据完成。

PR 检查通过只表示本次原理图交付及保留旧板回归符合范围，不代表 PCB、模拟瞬态、RTL/STA、实板或制造验收通过。

## 跨平台源文件保护

AD7606C 的 `source_manifest.json` 保留原始字节 SHA-256，并增加从原基准提交生成的 UTF-8/LF 文本 SHA-256。源文件比较只统一换行，不忽略内容差异，因此 Windows CRLF 与 Linux LF 都可复核，真实内容改动仍失败。
