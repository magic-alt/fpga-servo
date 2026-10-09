# Gate A/B 电气审查与仿真资格化（2026-10-09）

> **结论：自动化证据已建立，但 Gate A = BLOCKED、Gate B = BLOCKED。**
> 本文档不是投板、功率上电、安规 STO 或保护响应认证。不得把脚本 PASS、GitHub CI 绿灯或纯被动 ngspice 结果解释为工程放行。

## 1. 设计基线 / 不确定性

- 源代码：`hardware/ax7010_servo_reva.kicad_sch` 和七张子页；目标 KiCad 10。
- 冻结的目标：24–48 V 母线、20 kHz PWM、10 A 连续相电流。当前计算暂按 **10 Arms**，实际额定定义、峰值电流、工作环境及散热、回馈能量/电源吸收能力均未获验收。
- 原历史证据（2026-10-09，非本轮新执行结果）：ERC 0/0、图板 parity PASS、PCB DRC 271 条违规 + 478 未连接。新的 CI 从每次提交的原生 KiCad 源文件重新导出；绝不通过复制历史 XML 来伪造本轮 PASS。
- `tools/gate_ab_verify.py` 对每份**新导出的 XML 网表**重核物理引脚、关键被动值、模拟/保护链路，生成容差计算和两份 ngspice 理想模型。原源及自定义物理焊盘、元件选型、PCB 此 PR 不修改。

## 2. Gate A：原理图电气冻结

| 领域 | 当前证据 | 状态 / 未完成条件 |
|---|---|---|
| 8 页原生电路/ERC | `kicad-cli sch erc --severity-all --exit-code-violations`；此 PR 的 CI 重新执行 | 自动检查可 PASS，但不替代器件应用审查 |
| 采样三相 shunt/INA/ADC | 对 RSH1..3 的 1=3、2=4 Kelvin 电气节点，INA241 REF1/REF2、C40..42、U15/U16、U6 实际脚序验证；人工仍审查 PCB Kelvin 路由 | 图连接回归可 PASS；采样精度/共模恢复未资格化 |
| ADS8588S 串行模式 | U6 16..22、27..33 接 GND；采样输入 49/51/53 及数据接口检查 | 连接检查可 PASS；ADC 采样时序/欠压仍开放 |
| Bootstrap | D2..D4 真实 pad1 阴极到 BST、pad2 阳极到 12V，CBOOT1..3 与 U1 实脚对应 | 静态拓扑可 PASS；充电电压、压降、刷新/最高占空比与 PCB 回路未验证 |
| 失电安全 | R80..R86 默认下拉、U24/U25 看门、U26/U23/U20/U11 门控由既有脚本及新回归覆盖 | **A-ADC-UNDERVOLTAGE：阻塞**；局部断电、未配置 FPGA、门极状态必须用真实电源/波形确认 |
| 器件/热/机械 | 曾检查 MPN、若干物理焊盘；详见 `docs/release_gates.md` | **A-VENDOR-FOOTPRINT-MPN / A-PEAK-THERMAL-SPEC：阻塞**；真实厂家封装图、最大负载、温度/散热需冻结 |

### A-ADC-UNDERVOLTAGE：确认的资格化缺口

根据 TI 的公开数据：ADS8588S 模拟供电 AVDD 下限 **4.75 V**；TPS3808G50 的标称下降阈值 **4.65 V**，按阈值 ±2% 的高侧也只有 **4.743 V**。

因此即使选择最早动作的阈值角点，也仍存在至少 **7 mV** 的 `AVDD < 4.75 V` 但监督器尚未确保触发的区间（而典型情况窗口可更大）。这不是“参考设计容差够小即可忽略”的问题；一旦 ADC 数据已失效而门控仍允许 PWM，保护无法把有效电流测量当作前提。Gate A **不能以 ERC=0 放行**。

