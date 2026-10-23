# 硬件工程入口

两种 ADC 方案各自包含 KiCad 10 工程、原理图、本地符号/封装/模型、BOM、接口约束及四层 PCB。当前修复板均已通过全严重级别原生 DRC、未连接和图板一致性检查，以及八路 Kelvin、局部逃线、自由直角和 ADC 最大本体数字铜路检查。**人工工程审核及材料/工艺接受尚未关闭，禁止直接投板。**

| 方案 | 当前工程 | 原生对象 / 网络 / 引脚归属 | 采购实装 |
| --- | --- | --- | --- |
| ADS8588SIPM | [工程与说明](ads8588s_servo/README.md)、[四层 PCB](ads8588s_servo/ax7010_servo_reva.kicad_pcb) | 180 / 145 / 634 | 169 |
| AD7606C-16BSTZ | [工程与说明](ad7606c_servo/README.md)、[四层 PCB](ad7606c_servo/ax7010_servo_ad7606c.kicad_pcb) | 182 / 162 / 674 | 171 |

对象计数包含 DNP 和板外 J6；五个测试点属于铜图形，不采购或装配。两板目标为 24–48 V、20 kHz、10 Arms 连续相电流、20 A 瞬时正弦相电流幅值持续 30 s（14.142 Arms）、40°C 强迫风冷；12 V 总连续负载 1 A，含下游电源输入。没有板载制动，电机操作前必须独立验证外部吸能/钳位，J7 支路自行保护。

候选叠构为 JLC041621-3313 / NP-155F Tg155、外 70 µm / 内 30 µm 铜、ENIG。它与初始未证实的 Tg170 目标不同，材料接受仍开放；全部电气过孔要求付费四层 Type VII 填充/整平/铜帽工艺候选，J1/J5、J4 成品孔需要指定公差。所有实际台架、动态、温升及电机试验均为 NOT_RUN。

从仓库根目录运行：

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ads8588s --scope prototype
python tools/pcb.py verify --project ad7606c --scope prototype
```

完整原生几何验收使用带 `pcbnew` 的 KiCad Python；普通 Python 缺失该能力时不得报通过。工具位置由参数指定，详见[工具使用](../docs/pcb_toolkit.md)。`prototype` 保留七项人工审核要求，缺少签核时应明确 BLOCKED；它不等于完整 `pcb_release`。

最终源哈希、采用记录、逐器件覆盖和复核证据见[双方案审核](../docs/reviews/dual_prototype_2026-10-18/README.md)及[发布门禁](../docs/release_gates.md)。原 ADS 双层板保存在 `ads8588s_servo/evidence/legacy_pcb_before_dual_prototype_2026-10-18/`；来源清单的电气 ECO 前及布局采用前快照保存在 AD 工程的 `evidence/`。历史采购/成本日期不是当前库存报价。

接口 XDC 各自保存在工程目录中。本仓库尚无 HDL/固件实现；时序目标不是已测闭环带宽。原有 `.history/` 和本地锁文件保持保留，使用上表路径打开当前工程。
