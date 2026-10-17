# Rev.A-P 原理图设计与BOM选型冻结审查矩阵（2026-10-12）

> **当前状态：ARCHITECTURE SELECTED / SCHEMATIC FREEZE BLOCKED / NOT FOR FABRICATION**。本文件是冻结审核记录，不是假装已经完成ERC/DRC、SPICE动态证明、PCB制造首件/48V功率运行。本轮PR #16直接修正KiCad源和BOM的语义错误，不调整未经实测的硬件功率/保护拓扑。本表以最新`main`合并PR #15和本PR增量为基础；更改原理图后，先不要复用#15旧ERC计数或历史PCB的DRC0结论。

> **2026-10-12新增性能要求后的冻结级别修订**：下表中的ADS8588S是仍在原理图内的实际版次，F0原有“保留ADS8588S架构选定”不再适用于3–5kHz+高速电流环候选。首选[AD7606C-16BSTZ低延迟4lane](adc_high_performance_reselection_2026-10-12.md)，处于**PERFORMANCE ARCHITECTURE SELECTED / ADC KiCad+BOM ECO NOT IMPLEMENTED / F1仍BLOCKED**。原U6=ADS8588S的静态ERC0不构成新ADC原理图通过。L1/PCB与动态门禁仍各自未通过。

## A. 硬件设计输入与必须保持的电气拓扑

| 系统模块 | 冻结选型 / 范围 | 本轮裁决 | 尚未完成的证据 / 可退出条件 |
|---|---|---|---|
| 输入与功率 | 24–48V、10Arms相线连续、20A幅值30s、40°C、强制风冷 | **架构保持** | Peak具体波形、重复时间、最低风速、源最大故障电流和回馈吸收能力必须形成合同 |
| 逆变桥 | 6×Infineon BSC040N10NS5、DRV8300DPWR（非反相） | **MPN保持** | 六路VGS、栅极33Ω初值、2V/ns SH速率、24/48V VDS/SOA、功率热和驱动欠压行为实测 |
| 电流测量 | 3×HoYLR2512 5mΩ相线shunt + 3×INA240A1DR | **MPN保持** | 10Arms/20A30s热、8条inner-side sense (含母线)、PWM共模恢复和每路标定 |
| 正向总线OCP | RSH4 2mΩ + U5 INA240A1DR + U15 LM393LVDDFR + 锁存/6路PWM门控 | **功能/名义25A保持** | 正向母线检测不等于相峰值或反向保护。完整故障到VGS关断动态与C1/C2局部短路能量、MOS SOA待证实 |
| ADC | U6 ADS8588SIPM / 双串行DOUTA+DOUTB / 同时8通道 / ±5V / OS=000 | **硬件接口架构选定** | 数字SCLK上限20MHz、首版10MHz；64 clocks/frame。当前无合成HDL/AX7010 STA/实板波形，模拟LPF在±5V约16kHz且有频率相关相位延迟；另见[FPGA时序合同](adc_fpga_timing_and_freeze_2026-10-12.md) |
| FPGA接口 | J10为实际连接、J11/J2不装配 | **收口** | 现已注释禁用J11未装配端口XDC，保留历史映射在接口文档；J10实板连续性/IO bank电压仍需验收 |
| NTC | NTC1和NTC2为两个板上10k/B3950 | **描述修复** | 把`NTC_MOTOR`改为`NTC_BOARD_AUX`，BOM/原理图描述同步，不再宣称电机绕组过温保护。变更是网名，并无新增外部温度接口 |
| 双buck辅助电源 | U12 LM5164 12V、U13 TPS62901 5.1V、VIO 3.3V来自AX7010 | **拓扑保持** | L1实际额定与最差输入/电流纹波、辅助峰值负载、5.1V纹波/超快欠压、编码器短路影响未证明 |
| L1 | 68µH | **P0唯一较大未签核电感** | 不能把现用SOREDE SDRH.1209.LF680MT00的库存记录当做Irms、Isat及满温1A许可；需要核对真实厂商规格并经封装/PCB与首件测试签核 |
| DC-link | 2×100µF/100V铝电解，C3 1µF/250V film，C4 100nF/100V C0G | **保留，元数据更正** | C3图/表历史Function写100V，本轮修成250V。开关环、100V/250V有效容量、纹波/热和2oz铜厂制造工艺待验收，不擅删C3/C4 |
| 硬件电源安全 | F1 0456025.ER 25A SMD、LM74502 Q7/Q8，VA5/VIO监督 | **暂时保持** | F1标称72VDC/500A分断不是任意供电短路合格；VA5静态门限不构成全动态欠压资格；不加制动，但系统再生能量路径必须锁定 |
| 编码器 | 5V差分ABZ、AM26LV32E、ESD、F2 PTC | **MPN保持** | 线缆共模/端接、F2温度降额、远端短路影响5.1V母线以及物理连接器环境条件待证实 |