处理选项（需要设计复核后实施，而非本 PR 盲改原理图）：使用能在 ADC 保证工作下限以上、计入检测器误差/迟滞/纹波的独立模拟许可或提高阈值的监督器；或定义与实现 **ADC 不可信时禁止 PWM 的硬件联锁**。验收需包含下降沿、上升沿、偏置电源分别丢失、复位与随机时序、全部角点。还需确认 G33 恢复的最坏约 3.194 V 与 AX7010 VIO 实际最低值是否匹配。

## 3. Gate B：动态功率及保护

| 模型/场景 | 此 PR 可重复计算 / 测试 | 不能从该结果推断的事项 |
|---|---|---|
| R50..53 OCP 阈值 | VA5=5 V 名义阈值高/低 4.70588/0.29412 V；约 ±22.0588 A；4.75..5.25 V、分压电阻 ±0.1%、shunt ±1% 被动角点扫描 | INA 增益/输出摆幅与失真、比较器失调及温漂、全速率过驱量、错误中断的总延迟 |
| R40/C40 | 理想一阶网络 τ=47ns，fc≈3.386 MHz；SPICE 验证门限越过时刻 | INA241 动态（公开 1.1 MHz 带宽/1µs 阶跃到 1%）、ADC 建立/抗混叠及开关共模恢复 |
| 直流母线回馈 | C1+C2=200 µF、理想无吸收 +1 A，从 48 V 到 55 V 仅 1.4 ms；能量差约 0.0721 J；ngspice 与闭式公式互检 | **55 V 并非允许电压**；未建模上游回充、ESR/ESL、感性浪涌、实际电容与制动器；无已合格吸收回路 |
| 栅极驱动 / 功率开关 | BSC040N10NS5 100 V VDS Max、72 nC Qg 上界（只在厂家给定测试条件），FD6288 标称 +1.5/−1.8 A 峰值、标称 200 ns deadtime | Qg/峰值电流除法只能作为**理想理论量级**，绝不是实际关断时间上界；未完成 vendor model + 半桥 SPICE、反向恢复、门极/开关尖峰、SOA 和热验证 |
| 总过流保护时延 | 现有纯数字 `check_ocp_behavior.py` 覆盖稳态 531 场景；前序 32 ns 仅限数字逻辑特定边沿、温度和负载条件 | 必须测 `t_INA+t_RC+t_comparator+t_logic+t_driver+t_gate_off` 全链路；TLV9024 100 ns 是典型值非最坏安全上界；还需故障脉冲、竞争、相位及不同上电顺序 |
| 开关电源 12V/5V | TI LM5164 额定 VIN 6..100V / 输出最高 1A；必须回到真实原理图及厂家计算工具/模型 | 负载阶跃、启动、磁件饱和、纹波、输出电压误差、辅助电源失效行为均未资格化 |

公式和波形均来自**当前源网表中的实际数值**（而非人工重复填写的历史器件值）。计算的角点为探索性假设，尚未证明 BOM 电阻温漂/电容额定值等满足所选容差。注意 10 Arms 下每个 5mΩ shunt 名义耗散 0.5 W，不等于 5 W 器件在该 PCB 上已热合格。

### 必须完成后才能关闭 Gate B 的实验

1. **真实器件模型及三相动态**：取得且确认版本/端口顺序的 FD6288、MOSFET（含门电荷/寄生二极管）、INA241、TLV9024、LM5164 模型，分别执行 24/48 V、极端 PWM/死区、故障正负电流斜率、不同 MOS 温度/栅阻及最大占空比；模型缺失不能写“仿真已完成”。
2. **实测保护总时延/波形**：受控低能量、具限流/隔离条件和合格差分探头测六路 VGS、各相 SW/母线尖峰、OCP_N 和实际门极消隐过程；覆盖开路/短路、短脉冲与 CLEAR 竞争。不能根据 32ns 数字逻辑加典型 100ns 比较器直接声称安全。
3. **回馈和源侧协调**：记录实际电源吸收能力、闭合回馈能量/OV 动作、外置熔断器 KLKD025.T 与 LPSM0001Z、输入线缆与真实故障电流/动作时间的协调证据。
4. **供电/采样时序**：真实 12V、5V、VIO 启停及任意部分供电组合，确认 ADC 无效时 PWM 确实禁止；三路电流增益、偏移、PWM 动态失真和 ADC 采样窗口。
5. **热/规格冻结**：确定 10A RMS 的系统含义、峰值/持续时间、最高环境及散热方式；测 MOSFET、shunt、端子、磁件在最坏运行点的稳定温度。

