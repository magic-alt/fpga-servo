# AD7606C PCB 布线与 CAD 验收（2026-10-18）

状态：**ROUTED CAD CANDIDATE / PHYSICAL QUALIFICATION OPEN / NOT FOR FABRICATION**。

本轮承接 499 个未连接的四层布局候选，完成电源、功率级、Kelvin 采样、门极、硬件联锁、ADC、编码器和 AX7010 接口布线。保留已确认的板框、四个安装孔和连接器位置；没有更改物理引脚分配、取消连接或把必需引脚改为 NC。根目录 FPGA 文件夹已在先前提交移除，接口约束随硬件文档保存。

## 当前原生证据

最终运行及源文件 SHA-256 见 [CAD 证据摘要](routing_2026-10-18/cad_acceptance.json)，原始 [ERC](routing_2026-10-18/erc.json)、[DRC](routing_2026-10-18/drc.json) 和 [11 页原理图 PDF](routing_2026-10-18/schematic.pdf) 一并保存。

| 项目 | 实际结果 |
| --- | --- |
| KiCad | 10.0.3，重新导出网表，重新填充铜区，执行全部严重度 ERC/DRC |
| 原理图 / 图板 | 181 个系统元件、162 个网络、672 个物理引脚归属；180 个板载电气器件、4 个机械孔；J6 为板外对象 |
| 原理图 ERC | 0 errors / 0 warnings / 0 exclusions；AD7606C ignored_checks 为空 |
| PCB DRC | 0 violations / 0 unconnected / 0 schematic parity；ignored_checks 为空 |
| PCB 几何 | 4 个铜层、1733 段走线、441 个过孔、33 个铜区（含规则区） |
| 图板一致性 | 引用、值、DNP、封装 ID、物理焊盘及网络精确匹配 |
| 项目工程检查 | 供电/1 A 计算、器件焊盘、网络类、8 路 Kelvin、2 个封装逃线组、拐角检查通过 |
| 两工程 schematic check | ADS8588S、AD7606C 均通过；ADS8588S 保留原项目 ERC 配置，其旧 PCB 未资格化 |
| 完整回归 | 185 项：171 通过、14 明确跳过；另 44 项原生 PCB 几何测试全部通过 |

默认 Python 的 14 项跳过中，11 项 PCB 原生相关检查已由另行执行的 KiCad Python 几何测试覆盖；其余 3 项依赖 ngspice/POSIX 运行器，未执行、不记为通过。完整清单见证据摘要。原生验证运行前后受检源文件哈希一致。CAD 检查与回归均为实际执行记录。

## 布线和审查边界

关键功率路径、12 V/5 V 转换器、门极与采样先受约束布线，普通信号使用本机 Freerouting 2.5.0 辅助。自动布线只合入指定网络的新铜线，保留原有关键网络和铜区，再用 KiCad 原生 DRC、图板一致性及独立几何检查验证；未上传设计文件。自动布线器自己的完成率不是验收依据。

网络类使用真实层次网名，保留功率和门极间距/线宽要求。U1、U18 封装焊盘入口使用两个明确列举、由原生几何约束验证的局部逃线规则，不能扩展到其他走线或被视作全板间距豁免。没有新增 DRC 排除，也没有降低检查严重度；本轮反而启用了原先忽略的 5 类 DRC 和 4 类 ERC。修复了 23 处过孔接入端点警告，给 H1–H4 添加与本地库一致的 6 mm 庭院；孔位、孔径和焊盘不变，实际螺钉/垫圈仍需机械确认。

原理图去除 7 条完全重叠的重复线，将四向交点拆为邻近 T 点，并把两个电源图形沿实际导线移位。修改前后原生 XML 比对确认元件身份、网名及 672 个引脚归属精确一致。逐页复核原理图并重新检查修改页的电源/GND 区域；电源、GND、PWR_FLAG 仍通过可见原生导线连接实际节点。

已查看四层铜图：[F.Cu](routing_2026-10-18/ax7010_servo_ad7606c-F_Cu.png)、[In1.Cu](routing_2026-10-18/ax7010_servo_ad7606c-In1_Cu.png)、[In2.Cu](routing_2026-10-18/ax7010_servo_ad7606c-In2_Cu.png)、[B.Cu](routing_2026-10-18/ax7010_servo_ad7606c-B_Cu.png)。In1 保留连续地参考，L1 芯体下有所有铜层禁布区。该审查不能代替真实叠层、电流密度、回流阻抗、dv/dt 或 EMC 测量。

## 尚未完成的实物验收

**12 V 连续总负载 1 A 是设计要求，尚无实物连续输出 1 A 的保证证据。** 总电流包含 DRV8300 及下游 5.1 V 电源消耗，不能把外接 1 A 负载与总负载要求混用。满载冷启动/热重启、40°C 满载温升、负载及输入瞬态全部 NOT_RUN，详见 [台架验收程序](aux_1a_bench_acceptance.md) 和 [原始结果空表](aux_1a_bench_results.csv)；不能用计算值填写实测栏。

量产叠层/铜厚、器件与焊盘装配资格、10 Arms/20 A 热资格、OCP 关断时间、再生能量、ADC 目标 20 MHz 时序/噪声、实际 AX7010 接口、制造文件和首件验证继续 OPEN。5 MHz 初始调试约定不能充当 20 MHz 实物资格。完整边界见 [当前发布门禁](../../../docs/release_gates.md)。当前不发布生产批准或下单制造包。

## 复现

从仓库根目录运行（为 KiCad PCB 检查选择带 pcbnew 的 Python）：

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope pcb --kicad-cli kicad-cli
python tools/pcb.py test --lane all --kicad-cli kicad-cli --pcb-python <KiCad-Python>
```

`verify --scope pcb` 通过仅关闭当前 CAD 检查；严格 release 的工程和实物门禁仍然阻断。
