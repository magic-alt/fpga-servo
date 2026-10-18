# AX7010 + AD7606C-16 独立硬件工程

当前状态：11 页原理图、BOM、原生同步的四层 PCB 布局候选。**尚未布线，不可制造放行。**

打开 [KiCad 工程](ax7010_servo_ad7606c.kicad_pro) 或 [PCB](ax7010_servo_ad7606c.kicad_pcb)。
[布局图](evidence/pcb_placement_2026-10-18.png)、
[本轮审查](evidence/pcb_review_2026-10-18.md) 和 [开发板电气方案](development_board.md) 提供当前入口。

## 本轮进展

- 保留旧板 130 × 95 mm 板框、H1-H4 安装孔和 J1/J3/J4/J5 的原点/角度，建立独立四层板。
- 通过 KiCad 项目 F8 和新鲜 CLI 网表的原生导入完成同步；独立检查逐物理焊盘、完整封装 ID、值、DNP，保留四个机械孔。J6 是原理图明确排除于 PCB 的外部电源参考。
- 181 个原理图系统对象、162 网络；180 个电气封装与四个机械封装。原 ADS8588S 电气源和旧 PCB 保持原样。
- ADC 去耦/参考及 TXU 电平转换器按实际新 ADC 引脚布置，串联和偏置电阻靠近服务端。首次建板阶段未改变电气方案；随后仅对 12 V/1 A 电源的五个器件执行明确选型 ECO，所有引脚网络及保护拓扑保持一致。
- 修复复制工程的顶层文件名/UUID 元数据，统一工具已登记实际 PCB。
- 原生检查始终包含未连接和图板一致性；当前未连接仍开放，不能把几何零违规当成完整 DRC 通过。

## 电气与器件边界

U6 是 AD7606C-16BSTZ；AVCC/VDRIVE 同源 VA_5V，U27-U29 是 TXU0204PWR，OE 跟随 PWR_READY。
四路 DOUT、OS=111 软件模式、输入量程、配置镜像、启动/欠压/帧有效合同见开发板方案和 `adc_profile.json`。
独立 XDC 仅记录外部 AX7010 接口约束；本仓库为硬件工程，没有 HDL 实现。

所有板载符号脚号均可匹配指定封装的焊盘号；这不等于厂商尺寸、额定功率、热和动态验收全部完成。
用户已明确 12 V 辅助电源按 **总连续负载 1 A** 设计；本轮采用 L1=150 µH / Wurth 7447709151，442k/49.9k 精密反馈及 200k/3.3nF C0G 纹波网络，已同步原理图、BOM 和 PCB。
见 [1 A 电源审查](evidence/aux_power_review_2026-10-18.md)。静态角点计算不代替满载启动、温升和瞬态实测，整板发布门禁仍开放。
GUI 保存网表漂移已通过显式保留 6 mil 导线线宽修复；最终 11 页保存回读精确一致，W 相页边距已调整。PCB 布线和实物制造验收仍未关闭。

## 复现

在仓库根目录执行，原生工具路径使用本机参数指定：

```sh
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope pcb
python tools/pcb.py test --kicad-cli kicad-cli --pcb-python <KiCad-python>
```

PCB/release 不再因为缺板而退出；会运行实际图板一致性和 DRC。未布线时其非零退出码必须保留。
不能添加排除项、降低严重级别、删除必要连接或改成 NC 来获得通过。

原理图与最初独立工程交付的历史证据保留于 [2026-10-17 审查](evidence/review.md)；
[2026-10-18 初步器件审查](evidence/continuation_review_2026-10-18.md) 描述建板前状态。
当前制造/热/动态条件以 [发布门禁](../../docs/release_gates.md) 为准。
