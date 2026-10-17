# PCB 工具迁移记录

状态：实施中。设计与计划见 docs/superpowers 对应 2026-10-17 文件。

## 迁移前基线

Python 3.12.4；原生工具不在 PATH，后续使用显式本机参数验证，不把安装路径写入公共文档。

| 检查 | 退出码 |
| --- | --- |
| check_native_schematic | 0 |
| check_kicad_grid | 0 |
| check_schematic_layout | 0 |
| check_schematic_connectivity | 0 |
| check_power_wiring | 0 |
| check_adc_serial_contract | 0 |
| check_ad7606c_fast_profile | 0 |
| check_design | 0 |
| check_legacy_pcb_baseline | 0 |
| check_public_paths | 0 |
| tests | 1 |

旧测试发现 104 项，6 failures、3 errors、26 skipped；其中 ADC validity 缺少新鲜 XML。完整日志保存在本次本地临时证据中，不把这些失败当作迁移后引入。

## 入口迁移映射

完整映射以 [实施计划](superpowers/plans/2026-10-17-pcb-toolkit-docs.md#文件与迁移映射) 为准，交付时补充最终状态。
