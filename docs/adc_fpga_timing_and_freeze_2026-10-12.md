# Rev.A-P ADS8588S / AX7010 FPGA 双串行接口与冻结时序合同

- 审查日期：2026-10-12
- 源自：PR #16 / `review/reva-simplified-production-design-20261011`
- 硬件目标：24–48V单轴PMSM/BLDC、20kHz PWM、3路相线电流同时采样
- **状态：ADS8588S接口架构和使用策略可冻结（DESIGN DECISION）；真实ADC与FPGA联合时序、驱动波形和PCB仍未通过实板/STA资格（NOT FOR FABRICATION）。**

## 1. 结论：同时采样≠全通道并行数据输出

TI [ADS8588S SBAS642A数据表](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)：
- 8路16-bit SAR**同时取样**，每通道200kSPS**最高**，并不表示8路独立的16-bit输出接口；
- 支持DB[15:0]并行、8-bit byte-wide，以及串行输出。当前焊盘、引脚和FPGA J10使用 **PAR/SER/BYTE SEL=1、DB15/BYTE SEL=0、两路DOUTA+DOUTB**，不是16位并行总线，也不应依赖不存在的J11；
- DOUTA首先按CH1、CH2、CH3、CH4输出，DOUTB同时按CH5、CH6、CH7、CH8输出；**64个SCLK**足够8路完整的128-bit采样帧；如果只用一条DOUT则要128个SCLK；
- 串行tSCLK **≥50ns**，物理最大20MHz。sclk高、低时间各占45%～55%，输出SCLK上升沿至DOUT数据有效**最长15ns**，FPGA按手册的**下降沿取数**，并为J10缆线、布线、输入建立、时钟相位和时序抖动留出额外预算；特别注意20MHz的半周期最坏高电平只有22.5ns，扣15ns数据有效延迟仅剩7.5ns用于其他延迟，不能直接宣称原理图支持稳定20MHz。
- 无过采样情况下8通道BUSY转换时间3.7～3.9µs（典型3.8µs）。若**等转换完成才双串行读取**，官方最短ADC cycle规格为**9.7µs**；若**在新一轮转换期间读取旧一帧**，并满足20MHz/64时钟数据带宽，最短cycle为**5µs（理论200kSPS）**，但引入上一帧数据的明确时间归属。
- 当前选OS[2:0]=000、RANGE=0（±5V）、内部参考，以及PAR/SER=1/DB15=0；不要把过采样打开后还声称200kSPS。OSR=2时最大BUSY约8.8µs，OSR=4约18.5µs。以上模式引脚映射仍需用**最新原生KiCad网表**逐引脚确认。

## 2. 双串行时序表（数值不包括转换及控制等待）

| 读出路径 | SCLK | 单帧时钟数 | 单帧理想持续时间 | 当前设计 |
|---|---:|---:|---:|---|
| DOUTA+DOUTB | 20MHz | 64 | 3.2µs | 数据手册最大、STA/实体J10缆线资格开放 |
| DOUTA+DOUTB | **10MHz** | 64 | **6.4µs** | **推荐首版HDL/台架保守目标** |
| DOUTA单线 | 20MHz | 128 | 6.4µs | 不是当前布线计划 |
| DOUTA单线 | 10MHz | 128 | 12.8µs | 只允许调试低速，不作为正式路径 |

公式：`t_read_us = 16 × channels / (lanes × f_sclk_MHz)`。固定20kHz PWM周期 `50µs`：以10MHz双串行为例，**完成转换后再读出**的近似组合占用至少 `3.9+6.4=10.3µs`（还需CS设置/保持、BUSY同步、FRSTDATA、FPGA状态机与调度裕量）。所以20kHz下一周期一组三相电流读取有充裕的**数字接口**余量；这不等于整个模拟链/FOC控制没有延迟。

当目标提高到100kSPS或200kSPS：
- 10MHz双串行的64时钟读出已占6.4µs，因而**不能在5µs周期中输出一整帧**，实际吞吐必降至小于约156k完整帧/秒（尚未包含裕量）。这是数据带宽限制，与8通道是否同时取样无关。
- 20MHz双串行可以把64时钟缩到3.2µs，才有机会在5µs周期内交错读旧帧达到200kSPS；必须使用**转换中读取前一帧**方案，并验证BUSY、CS/SCLK相位、FRSTDATA及轮次关联。
- 数据手册的9.7µs后读最短周期不应被3.9+3.2的理想算术结果擅自覆盖，最短周期以原厂表格为准。

## 3. 20kHz PWM + FPGA FOC推荐时序（不改原理图采样拓扑）

```text
20kHz中心对齐PWM / 每50µs一周期
        ↓
避开MOSFET硬开关沿的稳定窗口发起ADC_CONVST
        ↓ 8路同时取样（非通道轮询）
ADC_BUSY=1 (最大约3.9µs，无过采样)
        ↓
BUSY下降沿同步；CS_N拉低；10MHz SCLK读64个时钟
        ↓
DOUTA: Iu, Iv, Iw, VBUS
DOUTB: NTC1(board), NTC2(board aux), CH7, CH8
        ↓
检查FRSTDATA/完整帧计数；锁存 timestamp + 有效标志
        ↓
电流零点/增益校准 → Clarke/Park → Id/Iq PI → SVPWM
        ↓
下一约定的PWM影子寄存器更新边沿生效
```

