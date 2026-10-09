# PCB 同步前复核与机械孔修复

本轮在 `fix/ocp-latch-industrial-review` 上继续，起点为 `4145df7`。保留未跟踪的 `hardware/.history/`；未推送。原理图与电气网络未改动。

## 已修复的机械错误

H1–H4 的 Value 为 `M3_HOLE`，原板却使用 1.0 mm 钻孔，不能穿过 M3 螺钉。现修正为 3.2 mm 间隙孔，尺寸参照本地 KiCad 10 `MountingHole:MountingHole_3.2mm_M3_Pad` 的钻孔定义。这里只采用其钻孔尺寸，没有把现有封装替换成该库封装。

四个孔中心仍为 (5,5)、(129,5)、(5,94)、(129,94) mm；5 mm 铜环外径、镀通孔属性、无网络状态、板框、20 段走线及 1 个铜区均保留。径向铜环宽度为 0.9 mm。机箱、螺钉头/垫片空间和机械电气隔离仍待实物审查，不能据此关闭全部机械门槛。

`tools/check_design.py` 新增 M3 标注孔的最小钻孔检查。先对未修复板运行，准确报告 H1–H4 四项失败；修复后通过。修复前板文件及报告保存在 `artifacts/pcb_mechanics_before/`。修复后俯视图为 `artifacts/pcb_mechanics_review.svg` 和 `.png`，已进行视觉检查；旧布局的重叠与占位封装仍清晰可见。

## 更新后的图板差异

旧 `artifacts/pcb_sync_audit.json` 停留在 137 器件阶段。本轮重新导出原理图网表，并使用 KiCad 10.0.3 的 pcbnew 读取 PCB，按真实物理引脚和焊盘比较，重新生成该文件。

| 项目 | 本轮结果 |
|---|---:|
| 原理图器件 / 网络 | 158 / 183 |
| PCB 封装 | 32 |
| 原理图有、PCB 无的位号 | 136 |
| 共同位号 | 22 |
| PCB 独有位号 | 10 |
| 共同位号中封装标识不匹配 | 22 |
| 共同位号中物理引脚集合不匹配 | 10 |
| 共同物理引脚上的网络名不匹配 | 268 |
| 排除仅差根层级 `/` 前缀后的网络不匹配 | 199 |

10 个引脚集合不匹配位号为 Q1–Q6、U10、U12、U13、U15。逐焊盘明细见 JSON；即使引脚集合相同，旧占位封装也不能视作合格实物封装。上述网络名比较没有自动合并 GND/PGND、VBUS/VBUS_PROT 或任何旧 Kelvin 伪网络，也没有修改 PCB。

PCB 独有 CBUS1/CBUS2、RSHU/RSHV/RSHW、U14 为待复核的旧电气器件；H1–H4 为必须保留的机械项，不能随普通多余器件删除。

原理图指定的 155 个非空封装均在本地官方库中找到，且其编号焊盘集合与网表物理引脚集合一致。**这只证明库存在和编号覆盖，不证明制造商引脚功能、焊盘尺寸或热设计合格。** RSH1–RSH3 仍无封装，继续阻止完整图板同步验收。临时只读审计脚本为 `artifacts/audit_pcb_parity.py`，未纳入 CI。

## 功率替代候选调查

Phoenix Contact MKDS 5 的两位 [1714971](https://www.phoenixcontact.com/us/products/1714971/pdf) 和三位 [1714984](https://www.phoenixcontact.com/us/products/1714984/pdf) 可作为 J3/J4 的候选：制造商标称 32 A，9.52 mm 间距，推荐孔径 1.3 mm。运行温度与载流能力相关，必须结合导线截面积及降额曲线验收；标称值不等于板上高温额定值。候选间距不同于现用 7.62 mm，且本地 `TerminalBlock_Phoenix` 库没有对应 MKDS-5 封装，需依制造商图纸建立、核验项目封装及板边空间后才能采用。本轮未将候选写入原理图/BOM。

分流器不能直接按系列最高功率选型。例如 [Bourns CSS4J-4026 数据手册](https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf) 的 5 mΩ 档 `CSS4J-4026K-5L00x` 只有 4 W，不满足项目既有 >=5 W 条件；不能用其他阻值档的额定功率替代。现有 BVB-I-R005 的问题仍未关闭。保持 5 mΩ 可避免改变 INA241 增益对应的量程/OCP 阈值；改用较低阻值需另行重新计算并审查整个测量与保护链。

## 新鲜验证与剩余门槛

- 五项仓库检查全部通过；网表安全检查通过；OCP 稳定电平模型 531 个场景通过。
- ERC：0 错误 / 0 警告 / 0 排除，保留已有 4 类忽略检查。
- 本轮机械孔修改后 DRC：357 项违规 / 129 项未连接 / 0 排除；保留已有 5 类忽略检查。CLI 返回码 5，表示验收仍失败。
- 最新 DRC 分类：solder_mask_bridge=118、silk_over_copper=112、shorting_items=53、lib_footprint_issues=32、clearance=24、silk_edge_clearance=7、silk_overlap=6、track_dangling=3、tracks_crossing=2。
- 修复前同轮 DRC 为 358 项，clearance=25；按位置/项目归一化比较，差别来自重复报告项数量，不能将一项计数变化称为电气净距已修复。旧版板源缺少稳定 UUID，逐次报告中的自动生成 UUID 也不可直接作差异依据。

下一步先完成端子/分流器确切选型与封装，再以当前网表重建图板一致性；每段既有铜线需核对新端点及网络。独立保留 OCP 台架时序、浪涌/再生、电源部分供电、AX7010 实物接口和温升门槛。本轮没有关闭布局冻结或制造放行门槛。
