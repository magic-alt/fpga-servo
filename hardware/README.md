# 硬件工程入口

两种 ADC 方案分别保存在独立目录中，各自包含 KiCad 工程、层次原理图、本地符号/封装库和 BOM。

| 方案 | 工程入口 | 说明 |
|---|---|---|
| ADS8588S 原方案 | [ads8588s_servo/ax7010_servo_reva.kicad_pro](ads8588s_servo/ax7010_servo_reva.kicad_pro) | [原方案说明](ads8588s_servo/README.md)；保留旧 PCB、采购表和成本快照 |
| AD7606C-16 新方案 | [ad7606c_servo/ax7010_servo_ad7606c.kicad_pro](ad7606c_servo/ax7010_servo_ad7606c.kicad_pro) | [新方案说明](ad7606c_servo/README.md)、[开发板方案](ad7606c_servo/development_board.md)、[原理图 PDF](ad7606c_servo/evidence/schematic.pdf) |

原 ADS8588S 工程文件名保持不变，目录内部相对路径和 `${KIPRJMOD}` 库引用仍然有效。原 FPGA XDC 仍位于 `../fpga/ax7010_servo_reva.xdc`；新方案的独立 XDC 位于 `ad7606c_servo/`。

仓库根目录的检查脚本默认检查 `ads8588s_servo/`。两个方案的完整原生检查入口为：

```powershell
E:\anaconda3\python.exe -X utf8 hardware/ad7606c_servo/tools/run_checks.py
```

目录整理不改变电气设计，也不解除发布门禁。原方案 PCB 的已知检查失败、新方案 PCB/RTL/STA/硬件实测的未完成状态保持不变，详见各方案说明和 [发布门禁](../docs/release_gates.md)。

`.history/` 与根目录原有 KiCad 锁文件是保留的本地状态；工程应通过上表中的新路径重新打开。
