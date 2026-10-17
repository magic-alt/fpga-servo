# FPGA-Servo Rev.A 高速电流环 ADC 重新选型与迁移规格（2026-10-12）

> 2026-10-17 状态补充：本文保留选型与迁移依据；下文“未实施”描述 ADS8588S 原工程。AD7606C 独立原理图已实现，见 [新工程](../hardware/ad7606c_servo/README.md)；PCB/RTL/STA/实物资格仍未完成。

> **选型裁决：高速版首选 ADI AD7606C-16BSTZ（LCSC C5371769），采用 8路同时取样 + FPGA J10 的四路并行串行输出；板上现用 ADS8588SIPM 尚未更换。** 本文是面向实现的电气/FPGA接口ECO规格，当前电气工程仍基于 ADS8588S，不得把这份方案称作已通过原生ERC、PCB同步、样机测试或已冻结生产MPN。受控版本始终保留历史设计可追溯性。

## 1. 任务边界与排序指标

- 当前系统：AX7010 2022 版 J10 实际线缆接口；24–48V，三相 INA240A1DR 20V/V + 5mΩ，每路灵敏度 0.100V/A、零点约 2.55V；20kHz PWM，10Arms连续 / 20A短峰值；另外VBUS分压和两路板载NTC，总共六路有效模拟量。
- 新目标：支持电流环交越3–5kHz及潜在更高的实验；以**模拟前端相位延迟、同时取样时刻偏差、采集到PWM更新的总延迟、抗PWM瞬态/信噪比、FPGA同周期并行收数**为排序优先级，之后再是采购/功耗/PCB复杂度。
- 改善 ADC 不代表软件电流环可立即稳定到5kHz。原20kHz PWM 的50µs周期、ADC触发到本周期或下周期PWM shadow load、驱动电流采样和PI计算，仍须做离散控制频响与全链路时序预算。若5kHz目标无法满足相位裕量，应审查40–80kHz PWM选项及相应 MOS 开关损耗/热；不是只换ADC。
- 不能把**1MSPS/channel**误写成**FPGA能同时读出8路16bit的独立并行总线**。AD7606C-16实现8个SAR同步采样，有16bit并行接口，以及1/2/4/8个DOUT分道的串行接口；不需要为了FPGA而强行采用16位平行排针。

## 2. 推荐器件和可生产采购的代价

