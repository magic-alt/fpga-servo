# 布局入口电气修复记录（2026-10-09）

分支：`fix/layout-entry-electrical`，从`79dd6fc`创建，保留原有未提交文档、项目设置和未跟踪文件。指标继续为24–48V、连续10A、20kHz。**两项明确原理图缺陷和三项图板一致性问题已关闭；完整PCB布局/布线和制造放行未完成。**

## 已实施修复

| 对象 | 修复及验证 |
|---|---|
| D2/D3/D4 | 本地及嵌入DIODE符号统一为K1/A2。保持图面阳极接12V、阴极接BST的方向，实际pad1接本相BST、pad2接VDRV。实例引脚编号同步，不旋转图形掩盖编号冲突。 |
| D1 | 同步修复TVS为K1/A2，实际pad1接VBUS_PROT、pad2接GND。继续DNP，没有批准装上SMCJ54A作为保护或回馈吸收器。 |
| U6 | 删除pins16..22、27..32共13个NC标记，以50mil网格原生导线接右侧地总线，逐T分支加junction，并放局部GND符号。保留REGCAP、参考、电源和DOUT/状态链路。 |
| ADC符号 | 新增`ADS8588S_SERIAL`，这13脚按已选串行模式定义为输入，原通用符号保留；pin33原为输入。避免双向输出与电源输出型地标志的13项类型警告，未改ERC矩阵、严重度或排除。精确模式接线规则确保不能把该专用符号当并行模式使用。 |
| PCB | 通过KiCad原生pcbnew对象更新22个焊盘归属（D1..4八个、U6十三个、J3.1一个），移除已改为板外的F1封装；J1复制隐藏的Board_Revision/Board_Connector字段。 |

物理极性依据[官方D_SMA](https://raw.githubusercontent.com/KiCad/kicad-footprints/master/Diode_SMD.pretty/D_SMA.kicad_mod)与[官方D_SMC](https://raw.githubusercontent.com/KiCad/kicad-footprints/master/Diode_SMD.pretty/D_SMC.kicad_mod)的阴极pad1定义；串行模式依据[TI ADS8588S Rev.A §8.4.1.13/.14/.17，p37](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)。保留原BOM元件与MPN，不借本次接线修复声称器件完整资格已关闭。

Windows桌面自动化内核启动失败（helper ACL错误），可用MCP没有F8同步能力。因此使用[限定原生pcbnew修复工具](../tools/repair_layout_entry_pcb.py)，先生成22焊盘差异预览，再应用，不手改PCB文本来制造一致性。工具固定目标网与封装标识，拒绝旧错误网表，重复预览零变更；原生DRC一致性检查独立复核为零。

## 验证结果与网络差异

| 检查 | 本轮最终结果 |
|---|---|
| 原生KiCad ERC | 0错误 / 0警告 / 0排除；继承忽略配置不变 |
| 六项源检查 | 全部PASS；含本地/嵌入符号K1/A2、串行符号类型和可见电源接线 |
| 网表安全 | PASS：157板级元件 / 166网；系统XML159对象 / 167网 |
| 精确图连接变更 | 仅21个物理引脚网络归属变化：D1..4八个、U6十三个；所有元件值/封装与物理引脚集合不变 |
| OCP数字回归 | 531场景PASS，稳定电平限制不变 |
| PCB检查回归 | 11项PASS |
| PCB焊盘parity及约束 | PASS：157元件 / 166网 / 161封装（含四机械孔） |
| 原生图板一致性 | **3→0** |
| 局部ngspice46 | 六被动/理想源模型及独立公式检查PASS；结果与修复前一致，仅网表哈希更新 |
| 最终PCB DRC | **271违规：220错误/51警告；478未连接；0原理图一致性问题**，退出码1，验收仍失败 |

新增回归先对旧网表/符号运行，准确检出极性和ADC缺陷；修复后通过。旧网表179网减少至166网，是13个浮空串行引脚网并入GND的预期变化，不能沿用旧计数。没有减少元件或删除必需连接以满足检查。

最终DRC分类与前一轮相同：2 tracks_crossing、17 shorting_items、113 clearance、88 solder_mask_bridge、8 track_dangling、43 isolated_copper。478未连接比466多12，反映新增接地要求与同步后的连接图；本轮未布这13脚到地平面的真实铜。不能通过NC、隐藏飞线或忽略未连接来把这个数降下去。

## 保留项与仍未完成的PCB工作

逐原生对象及文本比较确认：所有20条旧走线的UUID/几何/网络/宽度/层不变；五铜区完整定义不变；板框不变；H1..4整个封装不变。其余保留封装的UUID/位置/方向/库标识均不变；仅上述七个封装属性发生预期变化，额外F1移除。工作区原有`.kicad_pro`改动本轮未覆盖。

对旧铜实际端点审查发现多数不落在当前真实焊盘上，并带VBUS、PGND、SW_U等过时网络名；部分跨过其他相或分压器。不能只按旧网名自动改名，也不能只删除旧铜来降低DRC数。需要在批准的器件位置上逐段确定起止焊盘，建立正确替代连接后替换旧路径。当前板只有20线段、零过孔，478未连接代表完整布线工作仍待开展。

另外，POWER网络类0.8mm间距也作用于接这些网的IC局部焊盘；细间距封装存在0.15mm等固有间隙。未经板厂工艺与器件焊盘依据复核，不把间距降小或添加排除来清零。正式功率布局仍需确认实际叠层/铜厚、板厂最小线宽间距、10A RMS含义、环境与冷却；自举刷新、辅助电源负载、回馈吸收、封装热和OCP台架门禁继续开放。已向用户请求这些参数。

## 图纸与证据

- [八页修复后PDF](reviews/layout_entry_repair_2026-10-09/final.pdf)、[八页总览](reviews/layout_entry_repair_2026-10-09/all_pages.png)、[ADC接地页](reviews/layout_entry_repair_2026-10-09/page_5.png)、[二极管页](reviews/layout_entry_repair_2026-10-09/page_6.png)。已视觉核查，地总线未接到REGCAP或DOUT。
- [原生ERC](reviews/layout_entry_repair_2026-10-09/erc.json)、[原生DRC](reviews/layout_entry_repair_2026-10-09/drc_final.json)、[parity](reviews/layout_entry_repair_2026-10-09/pcb_parity.json)、[确切网络变更](reviews/layout_entry_repair_2026-10-09/intentional_graph_delta.json)、[PCB同步变更](reviews/layout_entry_repair_2026-10-09/pcb_sync_applied.json)。
- [PCB正面](reviews/layout_entry_repair_2026-10-09/pcb_front.svg)、[背面](reviews/layout_entry_repair_2026-10-09/pcb_back.svg)、[修复前PCB快照](reviews/layout_entry_repair_2026-10-09/before.kicad_pcb)、[对象保留校验](reviews/layout_entry_repair_2026-10-09/pcb_preservation.json)、[仿真结果](reviews/layout_entry_repair_2026-10-09/simulation/results.json)。

独立审查再次确认两项电气修复、地总线与图板parity正确，并核对旧铜/机械保留。制造放行清单继续以[release_gates.md](release_gates.md)为准；原[布局入口审查](schematic_layout_entry_review_2026-10-09.md)作为修复前发现及完整仿真边界记录保留。
