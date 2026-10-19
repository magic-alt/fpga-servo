# 阶段 1：AD7606C 实装接口时序纠错

本阶段不修改电气连线、器件或 PCB 铜路。基线时序配置缺少 TXU0204 往返链路的数值约束，原有回归不能拒绝错误的时序资格声明。新增七项定向测试，先在旧实现观察到八个断言失败，修复后七项全部通过；连同既有 AD7606C 候选测试，本地 14 项通过。完整原生与 PCB 验证由本提交的受控 ECO 工作流执行，完成前不宣称通过。

## 厂商依据与结论

- TI TXU0204 SCES936A §7.11：VCCA=3.3±0.3 V、VCCB=5±0.5 V、-40..125°C，A→B 最大 9 ns，B→A 最大 10 ns。§8.1 测试负载为 5 pF/10 kΩ；实际 RC、走线及 FPGA 输入负载不能自动等同此条件。原文：https://www.ti.com/lit/gpn/txu0204 。
- ADI AD7606C-16 Rev.A 表 5：VDRIVE≥3.1 V，SCLK 上升沿后 DOUT 最大访问时间 15.7 ns；表 3 无过采样转换最大 0.65 µs。原文：https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf 。
- 9+15.7+10=34.7 ns。以 FPGA 同一 SCLK 的随后下降沿、50% 占空比作参考，20 MHz 仅有 25 ns，尚未计板级延迟就差 9.7 ns；5 MHz 有 65.3 ns 原始剩余预算，但未实现 RTL/STA/负载资格，不能称为已验证裕量。

保留 5 MHz 首次调试；20 MHz 仅是需要专门采样相位或接口时序设计的目标，不声称芯片无法更快。新增配置与 XDC 注释明确 launch/capture 边沿、全温界限、测试负载、未定板级预算、首位 CS/MSB、SDI 与 setup/hold 条件。150 kHz、1.7 µs 是当前 0–5 V 高带宽模式典型模拟参数，不是电流环最坏保证。

## 可恢复提交机制

`eco/current.patch` 与逐文件修改前/后 SHA256 明確保存本阶段实际修改，避免大 KiCad 文件或会话临时工作丢失。仅在本仓库指定审核分支执行；文件不满足全部 before 或全部 after 状态时拒绝覆盖。ECO 经完整回归、两板新鲜 ERC/DRC/parity/几何检查后才生成真实源文件 Git commit，不推送 main，不强制推送，也不代签制造批准。补丁传输使用 LF，原硬件文件的 CRLF 在受控清单内恢复并核验精确最终字节。

补丁提交并不等于已应用完成；以工作流实际产生的 `verified-revision.txt`、源归档和 PR 中的源文件提交为准。