所有实测条件应写入 `docs/release_gates.md` 的原清单，并提供仪器截图、加载条件、签署人、硬件 PCB 版本、批次和可追溯 SHA。当前**无人执行实物台架，因此所有实测项仍开放**。

## 4. 可重复执行

请在 Linux/macOS/Windows 的 KiCad 10 环境中先导出新网表，使用一个安装好的 `ngspice` CLI：

```bash
mkdir -p artifacts/gate-ab
kicad-cli sch erc --severity-all --exit-code-violations \
  -o artifacts/gate-ab/erc.rpt hardware/ax7010_servo_reva.kicad_sch
kicad-cli sch export netlist --format kicadxml \
  -o artifacts/gate-ab/netlist.xml hardware/ax7010_servo_reva.kicad_sch
python tools/gate_ab_verify.py \
  --netlist artifacts/gate-ab/netlist.xml \
  --output artifacts/gate-ab/qualification.json \
  --spice-output artifacts/gate-ab/spice
GATE_AB_NETLIST=artifacts/gate-ab/netlist.xml \
  python -m unittest discover -s tools -p test_gate_ab_verify.py -v
```

产出：原生 ERC 报告、新导出 XML、`qualification.json`（输入 SHA256、拓扑、阈值容差、条件范围和 **两个 BLOCKED 字段**）、独立 ngspice 网表/波形/日志。CI 在 PR 中自动运行并上传不可伪造为物理试验的自动证据。运行 `--strict-gates` 时，即使图和理想电路测试通过，Gate A/B 未闭合也返回状态码 2。不能通过覆盖这个状态、忽略检查、直接上传历史 XML 或删除 PCB 铜来发布。

## 5. 数据来源与模型边界

- [ADS8588S（TI）](https://www.ti.com/product/ADS8588S)：AVDD 4.75..5.25V、16bit、SPI/并口。
- [TPS3808（TI）](https://www.ti.com/product/TPS3808)：G50 标称 4.65V、G33 标称 3.07V；阈值偏差及恢复迟滞按器件版本复核。
- [INA241A（TI）](https://www.ti.com/product/INA241A)：A2 增益20，带宽 1.1MHz、动态恢复取决于 PWM 条件。
- [TLV9024（TI）](https://www.ti.com/product/TLV9024)：开漏输出、100ns **典型**传播延迟；不是保证最大关断时间。
- [FD6288（Fortior Tech）](https://fortiortech.com/en/product/hvic/hvic/fd6288)：3相半桥驱动、UVLO、内置死区/直通防止；必须取得 V1.6 原始手册检查完整时序及典型应用。
- [BSC040N10NS5（Infineon）](https://www.infineon.com/part/BSC040N10NS5)：100V 最大 VDS、Qg 58nC 典型/72nC 在特定条件的最大值，不能替代开关仿真。
- [LM5164（TI）](https://www.ti.com/product/LM5164)：6..100V 1A buck；磁件和板上负载须单独定量验算。
- 本仓库：`docs/ocp_latch_review_2026-10-09.md`、`docs/schematic_layout_entry_review_2026-10-09.md`、`docs/analog_safety_layout_review_2026-10-09.md`、`docs/release_gates.md`。

**记录规则：**“自动物理连线 PASS”、“被动/理想源仿真 PASS”、“器件模型 PASS”、“实物资格 PASS”分别记录，绝不能互相替代。
