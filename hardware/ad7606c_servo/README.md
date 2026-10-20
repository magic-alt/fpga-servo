# AX7010 + AD7606C-16 四层工程板

2026-10-20：按用户确认取消整页板载 DC-link 电容和阻尼器件，仅保留 J7 外部电容/泄放接口，已同步原理图、PCB、BOM 和验证合同。新鲜 ERC/DRC/未连接/图板差异均为 0；当前制造复审导出通过。见[外置 DC-link 改版及证据](../../docs/reviews/ad7606c_jlc_2026-10-20/external_dc_link.md)。材料/特殊工艺接受、工程签核与实物资格仍开放。

2026-10-19 历史修复：四层 PCB 完成 U7、当时的 DC-link/J7、12 V 总负载 1 A、5 V 有效容量/软启动、装配焊盘、ADC 本体旁扇出及关键回路修复。八路 Kelvin、严格局部逃线、自由直角和 ADC 最大 10.2 mm 本体数字铜路检查在本次改版后重新通过。**人工工程审核、材料/特殊工艺接受和制造放行仍开放，禁止直接投板。**

打开 [KiCad 工程](ax7010_servo_ad7606c.kicad_pro) 或 [PCB](ax7010_servo_ad7606c.kicad_pcb)。当前源 SHA256、制造输出和实际变更见[本版摘要](../../docs/reviews/ad7606c_jlc_2026-10-20/external_summary.json)。[历史采用证明](../../docs/reviews/dual_prototype_2026-10-18/ad7606c_pcb_adoption_final.json)及[来源转换](../../docs/reviews/dual_prototype_2026-10-18/layout_adoption_transition.json)继续保留，没有取消 ADS8588S 原方案保存检查。

- 原生源：11 页、182 元件 / 162 网络 / 674 引脚归属，包含 DNP 和板外 J6。
- 采购实装：171 项；五个测试点为 PCB 裸铜，不进入装配 BOM/CPL。
- J7 为唯一外部 DC-link 接口，1 脚正极、2 脚 GND；外部电容及并联泄放电阻不在本板 BOM。连接及参考参数见[外部网络合同](../../docs/reviews/ad7606c_jlc_2026-10-20/external_dc_link.md)。
- U6：AD7606C-16BSTZ；AVCC/VDRIVE 同源 VA_5V，U27–U29 为 TXU0204PWR，OE 跟随 PWR_READY。四 DOUT、软件模式、配置/新帧有效合同见[电气方案](development_board.md)、`adc_profile.json` 与独立 XDC。
- 板框中心线 130 × 95 mm，原 H1–H4 及 J1/J3/J4/J5 锚点保留；安装孔为 3.2 mm PTH / 5 mm 铜焊盘。
- 原生叠构为 JLC041621-3313 / NP-155F Tg155 候选，外 70 µm / 内 30 µm 铜、ENIG。Tg155 与初始未证实的 Tg170 目标不同；材料接受、付费四层 Type VII POFV 和指定成品孔公差仍需关闭。
- 便携模型、许可和橙色 NOT OEM 净空模型见 [mechanical/](mechanical/README.md)。未知实际座高、配合端、线缆、工具和机箱仍为 OPEN。

设计目标：24–48 V、20 kHz、10 Arms 连续相电流、20 A 瞬时正弦相电流幅值 30 s（14.142 Arms）、40°C 强迫风冷；12 V **总**连续负载 1 A，含下游电源输入。静态预算不是满载启动、热或动态保证。没有板载制动；电机操作前必须独立验证外部吸能/钳位，J7 绕过输入 F1，外部支路自行保护。全部物理试验为 NOT_RUN。

从仓库根目录运行：

```sh
python tools/pcb.py check --project ad7606c --scope schematic
python tools/pcb.py verify --project ad7606c --scope prototype
python tools/pcb.py test --lane all --kicad-cli kicad-cli --pcb-python <KiCad-python>
```

完整几何验收使用带 `pcbnew` 的 KiCad Python；统一入口参数和缺失能力处理见[工具说明](../../docs/pcb_toolkit.md)。`prototype` 保留七项人工审核，缺少签核时应明确 BLOCKED；完整 `pcb_release` 及投板后的动态/热资格单独验收。

当前证据入口：[双方案审核](../../docs/reviews/dual_prototype_2026-10-18/README.md)、[逐器件覆盖](../../docs/reviews/dual_prototype_2026-10-18/component_coverage.md)、[发布门禁](../../docs/release_gates.md)、[低能量上电](../../docs/bringup.md)。`evidence/` 下日期为 2026-10-18 的初次建板、旧原理图 PDF 和旧布线验收属于电气 ECO 前历史，不可替代当前哈希的验证。

本仓库没有 HDL/固件实现。ADC 器件性能、候选高速配置和外部时序约束不代表已验证的 RTL/STA 或闭环带宽；不得把原 ADS 的 MPN 直接替换成 AD7606C。原方案及旧快照见 [ADS8588S 工程](../ads8588s_servo/README.md)。