**额定控制**优先方案：每个PWM周期一个固定相位CONVST，低速模式每周期读一次最新转换，SCLK先10MHz，CH7/8的数据仍需完整移出以保持固定帧顺序。输入通道的取样瞬时相同，不代表数字数据必须在同一刻读完。

若ADC BUSY超时、FRSTDATA错位、上/掉电不足或采样周期丢失，**禁止将旧数据误标为新样本**，将帧标记无效并转向安全策略；该故障路径必须经过FPGA实际RTL设计和测试。当前项目仍没有已验证的合成RTL、时序报告，本文不能替代RTL交付。

## 4. 关键但易忽略：模拟带宽与电流环相位裕量

TI ADS8588S的每路集成三级Butterworth反混叠LPF，在 **±5V RANGE=0时模拟-3dB约16kHz**，±10V模式约24kHz。它不是一个无延迟SAR采样引脚。数据手册Figure 56显示模拟相位延迟随频率变化，应针对预定电流环交越频率估算/实测。当前外接R40–R42=47Ω、C40–C42=1nF，RC本身约3.39MHz的截止频率，无法替代PWM尖峰抑制与专业采样窗口。

冻结结论：
1. 20kHz PWM采样的**数字吞吐**可行，不等于20kHz电流环闭环带宽可达；
2. FOC采样延迟至少包含模拟INA240动态恢复、ADC模拟LPF频域响应、BUSY转换、串行读出、RTL同步/计算、PWM影子更新。三相必须通过共同时间戳对齐，PWM边沿附近的共模恢复需实测；
3. 不建议在Rev.A为了更高纸面ksps将ADC改为不同时采样的多路复用ADC。ADS8584S仅四通道会失去当前总线/两路NTC的共同采样资源，改动FPGA/模拟链/PCB，须另行成本版评审；
4. 若要求电流环极高带宽或极低相位延迟，应**重新比较更低模拟前端群延迟的ADC**，不能把提升SCLK误当成改善内置模拟滤波器相位延迟。

### 模拟相位延时不能用提升SCLK消除

原厂[ADS8588S数据手册Figure 56（PDF第28页）](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)给出了±5V档片内三级Butterworth LPF的**模拟相位延时在低频约20µs**，随频率变化；这是一项独立于FPGA双串行读出（6.4µs@10MHz）的模拟链路延迟。按简单纯时延做频率预算，20µs在1/2/3/5kHz交越频率分别贡献约7.2°/14.4°/21.6°/36°的相位滞后；**这些仅为定性量级估算**，实际不等同于含INA240、采样保持/数字处理与PWM更新的完整环路相位。对20kHz PWM，若目标电流环带宽接近3kHz或更高，需先完成全链路实测频响和PI补偿验证，不能仅凭200kSPS的采样速率宣称高速伺服性能。

## 5. 工程实际连接和16位模式

| 功能 | PL_A / AX7010 J10 FPGA封装脚 | 信号 |
|---|---|---|
| ADC触发 | Y14 | ADC_CONVST（两个内部转换组同时触发需要按最新网表/示波确定） |
| ADC串行时钟 | W14 | ADC_SCLK |
| CS | P18 | ADC_CS_N |
| RESET | N17 | ADC_RESET |
| 数据lane A | U15 | ADC_DOUTA |
| 数据lane B | U14 | ADC_DOUTB |
| BUSY | P16 | ADC_BUSY |
| 第一字 | P15 | ADC_FRSTDATA |

当前KiCad层级图中存在这8条信号，J10导线可追踪；**J11 PL_B根本没有装配**，`fpga/ax7010_servo_reva.xdc`中的J11参考分配现仅保留为注释。以后若需要硬件16bit并行接口，必须增加真实线束/连接器和引脚/模式重布，不能只取消XDC注释。

## 6. 源文件检查、验收及冻结结论

新增 `tools/check_adc_serial_contract.py`：
- 判断8条实际J10 ADC信号、双DOUT的原理图层级接口和XDC脚约束；
- 禁止未安装J11的平行数据引脚被误用成Vivado有效端口约束；
- 锁定CH6只描述板载NTC2、不宣称电机绕组温度；修正C3实际250V额定描述；提醒L1电流额定仍需资格；
- 检查64/128时钟、20MHz和20kHz周期计算。

本检查仅是文字和接口静态合同，不断言ADC DB15/PAR/SER实际铜网络正确或RTL时序完成：必须另从**新鲜KiCad XML网表**校核模式strap、CONVSTA/B、ADC各物理供电/输入引脚，进行原生ERC；实机逻辑分析仪测量SCLK上升/下降沿、FRSTDATA、BUSY、CONVST和双DOUT，并以AX7010 Vivado的I/O setup/hold时序报告与实际接线核对。

**冻结等级**：ADC器件及双串行架构 **DESIGN SELECTED**；器件数量/引脚的原理图文字一致性在静态检查通过后可作为接口交付；**SPI/QSPI速率、RTL、真实模拟群延迟、PCB、系统故障安全不视为已经验证或生产冻结。**

## 7. 原厂参考

- [ADS8588S datasheet SBAS642A](https://www.ti.com/lit/ds/symlink/ads8588s.pdf)：p12 tSCLK/p13 tCYC/p14 tCKDO/p42–43双串行帧/p28模拟LPF；
- [ADS8588S产品页](https://www.ti.com/product/ADS8588S)：200kSPS/ch、8路同时采样/并串接口；
- [LM5164 datasheet](https://www.ti.com/lit/ds/symlink/lm5164.pdf)：12V/1A参考68µH、饱和电流需要显著高于器件限流。
