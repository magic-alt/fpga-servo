# AX7010 + ADS8588S 四层工程板

2026-10-19：当前源已采用修复后的四层 PCB，完成 U7 物理引脚、独立阻尼 DC-link/J7、12 V 总负载 1 A、5 V 有效容量/软启动、装配焊盘及关键布线修复。原生 ERC 为 0 错误 / 0 警告 / 0 排除，原生 DRC 为 0 违规 / 0 未连接 / 0 图板差异；八路 Kelvin、严格局部逃线、自由直角和 ADC 最大 10.2 mm 本体数字铜路检查通过。**制造放行仍为 BLOCKED，禁止直接投板。**

打开 [KiCad 工程](ax7010_servo_reva.kicad_pro) 或 [PCB](ax7010_servo_reva.kicad_pcb)。当前 PCB SHA256：`e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226`。[采用与来源记录](../../docs/reviews/dual_prototype_2026-10-18/ads8588s_pcb_adoption.json)不构成人工批准。

- 原生源：9 页、180 元件 / 145 网络 / 634 引脚归属，包含 DNP 和板外 J6。
- 采购实装：169 项；五个裸铜测试点不进入装配 BOM/CPL，DNP/板外件独立排除。
- U6：ADS8588SIPM，双 DOUT 接口；[接口与时序合同](../../docs/adc_fpga_timing_and_freeze_2026-10-12.md)。
- 板框中心线 130 × 95 mm，原连接器与四安装孔锚点保留。H1–H4 为 3.2 mm PTH / 5 mm 铜焊盘，不能改称 NPTH。
- 候选叠构为 JLC041621-3313 / NP-155F Tg155，外层 70 µm、内层 30 µm、ENIG；材料接受、付费四层 POFV 和受控成品孔工艺尚未关闭。
- 本地 `mechanical/` 包含原样保存的通用模型及明确标为 NOT OEM 的橙色净空模型，不能代替实际配合、座高、工具和机箱审核。来源与许可见 [model_sources.json](mechanical/model_sources.json)。

设计目标：24–48 V、20 kHz、10 Arms 连续相电流、20 A 瞬时正弦相电流幅值 30 s（14.142 Arms）、40°C 强迫风冷；12 V **总**连续 1 A。额定工作与全部物理试验尚未资格化。没有板载制动；电机运行前需独立验证外部吸能/钳位，J7 绕过输入 F1，外部夹具必须提供支路保护。

从仓库根目录运行：

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py verify --project ads8588s --scope prototype
python tools/pcb.py test --lane all --kicad-cli kicad-cli --pcb-python <KiCad-python>
```

`prototype` 必须包含原生几何和七项源哈希绑定的人工审核，缺失时保持 BLOCKED；ngspice 仅证明静态/理想模型部分。详见[统一工具](../../docs/pcb_toolkit.md)、[本轮审核](../../docs/reviews/dual_prototype_2026-10-18/README.md)、[首板边界](../../docs/reviews/dual_prototype_2026-10-18/first_board_boundary.md)与[低能量上电程序](../../docs/bringup.md)。

顶层、全部子页（含 `dc_link.kicad_sch`）、`.kicad_sym`、`.kicad_pro/.kicad_dru`、`bom.csv`、XDC、工艺/电源 profile 及本地库共同构成当前设计。`${KIPRJMOD}` 引用可随仓库迁移。历史双层 PCB 快照在 `evidence/legacy_pcb_before_dual_prototype_2026-10-18/`，旧未同步结论和旧零 DRC 不能作为当前板验收。

AD7606C 是[独立工程](../ad7606c_servo/README.md)，不是本板中一行 MPN 替换。本仓库尚无 HDL 或固件；候选性能配置和 RTL/STA/实测资格分开维护。历史成本和采购表保留其原日期，不代表当前价格或可替代资格。