## B. 确认不再进行的无依据降本

Rev.A明确**保留**第三路相电流、ADS8588S（不更换成4ch导致额外ADC重设计）、独立母线正向OCP、六路PWM硬件输入关断和供电有效性连锁，避免为了“元件数量少”损失实际监测/控制稳定性。C94高成本稳定定时C0G、R93/R94/R95高精度、C4 1812 C0G和C3 film在本轮默认不动；下一设计版本只有在原厂/试验模型和新MPN/实际工艺成本证据支持时才允许ECO。在Rev.A冻结前引入无验证替代件**不划算**。

## C. L1重新选型：规格可以初筛，采购/封装未冻结

当前L1为SOREDE `SDRH.1209.LF680MT00` 68µH，生产决策保留BLOCKED而非虚假标成Ready。

| 具体候选 | 原厂已可核对参数/采购链接 | 本次结论 |
|---|---|---|
| SXN(顺翔诺) `SMDRI127-680MT`, LCSC **C9907** | [供货页](https://item.szlcsc.com/10439.html)、[原厂资料](https://atta.szlcsc.com/upload/public/pdf/source/20210810/6F96FDC19AA308DD2AD166FFB9640E87.pdf) p2/p9：68µH ±20%、DCR最大0.140Ω、Isat 4A、温升电流2.1A，最大本体12.3×12.3×8mm，厂家焊盘图的F/G/H尺寸需与现板匹配 | **优先电气候选，待库存/焊盘/首件确认**。部分页面展示无库存，**不能宣称现货**；原SOREDE焊盘不得未经核对直接通用 |
| Coilcraft `MSS1246T-683MLC` | [原厂资料](https://www.coilcraft.com/en-us/products/power/shielded-inductors/ferrite-drum/mss-mos/mss1246t/mss1246t-683/)：68µH、最大DCR约186mΩ、Isat2.3A（10%L下降）、Irms1.3A（20°C温升）/1.8A（40°C温升） | **原厂电气对照件**，适合1A附近热预算初筛，但须检查空间、满温及供应链 |
| Coilcraft `MSS1210-683MED`, LCSC **C5183009** | [LCSC](https://item.szlcsc.com/5844713.html)：68µH ±20%、最大DCR标示68mΩ、Isat4.9A、额定2.8A、器件高10mm | **大电流备选**，但更高器件高度和单件成本可能导致结构约束，货源/样品资料未核对，不能直接选入BOM |

按TI LM5164原厂2026版本参考68µH设计，48Vin/12Vout/1A、约300kHz、L=68µH给出典型约447mA峰峰电流；使用-20%电感值可按相同频率得约551mA，理想1A负载峰值约1.276A，负载RMS电感电流约1.013A。**实际LM5164限流阈值仍应高于电感的额定饱和值并有动态裕量**；此处不能使用“平均电流1A所以Isat1A就够”判定。温升必须依据PCB/环境实测，并按制造商关于Isat（L下降比例）及Irms（温升标准）的定义计算。

L1关闭条件：厂家原厂签章规格文件及型号/封装/推荐焊盘、具体采购渠道库存快照与不少于5板数量、额定电流/温升/饱和定义、LM5164最差电流限值和最小频率的电感峰值预算、满载/过载/开关动态及PCB 2oz工艺验收。**没有这些证据，不通过MPN冻结。**

## C2. 最新TI限制：68µH的1A端到端电流裕量尚不能保证

TI LM5164新版原厂规格：[2026-02 Rev.D PDF](https://www.ti.com/lit/ds/symlink/lm5164.pdf) 第6页给出**最小峰值限流1.25A、典型1.5A、最大1.75A**；其12V/1A典型应用第17页用68µH Coilcraft参考电感，**不能将该典型示例等价成48V、全温、全容差、所有批次的1A保证**。另见[TI应用工程师的电感建议](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1568691/lm5164-lm5164ddar-schematics-review)：当1A载流和高输入电压接近限流角点，建议考虑约120µH并评估反馈纹波和电容有效容量。

理想连续导通CCM初步模型（未含频率漂移、DCR、器件电感随电流下降、峰值限流检测延迟）：

```
Vin = 48 V, Vout = 12 V, fsw = 300 kHz illustrative
ΔIL_pp = Vout*(1-Vout/Vin)/(L*fsw)
68µH min -20% = 54.4µH → ΔIL_pp ≈ 0.551A
@12V/0.5A → Ipeak ≈ 0.776A，距离1.25A静态门限约0.474A
@12V/1.0A → Ipeak ≈ 1.276A，超过1.25A静态门限约0.026A
120µH min -20% = 96µH → ΔIL_pp ≈ 0.313A
@12V/1.0A → Ipeak ≈ 1.156A，距离最小门限仅约0.094A
```

**工程裁决**：Rev.A真实12V总峰/连续负载若可证明≤0.5A，继续68µH + 具备原厂Irms/Isat的候选电感即可；若定义必须**保证**1A，重新核算最小/最大开关频率、限流全温及负载动态并优先评审≥120µH电感，不能只换“68µH大电流牌子”。具体120µH库存及电气候选包括[PROD Tech PSPHAQ127-121M，C2983074](https://www.lcsc.com/product-detail/power-inductors_prod-tech-psphaq127-121m_C2983074.html)（120µH、2A、Isat2A、DCR250mΩ）及[Bourns SRR1210-121M，C2045692](https://www.lcsc.com/product-detail/C2045692.html)（120µH、Irms2.3A、Isat1.9A、DCR170mΩ）；两者**都不自动满足芯片限流设计、PCB焊盘、损耗和采购预算**，只列待询价。无外部负载及磁件/PCB资格前，F1原理图冻结**必须维持BLOCKED**。

## D. 原理图KiCad实际修改及净表影响

- `hardware/ads8588s_servo/current_adc.kicad_sch`：两处真实`(label "NTC_MOTOR")`统一为`(label "NTC_BOARD_AUX")`，NTC2的Description同时更正；8通道ADS8588S双串行信息写入页标题栏注释。**同一节点标签改名，网络连接物理拓扑未被故意改变；但网名发生变化，PCB须后续同步**。
- `hardware/ads8588s_servo/power_input.kicad_sch`：C3 Description `1uF_100V_FILM`→`1uF_250V_FILM`，保持1µF和原厂选中的实际250V订货号。
- `hardware/ads8588s_servo/aux_power.kicad_sch`：L1 Description从过期Coilcraft描述改成当前资格开放提示；不偷偷换MPN或改变焊盘。
- `hardware/ads8588s_servo/bom.csv`：C3、L1、NTC2 Function三项与现行选型/硬件安装位置相符，159个对象结构未改变。
- `fpga/ax7010_servo_reva.xdc`：J11不存在的30项并行/辅助pin assignment仅注释，J10 active 26条真实物理映射保持。
- `tools/pcbtools/rules/adc.py`及`tools/tests/test_adc_serial_contract.py`：接口/源语义和负向变异回归；已接入两个硬件CI工作流。**此类静态检查无法证明真实功率关断或替代KiCad ERC**。

## E. 五级冻结Gate

| Gate | 应有证据 | 当前可声明状态 |
|---|---|---|
| F0 功能和器件架构选择 | 三相采样、ADC双串行、独立母线OCP、无板载制动器、J10 2022版接口冻结 | **DESIGN SELECTED（不修改基本架构）** |
| F1 原理图源与具体零件MPN冻结 | 8页原生ERC 0、最新物理pin/net XML、模式strap、全BOM同源且关键L1/电源/连接器规格和采购资料完整 | **BLOCKED：L1尚未完整资格；本分支最新ERC尚须新执行** |
| F2 PCB布局冻结 | 最新8页与PCB逐Pad-Net一致、完整0 DRC/0未连接、Kelvin/回流/功率环/厂商焊盘、板厂DFM报告 | **BLOCKED：PR #15新增总线OCP等尚未同步PCB** |
| F3 功率与时序样机资格 | OCP sense→6VGS-off延迟/SOA、VA5快速跌落、死区/driver D slew、ADC LPF与RTL/STA、温升/电源限能 | **BLOCKED：没有本轮测量证据** |
| F4 48V满载/制造放行 | 电源短路分断/I²t/线束、回馈系统合同、10Arms长稳态、20A30s/冷却、首件检测 | **BLOCKED：不得声称量产或额定通过** |

## F. 2026-10-12 GitHub Actions 新鲜原理图/PCB证据（冻结裁决）

本轮在commit `c6f03144a70da6ab4fd168637f71472fcd8654e7` 的CI实机KiCad 10核查：

- [kicad-erc run #38209360502](https://github.com/magic-alt/fpga-servo/actions/runs/38209360502)：`kicad-cli sch erc --severity-all` 导出 **0 violations / 0 errors / 0 warnings**，原始工件可在run下载，随后按**原始不放宽**的板级一致性测试仍**FAIL**（158个元件 /135网络 /166 footprints）。这说明**现行8页原理图通过原生ERC，但生产PCB仍不匹配**。
- [hardware-sanity run #38209360509](https://github.com/magic-alt/fpga-servo/actions/runs/38209360509)：新6项ADS8588S双串行/防误配置回归**全部通过**，原生文本/网格/图面/连线检查通过；`check_design.py` **FAIL**：旧PCB还留J2，PCB缺DRV8300型号，U15焊盘与物理脚位不符，U5不存在，RSH1–3不符SMD制造封装/物理两脚，缺第4个shunt和已审核规则组。
- [gate-ab run #38209360634](https://github.com/magic-alt/fpga-servo/actions/runs/38209360634)：静态OCP/ADC工具与Gate A/B热/能量资格分开审查；最终关闭Gate A/B的必要动态/实验依据仍不可由这个工作流代替。

**发布状态仍严格保持** F0 DESIGN SELECTED、F1 MPN/全源设计冻结BLOCKED（L1规格及测量）、F2 PCB同步BLOCKED（独立[Issue #17](https://github.com/magic-alt/fpga-servo/issues/17)）、F3/F4实验/功率释放BLOCKED。L1专项由[Issue #18](https://github.com/magic-alt/fpga-servo/issues/18)追踪。

### 技术验收命令（须基于当前分支真实执行，不能使用旧日志冒充）

```sh
python tools/pcb.py check --project ads8588s --scope schematic
python tools/pcb.py test --lane static --pattern test_adc_serial_contract.py

# 需要KiCad 10本机环境，并且本分支原理图已同步本机库：
kicad-cli sch erc --exit-code-violations --severity-all hardware/ads8588s_servo/ax7010_servo_reva.kicad_sch
kicad-cli sch export netlist --format kicadxml --output /tmp/reva_latest.xml hardware/ads8588s_servo/ax7010_servo_reva.kicad_sch
python tools/pcb.py check --project ads8588s --scope schematic
```

本轮任何Github CI的绿色也只能证明其包含的静态/原生语法和脚位检查；**电气/热/保护动态与生产冻结必须独立签署**。工程不因这一组源文件的小修而获得送厂资格。

### 权威依据

- [ADS8588S datasheet](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)
- [LM5164 datasheet](https://www.ti.com/lit/ds/symlink/lm5164.pdf)
- [DRV8300 datasheet](https://www.ti.com/lit/ds/symlink/drv8300.pdf)
- [SXN SMDRI127 68µH原厂手册](https://atta.szlcsc.com/upload/public/pdf/source/20210810/6F96FDC19AA308DD2AD166FFB9640E87.pdf)
- [既有量产释放门禁](release_gates.md)，[PCB同步Issue #17](https://github.com/magic-alt/fpga-servo/issues/17)。
