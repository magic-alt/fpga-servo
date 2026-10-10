# PCB 直角、铜皮与采样电阻 3D 排查 — 2026-10-10

分支：`fix/pcb-corners-copper-3d-20261010`，起点 `0d6b3d3`（main）。用户授权创建分支、修复 PCB 直角、确认铜皮后酌情优化，并排查采样电阻 3D 不显示。工作板已采用验证后的候选结果；原有 `hardware/.history/` 保留；修复分支提交供 PR 审查，不直接合并 main。

## 走线修复

将 **39 处外露的两段走线直角改为斜角**，包含浮点坐标量化产生的一处近似 90° 拐角。保持原走线线宽、网络、层及 UUID；新增 39 段短连接。166 个封装的身份、位置、方向及焊盘网络/位置/尺寸/孔径一致；456 个过孔的位置、网络、直径和孔径一致。原理图、板框、安装孔、项目设置和规则文件未改。

U18 的 3 段新斜角位于既有 `U18_pad_escape` 范围内，并继承原两段走线所属的原生组。没有改动逃线规则、扩大限定范围或降低严重级别；`check_pcb_escape.py` 验证组内铜均在限定区域内且物理接入本器件焊盘。

新增 `tools/check_pcb_corners.py` 检查外露的 degree-two 拐角：修改前 39，修改后 0。另行报告 42 处焊盘/过孔内的方向交汇及 10 处小于 1µm 的路由量化短段；这些没有作为外露直角处理。T 分支不属于两段转弯检查范围。5 项原生几何回归通过，涵盖外露直角、斜角/直线、T 分支、量化短段和过孔锚点。

[逐处修复坐标](reviews/pcb_corners_copper_2026-10-10/bevels.json) · [修改前检查](reviews/pcb_corners_copper_2026-10-10/before-corners.json) · [最终检查](reviews/pcb_corners_copper_2026-10-10/final-corners.json)

## 铜皮判断与处理

按保存的实际填充多边形分析，不以区域标签或视觉孤立作为判断依据。使用原生几何碰撞连接同网、同铜层的走线/过孔/焊盘，再将每一块填充铜加入连接图，确认能到达真实焊盘；保留多边形孔洞。过孔连接两面铜，层间不会凭投影相交误连。

| 区域 | 修改前块数 | 重铺铜后块数 | 最终到焊盘连通 |
| --- | ---: | ---: | ---: |
| F.Cu `/DC Input & Protection/RPP_SRC` | 1 | 1 | 1/1 |
| F.Cu `/GND` | 50 | 50 | 50/50 |
| B.Cu `/GND` | 33 | 32 | 32/32 |
| 合计 | 84 | 83 | 83/83 |

**未发现死铜。** 中间外观看似分开的地铜实际通过走线/过孔/焊盘接入网络，因此保留其回流功能。三处铺铜区原本均设为“始终移除孤岛”，继续保持；直角修复后原生重铺铜更新了碎片数量，不手动删除连接铜、不盲目添加跨区连接。原生孤岛标志亦为 0。该结论证明静态连接，不代替高频回流、EMI 或功率热设计审查。

[修改前铜连接证据](reviews/pcb_corners_copper_2026-10-10/before-copper.json) · [最终铜连接证据](reviews/pcb_corners_copper_2026-10-10/final-copper.json) · [可复现的只读审计脚本](reviews/pcb_corners_copper_2026-10-10/audit_copper.py)

## 采样电阻在 3D Viewer 中缺失的原因

`RSH1/RSH2/RSH3` 使用项目自定义封装 `fpga-servo:Ohmite_650_4T_P25.40x6.35mm`。原生 API 检查发现：**板上三个封装的模型列表长度均为 0，封装库的模型列表长度也为 0。** 因而 3D Viewer 显示焊盘/孔，却没有电阻本体可绘制；不是模型文件路径丢失或隐藏设置造成。

本轮只定位此问题，未添加未经验证的通用模型。恢复本体显示需要将匹配实际 `Ohmite 650FPR005E` 的 STEP/WRL 绑定到本地库与板上三处封装，并核对四脚方向、落板高度和包络。型号参考：[Ohmite 产品页](https://www.ohmite.com/catalog/60-series/650FPR005E)。

## 验收与视觉证据

最终工作 PCB：166 封装，5517 段走线，456 过孔，169 个非空网络；网表 162 板上元件 /169 网络。

- 六项项目检查全部通过：native schematic、grid、schematic layout、schematic connectivity、power wiring、design。
- 新鲜网表的 safety、OCP 531 稳态场景、物理 PCB parity、PCB constraints 通过。
- 原生 ERC：0 违规。
- 工作板原生 DRC：`--severity-all --all-track-errors --schematic-parity --refill-zones --save-board --exit-code-violations`，**0 违规 /0 未连接 /0 原理图一致性问题**。
- 六条 Kelvin 独立采样支路、既有封装逃线检查和新增拐角检查通过。规则/项目设置字节不变；未新增排除或更改忽略类别。
- 已逐面查看导出图。采样电阻本体仍缺少 3D 模型，前述原因已确认。

[最终 DRC](reviews/pcb_corners_copper_2026-10-10/final-drc.json) · [Kelvin](reviews/pcb_corners_copper_2026-10-10/final-kelvin.json) · [逃线](reviews/pcb_corners_copper_2026-10-10/final-escape.json)

[修改前正面](reviews/pcb_corners_copper_2026-10-10/before-front.png) · [修改后正面](reviews/pcb_corners_copper_2026-10-10/after-front.png) · [修改后背面](reviews/pcb_corners_copper_2026-10-10/after-back.png)

复现原生只读检查（使用支持 `import pcbnew` 的 KiCad Python）：

```sh
python tools/check_pcb_corners.py
python tools/test_pcb_corners.py
python tools/check_pcb_escape.py
python tools/check_pcb_kelvin.py
python docs/reviews/pcb_corners_copper_2026-10-10/audit_copper.py \
  hardware/ax7010_servo_reva.kicad_pcb /tmp/pcb-copper.json
```

此次为布局几何修复，不关闭 [release gates](release_gates.md) 中的动态保护、时序、热、机械及制造资格门禁。