| 优先级 | 具体器件 | 合规性/速度 | 与现有板配合 | 当前参考采购与风险 |
|---|---|---|---|---|
| 首选 HIGH-BW | **ADI AD7606C-16BSTZ** (C5371769) | 8ch/16b同时采样、1MSPS/ch；0–5V高速模式**150kHz −3dB**、典型**1.7µs phase delay**；其他量程可到220kHz/1.1µs | 单5V模拟+3.3V逻辑，不需负电源；0–5V覆盖三路INA电流输出；4路DOUT适配J10仅加3根信号；需重新绘制64脚原理图与连接 | [LCSC](https://www.lcsc.com/product-detail/C5371769.html)，国际站网页缓存约**US$47.8659/颗**、188件快照、MOQ1；**不是人民币报价或库存锁定** |
| 包装备选 | **ADI AD7606C-16BSTZ-RL** (C5240947) | 同电气芯片、同LQFP-64；卷带 | 可作为同料号不同包装条件候选，不作为其他厂商2nd-source | [LCSC](https://www.lcsc.com/product-detail/C5240947.html)：近期网页标US$53.7103–59.1322单件，库存页面间不一致，必须以实际下单为准 |
| 次选，成本敏感 | **TI ADS8568SPMR** (C2670843) | 8ch/16b，510kSPS并行或400kSPS串行，约1.7µs转换，4路串行/16bit平行 | **需HVSS负模拟电源**及HVDD正模拟电源，当前无负电源；输入调理、板面积、EMI和启动连锁的增量成本高 | [LCSC](https://www.lcsc.com/product-detail/C2670843.html) 最新缓存US$22.65、库存903；不能将裸芯片差价视为整板成本节约 |
| 极低延迟特殊版 | **TI ADS9224R** | 双通道16b/3MSPS、333ns级延迟，差分输入 | 至少两颗覆盖三相，再增加一组慢速采集器件，并重新设计INA240输出/差分输入与供电 | 不适合作为当前六路采集一颗替换 |
| 高速四通道替代 | **ADI AD7386-4** | 4ch/16b/4MSPS、4lane读数 | 现有0–5V模拟输出超出其0–VREF输入；还需额外慢速ADC读VBUS/NTC，增加模拟调理 | 高频特殊产品值得研究，当前Rev.A非最小可制造修改 |
| 原方案 | **TI ADS8588SIPM** (C1543171) | 8ch/16b、200kSPS、双DOUT，每8ch需64clk；±5V档内部LPF约16kHz、约20µs相位延迟 | 现有可工作原理图选型；没有高速电流环性能优势 | 原仓库人民币快照**¥40.82/板**，不可以把US$与CNY裸数比较 |

**结论**：AD7606C-16以更高采购单价交换显著降低的模拟相位延迟，较多颗ADC+额外负电源/模拟差分驱动方案简单、可追踪。它仍是单来源关键IC；以速度优先的实验板可以买到，但对最终成本敏感的量产版应保留独立竞争路线。**没有经销商真实人民币报价，不给出虚假整板最终成本。**

## 3. 模拟前端和通道量程：利用现有INA240输出，无需±模拟电源

| ADC通道 | 对应信号 | 新输入模式 | LPF模式 | 验收要点 |
|---|---|---|---|---|
| CH1 | INA240 IU_ADC | **0–5V unipolar** | 高速 | 2.55V零点，±20A理想0.55–4.55V；上下额定输入理想约0.45V余量，INA零点/增益/供电/纹波/动态过冲的最差角点必须重算，不能承诺故障期间永不饱和 |
| CH2 | IV_ADC | 0–5V | 高速 | 相同增益/温度漂移校准 |
| CH3 | IW_ADC | 0–5V | 高速 | 三相采样物理时标一致 |
| CH4 | VBUS_ADC | **0–10V unipolar** | 高速 | 48V正常母线约3.125V，保留浪涌观测余量；ADC通道**不等于独立硬件OV保护** |
| CH5 | NTC_BOARD | **0–10V unipolar** | 低速 | 板载NTC分压最高可能随5.1V供电接近5.17V，0–5V模式可能饱和，所以预设0–10V |
| CH6 | NTC_BOARD_AUX | 0–10V | 低速 | 板载二号温度，不等于远端电机绕组NTC |
| CH7,CH8 | 保留/接地 | 0–10V | 低速 | 未用通道按ADI手册接AGND，完整帧仍包含其数据 |

模式下**单极性数据为 straight binary**，不是原ADS8588S双极性 two's-complement 编码。对于CH1–3，理想电压为`V = raw * 5V / 65536`；`I_phase = (V - Vzero_calibrated)/gain_calibrated`，不能简单把旧码直接复用。0–5V理想LSB=76.3µV，对0.1V/A为**0.763mA/LSB**（仅量化步距，不是有效精度）。ADI表2显示高速0–5V SNR典型**80dB**，相当于约13有效位的噪声量级；放大器动态失调、ADC数据手册TUE、线束共模、温漂与PWM瞬态实际占优。温度/母线选择0–10V量程使数字比例另行计算。

**抗混叠权衡**：原ADC自带16kHz低通一定程度抑制开关高频，新ADC高速模式0–5V带宽150kHz，不能假定抗开关噪声相同；现有三路INA→ADC仅47Ω/1nF截止约3.39MHz，几乎没有有效PWM频率抗混叠。正式电气ECO必须在INA240输出纹波恢复/PWM中心触发窗口和ADC噪声间联合选取RC（可测100–300kHz候选，不先锁定），同时计算该RC本身的额外群延迟，不能只看1.7µs芯片规格。

## 4. FPGA并行接收的最小改造（推荐四路DOUT）

**先只使用已装配的AX7010 J10（servo PCB J1），不恢复已取消的J11。**

| AX7010 J10 引脚 | Xilinx物理脚 | 新功能 | 本次硬件ECO |
|---|---|---|---|
| 11、12、13、14 | Y14、W14、P18、N17 | CONVST、SCLK、CS_N、RESET | 新AD7606C需按其**不同的芯片脚位**重新接入，J10端信号定义可沿用 |
| 15、16 | U15、U14 | DOUTA、DOUTB | 按AD7606C四lane顺序重新解码，原ADS8588S lane排序不能复用 |
| 17、18 | P16、P15 | BUSY、FRSTDATA | 保留逻辑功能但电平/时序重核对 |
| **29**（原SPARE_A0） | **U12** | **DOUTC** | 新增1个DOUT，从ADC至J1并添加XDC |
| **30**（原SPARE_A1） | **T12** | **DOUTD** | 新增1个DOUT，从ADC至J1并添加XDC |
| **31**（原SPARE_A2） | **T10** | **ADC_SDI** | 新增配置写入MOSI信号，用于软件模式写寄存器及读回 |
| 32–36 | 其他当前空脚 | 预留 | 保持NC，暂不增加8lane线路 |

四lane读数顺序（每lane有两个16bit字）：
```text
          CONVST 同时采样 8路
                   │
               tCONV<=0.65us（无OS，datasheet最大）
                   │  BUSY 下降
              CS_N=0、SCLK
       ┌────────┬────────┬────────┐
       ▼        ▼        ▼        ▼
     DOUTA    DOUTB    DOUTC    DOUTD
     CH1      CH3      CH5      CH7    前16clk（4路FPGA移位寄存器并发）
     CH2      CH4      CH6      CH8    后16clk
       └────────┴────────┴────────┘
             CH1..CH8 完整帧
                   │
             帧valid + FPGA采样时间戳
                   │
         Iabc Clarke/Park/PI/SVPWM 并行流水
```
- 20MHz时32clk=**1.6µs**；40MHz时0.8µs，但即便ADI注明VDRIVE>=3.1V允许最高63.5MHz，J10 2.54mm多线线束的上升沿/回流/接收建立保持时间必须在实物及Vivado STA闭合之后才逐级提频。
- **8lane升级选项**：再占用SPARE_A3..A6的4个信号，共六新增DOUT（加SDI即占7个原空脚），16clk在20MHz理论0.8µs。升级仅节约0.8µs读取时间，相较全链路PWM更新/采样相位不一定值得线束、EDA和信号完整性成本。优先4lane。
- 不提议在现有J10单排线恢复所谓16位并行总线；那需要更多信号数量和更密的高速回流参考。

## 5. AD7606C-16 必需软件模式配置（候选镜像）

原图ADS8588S 的OS[2:0]=000与新芯片**完全不同**；AD7606C需要**OS2/OS1/OS0全部置1**进入software mode。PAR/SER SEL=1，STBY=1（软模式建议），RANGE需绑稳定高/低（软模式忽略），内部参考REF_SELECT=1，AVCC = 当前标称5.1V，VDRIVE = FPGA3.3V；所有电气脚位、参考旁路及新增Vx−必须按新器件datasheet而非旧U6封装编号连接。

| 寄存器地址 | 写入值 | 目的 | 核验方式 |
|---|---|---|---|
| `0x02 CONFIG` | `0x10` | [4:3]=10选四路DOUT，status header关闭，normal mode | 软件读回，断电重新配置 |
| `0x03 RANGE_CH1_CH2` | `0x55` | CH1/CH2均0–5V |
| `0x04 RANGE_CH3_CH4` | `0x65` | CH3=0–5V，CH4=0–10V |
| `0x05 RANGE_CH5_CH6` | `0x66` | CH5/CH6均0–10V |
| `0x06 RANGE_CH7_CH8` | `0x66` | 两路保留/0–10V |
| `0x07 BANDWIDTH` | `0x0F` | CH1–CH4高速（bit0..3=1），NTC等低速 |
| `0x08 OVERSAMPLING` | `0x00` | OSR1，禁用数字过采样以免增加控制延迟 |

**寄存器只是已审查的配置提议**；配置前后必须执行完整复位时序、以设备ID核对具体硅版本、读回验证关键寄存器，返回ADC正常读数模式。ADI的寄存器写入需SDI、SCLK、CS组合，不能把表格值作为“上电自动有效”。FPGA不得在模式不明、VA5欠压或新样本无效时把旧帧误用作有效三相电流；应保持`GATE_EN=0`直到ADC_CONFIG_OK和健康链同时有效，失帧按经过资格的故障政策处理。保留当前独立母线OCP硬件保护，不允许用“ADC更快”取代。

## 6. 控制链延迟与PWM频率约束

| 项目 | ADS8588S目前方案 | AD7606C-16拟定方案 |
|---|---:|---:|
| 片内模拟相位延迟（典型、相应量程） | 约20µs | **1.7µs**（0–5V、high BW） |
| 16bit八通道一次采样 | 同时采样 | 同时采样 |
| 本板当前读帧，约20MHz | 双lane 64clk=3.2µs | 4lane 32clk=1.6µs |
| 采集芯片转换时间 | 最大约3.9µs | 最大0.65µs（无OS） |
| 额定采样率上限 | 200kSPS/ch | 1MSPS/ch |

*注意phase delay已经包含模拟前端加到结果可读的时域表现，不能简单把1.7µs与0.65µs当成互不重叠的两个固定延迟相加。* 控制环还含INA240/PWM尖峰、外部滤波、J10线束、FPGA同步/FOC计算和PWM寄存器边界，实际按新旧样机采样时间戳与VGS/编码器/电流响应测量。

仅按纯延迟估算`phase_lag_deg=360 × f_c × latency_s`：
- 5kHz交越，20µs模拟延迟约36°；1.7µs约3.06°，差约33°，理论改善显著；
- 20kHz PWM周期是50µs；如果控制律必须等到下一PWM边界更新，额外25µs/50µs延迟在5kHz分别产生约45°/90°相位滞后。ADC换芯**不能弥补PWM调度延迟**。
- 高速控制目标建议先把PWM及采样更新划定20k/40k/60k三种候选，并根据MOSFET损耗/温升、FPGA并行流水线与延迟实测确认5kHz闭环稳定性，而不是默认即刻提高到60kHz。

## 7. KiCad/ECO修改工作合同（不允许仅换Value/MPN）

1. **独立原理图子页ECO**：新建AD7606C-16本地可审计原生KiCad符号，逐芯片物理脚对厂商Rev.A PDF，封装LQFP-64 10×10mm/0.5mm；虽与现用U6机械封装类似，绝不假设引脚完全兼容。
2. **模拟电路**：新增各通道正确VIN+/VIN−接法和输入保护/滤波；按OEM建议布置REFIN/REFOUT、REFCAPx及多AVCC/GND旁路，切勿直接套用ADS8588S的REGCAP、REFCAP器件及管脚；评估现有5.1V TPS62901负载、电容与U25欠压联锁（ADI AVCC最低4.75V，当前仅静态裕量）。
3. **数字电路**：软件模式OS0/1/2=111、PAR/SER=1、SDI、DOUTC/D；更新AX7010 J10连接器物理pin29/30/31、`fpga/ax7010_servo_reva.xdc`真实信号和板端J1铜、`docs/ax7010_interface.md`映射，确保新IOSTA/LVCMOS33 IO bank与Vivado实际冲突检查。
4. **BOM及成本**：新U6准确厂商、MPN、LCSC C5371769，C5240947仅作为包装备选；根据实际器件重新整理所需去耦/稳压/参考器件与DNP，更新分组采购和五板价额。实际采购前刷新单价/币种/现货/发票/进口。
5. **FPGA RTL**：独立ADC驱动状态机、初始化寄存器读回、BUSY超时、采样触发调度、4个并行16bit移位器/帧对齐、固定时间戳/有效标记和CRC/模式回归；记录Vivado STA实际 SCLK IO delay和J10端波形，不得依赖不存在的J11。
6. **资格分层**：新鲜KiCad全严重度ERC0、物理脚/节点网表检查、真实PCB全部端点一致且DRC0/未连接0/DFM通过；逻辑/有源电路仿真与实际硬件低能量PWM噪声、ADC线性/频响、FPGA 20MHz/40MHz校验；维持独立硬件OCP及VA5动态关断门禁BLOCKED直到实测。

### PR #16 新鲜源检查（不等于目标器件已应用）

[GitHub hardware-sanity #38211317168](https://github.com/magic-alt/fpga-servo/actions/runs/38211317168) 证实新增候选规格脚本**PASS**，其7项含错误注入回归全部PASS；旧ADS8588S源检查6项亦PASS。正式`check_design.py`仍FAIL，原因是本来就没有与当前BOM/母线OCP相同的PCB，不是ADC候选规格脚本的通过就能解除的PCB门禁。

[GitHub kicad-erc #38211317075](https://github.com/magic-alt/fpga-servo/actions/runs/38211317075) 在本次提交的**旧ADS8588S原理图**上运行原生KiCad10得到**ERC 0 errors / 0 warnings / 0 violations**，并导出158板载器件/135网络网表；`check_pcb_parity.py`依旧FAIL（166 footprints旧板），因此整项工作流为失败状态。**不能把这个ERC0当作AD7606C新原理图ERC已通过。** 原硬件保护Gate A/B、L1及PCB制造资格保持BLOCKED；独立[迁移Issue #19](https://github.com/magic-alt/fpga-servo/issues/19)负责后续真实ECO。

## 8. 最终状态与设计决定

**Performance ADC SELECTED = AD7606C-16BSTZ / 4lane / unipolar 0–5V three current + 0–10V housekeeping / no oversampling / high bandwidth CH1..4。**

**Working hardware still ADS8588S；FAST ADC electrical ECO/PCB freeze NOT IMPLEMENTED、NOT FOR FABRICATION。** 本文不篡改PR #16已有通过的ADS8588S双串行静态回归；迁移成功前应对两种工程状态分别检查、不能同一套原理图声称既保留旧ADC引脚又安装新ADC。

### 原厂与采购证据

- ADI [AD7606C-16 datasheet Rev.A](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf) —— Table2 (相位/带宽/SNR), Table3 (BUSY/转换), Table5 (串行频率), Table9 (芯片脚), Table14/15 (OS=111), Table26 (lane数量), Register0x02..0x08.
- TI [ADS8588S datasheet](https://www.ti.com/lit/ds/symlink/ads8588s.pdf), [ADS8568 datasheet](https://www.ti.com/lit/ds/symlink/ads8568.pdf), [ADS9224R datasheet](https://www.ti.com/lit/ds/symlink/ads9224r.pdf).
- [LCSC AD7606C-16BSTZ/C5371769](https://www.lcsc.com/product-detail/C5371769.html), [LCSC ADS8568SPMR/C2670843](https://www.lcsc.com/product-detail/C2670843.html).
- 当前工程[FPGA双串行旧方案](adc_fpga_timing_and_freeze_2026-10-12.md)及[器件冻结矩阵](reva_schematic_component_freeze_matrix_2026-10-12.md).
