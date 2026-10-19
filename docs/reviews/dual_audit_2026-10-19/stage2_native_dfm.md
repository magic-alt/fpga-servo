# 阶段 2：两板真实工艺、U13 铜焊盘与原理图边界修复

基线源提交 b17c5c4。上一阶段的完整原生结果已在 PR #24 留存；本阶段修改必须重新验证，不能沿用零 DRC。

## 确认的问题与实际 ECO

1. 两个 PCB 的 setup 都是 filling=no、capping=no，与已有制造规格的 Type VII 矛盾。修改为 filling=yes/capping=yes；掩膜 tenting 保留，全部电气过孔的位置、孔径、层对和连接不动。制造配置明确非导电环氧填料；KiCad 布尔值不能代替材料或板厂接受。
2. U13 TPS62901 的 RPJ0009A 官方铜焊盘 1–6 宽度是 0.20 mm，而拟用 JLC 常规 SMD 铜焊盘下限为 0.25×0.25 mm。两套局部库与 PCB 内嵌 U13 同步将这些铜焊盘增宽到 0.25 mm，保持中心、针脚、网络、器件位置和其余三个焊盘不变。六个原有 0.20 mm 钢网开口改为独立无编号、无网络、仅 F.Paste 的焊膏图形，避免铜增宽同时过量加锡。TI 的该页钢网基准为 0.125 mm，保留该值。这是明确记录的定制 DFM 铜地修改，不冒充官方原样推荐或已被装配厂批准。
3. 两板 gate_inverter 页 PWR923 的图形原先延伸到 200 mm 下边框之外。将 GND 图形和必要 GND 标签直接锚定 U11/C83 的真实地节点（43.18,194.31），移除原 2.54 mm 图形末端短支线；保留本地可见实际电路连线。新鲜 XML 必须证明所有器件、封装、网络和物理引脚连接不变。

## 防复发及保护原源

新增工艺门禁检查全板 SMD 最小铜尺寸、原生填孔/铜帽及逐过孔禁止覆盖、U13 精确铜焊盘中心和原有钢网。定向回归 13 项通过，涵盖关闭 filling/capping、单过孔覆盖、焊膏误增宽、移位和丢失开口。最初阳性约束在原板失败，已保留本地失败记录；没有减少已有 ERC/DRC、图板一致性或原始来源保护规则。

完整静态回归 310 项，266 通过、44 项因缺少本地原生工具明确跳过。源保护回归曾指出三个授权修复文件与原清单不同；保留旧清单为 source_manifest_before_native_dfm_2026-10-19.json，新增明确 before/after 转换，未删除保护检查。

工作流原生重填覆铜后，除生成器信息及 filled_polygon 缓存外，全部 S 表达式设计内容必须等价；否则停止，不提交。实际原生保存的字节和来源清单记录为 native_after_sha256，保留补丁预期字节 after_sha256。随后运行完整原生回归、两板 ERC/DRC/parity/几何检查和前后物理网表等价检查，成功后才推送真实源文件提交。

## 一手依据

TI TPS62901 SLVSFS7A 的 RPJ0009A 4224505/A land pattern 和 solder-paste example（PDF 第 46、47 页）：https://www.ti.com/lit/ds/symlink/tps62901.pdf 。
JLC 工艺能力 SMD pad、阻焊及 POFV 项：https://jlcpcb.com/capabilities/pcb-capabilities/ 。
KiCad 10 pcbnew 文档中的 IPC-4761 填孔与铜帽设置：https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html 。

工程七项签核、同一实际订单能否组合四层指定叠构/外70内30µm/ENIG/Type VII/特殊成品孔公差仍未取得。本阶段不关闭这些条件，也不把制造后的实板资格记作已完成。

## 可恢复性

三段 .gz.part 仅为传输编码，顺序拼接后的 gzip 和展开的完整文字补丁均由 SHA256 校验；完整补丁会在实际应用提交中恢复为 current.patch，真实源文件差异也直接出现在 PR 中。所有失败和成功产物继续归档到工作流 artifact。
