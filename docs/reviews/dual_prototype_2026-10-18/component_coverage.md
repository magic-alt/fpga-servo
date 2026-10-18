# Exact native component coverage

Current source inventory exported by KiCad 10.0.3 on 2026-10-19. This verifies source identities and physical pin membership only; it does not certify PCB synchronization, manufacturing acceptance, availability, or bench results. Historical 159/181-object evidence remains in [baseline inventory](component_inventory_baseline_2026-10-18.json). Native counts include DNP and external J6. Test points are copper features rather than implied purchased exact MPNs.

## ads8588s

180 components / 145 nets / 634 memberships; 179 board objects; 174 fitted board objects including5 bare-copper testpoints;169 purchased fitted components. DNP: D1, R32, RT1, RT2, RT3. J6 excluded from board.

| Sheet | References | Value | Exact MPN | Footprint | Native assembly |
| --- | --- | --- | --- | --- | --- |
| aux_power.kicad_sch | R32 | 100k | (generic geometry / DNP) | Resistor_SMD:R_0603_1608Metric | DNP |
| aux_power.kicad_sch | R20 | 100k | 0603WAF1003T5E | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | R95 | 10k | PTFR0603Q10K0N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C133 | 10nF | 0603B103K101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | L1 | 150uH | 7447709151 | fpga-servo:Wurth_WE_PD_1210_7447709151 | fitted |
| aux_power.kicad_sch | C24 | 2.2nF | 0603B222J500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | C20, C21 | 2.2uF | 1210B225K101NT | Capacitor_SMD:C_1210_3225Metric | fitted |
| aux_power.kicad_sch | L2 | 2.2uH | SWPA4020S2R2MT | fpga-servo:Sunlord_SWPA4020S | fitted |
| aux_power.kicad_sch | R23 | 200k | RC0603FR-07200KL | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C22, C23 | 22uF | 1210B226K250NT | Capacitor_SMD:C_1210_3225Metric | fitted |
| aux_power.kicad_sch | C30, C31, C132 | 22uF | GRM32ER71E226KE15L | fpga-servo:Murata_GRM32_1210 | fitted |
| aux_power.kicad_sch | C25 | 3.3nF | GRM1885C1H332JA01D | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | R21 | 442k | RT0603BRD07442KL | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | R22 | 49.9k | RT0603BRD0749K9L | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C26 | 56pF | 0603CG560J500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | R94 | 75k | PTFR0603Q75K0N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | U12 | LM5164DDAR | LM5164DDAR | fpga-servo:TI_DDA0008B_LM5164 | fitted |
| aux_power.kicad_sch | U13 | TPS62901RPJR | TPS62901RPJR | fpga-servo:Texas_RPJ0009A_VQFN-HR-9_1.5x2mm | fitted |
| aux_power.kicad_sch | TP3 | TP_12V | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| aux_power.kicad_sch | TP4 | TP_5V | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| ax7010_interface.kicad_sch | R80, R81, R82, R83, R84, R85, R86 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ax7010_interface.kicad_sch | J1 | AX7010_PL_A | 321040SG0ABK00A01 | fpga-servo:JILN_3210_2x20_P2.54mm_D1.02 | fitted |
| current_adc.kicad_sch | C43, C44, C45, C84, C85 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| current_adc.kicad_sch | NTC1, NTC2 | 10k | CMFA 103F3950 | fpga-servo:NTC_0603_Shiheng_KUU | fitted |
| current_adc.kicad_sch | R70, R71 | 10k | TD03G1002BT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | C60, C61 | 10uF | HGC0805R7106K250NSLJ | Capacitor_SMD:C_0805_2012Metric | fitted |
| current_adc.kicad_sch | C40, C41, C42 | 1nF | 0603CG102J101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| current_adc.kicad_sch | C62, C63, C64, C65, C66, C67, C68 | 1uF | 0603B105K250NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| current_adc.kicad_sch | R53 | 2k | TD03G2001BT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | RSH4 | 2mR | HoYLR2512-3W-2mR-1% | fpga-servo:HoYLR2512_Kelvin | fitted |
| current_adc.kicad_sch | R54 | 4.7k | RS-03K4701FT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | R40, R41, R42 | 47R | RS-03K47R0FT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | R50 | 8.2k | PTFR0603B8K20P9 | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | U6 | ADS8588SIPM | ADS8588SIPM | Package_QFP:LQFP-64_10x10mm_P0.5mm | fitted |
| current_adc.kicad_sch | U2, U3, U4, U5 | INA240A1DR | INA240A1DR | fpga-servo:TI_D0008A_SOIC8_P1.27mm | fitted |
| current_adc.kicad_sch | U15 | LM393LVDDFR | LM393LVDDFR | fpga-servo:TI_DDF0008A | fitted |
| dc_link.kicad_sch | R120, R121, R122, R123, R124, R125, R126, R127, R128, R129 | 0.33R | WSL2512R3300FEA | fpga-servo:Vishay_WSL2512_0R33 | fitted |
| dc_link.kicad_sch | C1, C2, C120, C121, C122, C123, C124, C125, C126, C127 | 100uF | EKZN101ELL101MJ20S | fpga-servo:NCC_KZN_D10_P5_Courtyard11 | fitted |
| dc_link.kicad_sch | J7 | EXT_SINK | 1714971 | fpga-servo:PhoenixContact_MKDS_5_2_9.52mm | fitted |
| encoder.kicad_sch | F2 | 0.5A_PTC_ENCODER_5V | ASMD1812-050 | Fuse:Fuse_1812_4532Metric | fitted |
| encoder.kicad_sch | C70 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| encoder.kicad_sch | RT1, RT2, RT3 | 120R | (generic geometry / DNP) | Resistor_SMD:R_0603_1608Metric | DNP |
| encoder.kicad_sch | C71 | 4.7uF | CGA0805X7R475K250MT | Capacitor_SMD:C_0805_2012Metric | fitted |
| encoder.kicad_sch | J5 | ABZ_DIFF_ENCODER | 321010SG0ABK00A01 | fpga-servo:JILN_3210_2x05_P2.54mm_D1.02 | fitted |
| encoder.kicad_sch | U7 | AM26LV32EIPWR | AM26LV32EIPWR | Package_SO:TSSOP-16_4.4x5mm_P0.65mm | fitted |
| encoder.kicad_sch | U19 | TPD6E05U06RVZR | TPD6E05U06RVZR | fpga-servo:TI_RVZ0014A_W025 | fitted |
| gate_inverter.kicad_sch | R56, R57, R58, R59, R60, R61 | 100k | RS-03K1003FT | Resistor_SMD:R_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | C46, C80, C81, C82, C83 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | R55, RGS1, RGS2, RGS3, RGS4, RGS5, RGS6 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | C69 | 10uF | CGA1206X7R106K250NT | Capacitor_SMD:C_1206_3216Metric | fitted |
| gate_inverter.kicad_sch | RG1, RG2, RG3, RG4, RG5, RG6 | 33R | CRCW060333R0FKEAHP | fpga-servo:Vishay_CRCW0603_HP | fitted |
| gate_inverter.kicad_sch | CBOOT1, CBOOT2, CBOOT3 | 470nF | 0805B474K500NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| gate_inverter.kicad_sch | RSH1, RSH2, RSH3 | 5mR | HoYLR2512-3W-5mR-1% | fpga-servo:HoYLR2512_Kelvin | fitted |
| gate_inverter.kicad_sch | Q1, Q2, Q3, Q4, Q5, Q6 | BSC040N10NS5 | BSC040N10NS5 | Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm | fitted |
| gate_inverter.kicad_sch | U1 | DRV8300DPWR | DRV8300DPWR | Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm | fitted |
| gate_inverter.kicad_sch | J4 | MOTOR_UVW | KF950-9.5-3P | fpga-servo:KEFA_KF950_3_9.50mm_D1.85 | fitted |
| gate_inverter.kicad_sch | U11 | SN74LVC1G11DCKR | SN74LVC1G11DCKR | Package_TO_SOT_SMD:SOT-363_SC-70-6 | fitted |
| gate_inverter.kicad_sch | U8, U9, U10 | SN74LVC2G08DCUR | SN74LVC2G08DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | R89 | 100k | RS-03K1003FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C86, C87, C88, C89, C90, C91, C93 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C94 | 100nF | GRT31C5C1H104FA02L | Capacitor_SMD:C_1206_3216Metric | fitted |
| ocp_latch.kicad_sch | R87, R90, R91 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R88 | 1k | ABD03K1001FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R93 | 1k | PTFR0603Q1K00N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C92 | 1nF | 0603CG102J101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R92 | 3.24k | TD03G3241BT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | TP5 | ARMED | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D1.5mm | fitted |
| ocp_latch.kicad_sch | U23 | SN74LVC1G11 | SN74LVC1G11DCKR | Package_TO_SOT_SMD:SOT-363_SC-70-6 | fitted |
| ocp_latch.kicad_sch | U22 | SN74LVC1G14 | SN74LVC1G14DBVR | Package_TO_SOT_SMD:SOT-23-5 | fitted |
| ocp_latch.kicad_sch | U21 | SN74LVC1G17 | SN74LVC1G17DBVR | Package_TO_SOT_SMD:SOT-23-5 | fitted |
| ocp_latch.kicad_sch | U20 | SN74LVC1G74 | SN74LVC1G74DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | U26 | SN74LVC3G17 | SN74LVC3G17DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | U24 | TPS3808G33 | TPS3808G33DBVR | Package_TO_SOT_SMD:SOT-23-6 | fitted |
| ocp_latch.kicad_sch | U25 | TPS389001DSER | TPS389001DSER | fpga-servo:Texas_DSE0006A_WSON-6_1.5x1.5mm | fitted |
| power_input.kicad_sch | C19 | 100nF | 0805B104K101NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| power_input.kicad_sch | C4 | 100nF | C4532C0G2A104JT000N | Capacitor_SMD:C_1812_4532Metric | fitted |
| power_input.kicad_sch | C5 | 10nF | 0603B103K101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| power_input.kicad_sch | C3 | 1uF | C212E105J6BC000 | Capacitor_THT:C_Rect_L18.0mm_W8.0mm_P15.00mm_FKS3_FKP3 | fitted |
| power_input.kicad_sch | C18 | 220nF | 0805B224K500NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| power_input.kicad_sch | F1 | 25A_0456025.ER | 0456025.ER | fpga-servo:Littelfuse_456_25A_SMD | fitted |
| power_input.kicad_sch | R1, R2 | 280k | PTFR0805B280KP9 | Resistor_SMD:R_0805_2012Metric | fitted |
| power_input.kicad_sch | R3 | 39k | TC0325B3902T5F | Resistor_SMD:R_0603_1608Metric | fitted |
| power_input.kicad_sch | Q7, Q8 | BSC040N10NS5 | BSC040N10NS5 | Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm | fitted |
| power_input.kicad_sch | J3 | DC_IN_48V | 1714971 | fpga-servo:PhoenixContact_MKDS_5_2_9.52mm | fitted |
| power_input.kicad_sch | U18 | LM74502DDFR | LM74502DDFR | fpga-servo:TI_DDF0008A_SOT23_8_P0.65mm | fitted |
| power_input.kicad_sch | J6 | PSU_EXT | TBD | (none) | external |
| power_input.kicad_sch | D1 | SMCJ54A | (generic geometry / DNP) | Diode_SMD:D_SMC | DNP |
| power_input.kicad_sch | TP2 | TP_GND | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| power_input.kicad_sch | TP1 | TP_VBUS_PROT | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |

## ad7606c

202 components / 172 nets / 714 memberships; 201 board objects; 196 fitted board objects including5 bare-copper testpoints;191 purchased fitted components. DNP: D1, R32, RT1, RT2, RT3. J6 excluded from board.

| Sheet | References | Value | Exact MPN | Footprint | Native assembly |
| --- | --- | --- | --- | --- | --- |
| adc_core.kicad_sch | R105, R106, R107, R108, R109 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| adc_core.kicad_sch | R104 | 47R | RS-03K47R0FT | Resistor_SMD:R_0603_1608Metric | fitted |
| adc_core.kicad_sch | U6 | AD7606C-16BSTZ | AD7606C-16BSTZ | Package_QFP:LQFP-64_10x10mm_P0.5mm | fitted |
| adc_levelshift.kicad_sch | C101, C102, C103, C104, C105, C106 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| adc_levelshift.kicad_sch | R100, R101, R102, R103 | 47R | RS-03K47R0FT | Resistor_SMD:R_0603_1608Metric | fitted |
| adc_levelshift.kicad_sch | U27, U28, U29 | TXU0204PWR | TXU0204PWR | Package_SO:TSSOP-14_4.4x5mm_P0.65mm | fitted |
| adc_power.kicad_sch | C61, C64, C65, C66, C67, C68 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| adc_power.kicad_sch | C60, C100 | 10uF | HGC0805R7106K250NSLJ | Capacitor_SMD:C_0805_2012Metric | fitted |
| adc_power.kicad_sch | C62, C63 | 1uF | 0603B105K250NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | R32 | 100k | (generic geometry / DNP) | Resistor_SMD:R_0603_1608Metric | DNP |
| aux_power.kicad_sch | R20 | 100k | 0603WAF1003T5E | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | R95 | 10k | PTFR0603Q10K0N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C133 | 10nF | 0603B103K101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | L1 | 150uH | 7447709151 | fpga-servo:Wurth_WE_PD_1210_7447709151 | fitted |
| aux_power.kicad_sch | C24 | 2.2nF | 0603B222J500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | C20, C21 | 2.2uF | 1210B225K101NT | Capacitor_SMD:C_1210_3225Metric | fitted |
| aux_power.kicad_sch | L2 | 2.2uH | SWPA4020S2R2MT | fpga-servo:Sunlord_SWPA4020S | fitted |
| aux_power.kicad_sch | R23 | 200k | RC0603FR-07200KL | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C22, C23 | 22uF | 1210B226K250NT | Capacitor_SMD:C_1210_3225Metric | fitted |
| aux_power.kicad_sch | C30, C31, C132 | 22uF | GRM32ER71E226KE15L | fpga-servo:Murata_GRM32_1210 | fitted |
| aux_power.kicad_sch | C25 | 3.3nF | GRM1885C1H332JA01D | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | R21 | 442k | RT0603BRD07442KL | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | R22 | 49.9k | RT0603BRD0749K9L | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | C26 | 56pF | 0603CG560J500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| aux_power.kicad_sch | R94 | 75k | PTFR0603Q75K0N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| aux_power.kicad_sch | U12 | LM5164DDAR | LM5164DDAR | fpga-servo:TI_DDA0008B_LM5164 | fitted |
| aux_power.kicad_sch | U13 | TPS62901RPJR | TPS62901RPJR | fpga-servo:Texas_RPJ0009A_VQFN-HR-9_1.5x2mm | fitted |
| aux_power.kicad_sch | TP3 | TP_12V | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| aux_power.kicad_sch | TP4 | TP_5V | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| ax7010_interface.kicad_sch | R80, R81, R82, R83, R84, R85, R86, R110, R111 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ax7010_interface.kicad_sch | J1 | AX7010_PL_A | 321040SG0ABK00A01 | fpga-servo:JILN_3210_2x20_P2.54mm_D1.02 | fitted |
| current_adc.kicad_sch | C43, C44, C45, C84, C85 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| current_adc.kicad_sch | NTC1, NTC2 | 10k | CMFA 103F3950 | fpga-servo:NTC_0603_Shiheng_KUU | fitted |
| current_adc.kicad_sch | R70, R71 | 10k | TD03G1002BT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | C40, C41, C42 | 1nF | 0603CG102J101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| current_adc.kicad_sch | R53 | 2k | TD03G2001BT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | RSH4 | 2mR | HoYLR2512-3W-2mR-1% | fpga-servo:HoYLR2512_Kelvin | fitted |
| current_adc.kicad_sch | R54 | 4.7k | RS-03K4701FT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | R40, R41, R42 | 47R | RS-03K47R0FT | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | R50 | 8.2k | PTFR0603B8K20P9 | Resistor_SMD:R_0603_1608Metric | fitted |
| current_adc.kicad_sch | U2, U3, U4, U5 | INA240A1DR | INA240A1DR | fpga-servo:TI_D0008A_SOIC8_P1.27mm | fitted |
| current_adc.kicad_sch | U15 | LM393LVDDFR | LM393LVDDFR | fpga-servo:TI_DDF0008A | fitted |
| dc_link.kicad_sch | R120, R121, R122, R123, R124, R125, R126, R127, R128, R129 | 0.33R | WSL2512R3300FEA | fpga-servo:Vishay_WSL2512_0R33 | fitted |
| dc_link.kicad_sch | C1, C2, C120, C121, C122, C123, C124, C125, C126, C127 | 100uF | EKZN101ELL101MJ20S | fpga-servo:NCC_KZN_D10_P5_Courtyard11 | fitted |
| dc_link.kicad_sch | J7 | EXT_SINK | 1714971 | fpga-servo:PhoenixContact_MKDS_5_2_9.52mm | fitted |
| encoder.kicad_sch | F2 | 0.5A_PTC_ENCODER_5V | ASMD1812-050 | Fuse:Fuse_1812_4532Metric | fitted |
| encoder.kicad_sch | C70 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| encoder.kicad_sch | RT1, RT2, RT3 | 120R | (generic geometry / DNP) | Resistor_SMD:R_0603_1608Metric | DNP |
| encoder.kicad_sch | C71 | 4.7uF | CGA0805X7R475K250MT | Capacitor_SMD:C_0805_2012Metric | fitted |
| encoder.kicad_sch | J5 | ABZ_DIFF_ENCODER | 321010SG0ABK00A01 | fpga-servo:JILN_3210_2x05_P2.54mm_D1.02 | fitted |
| encoder.kicad_sch | U7 | AM26LV32EIPWR | AM26LV32EIPWR | Package_SO:TSSOP-16_4.4x5mm_P0.65mm | fitted |
| encoder.kicad_sch | U19 | TPD6E05U06RVZR | TPD6E05U06RVZR | fpga-servo:TI_RVZ0014A_W025 | fitted |
| gate_inverter.kicad_sch | R56, R57, R58, R59, R60, R61 | 100k | RS-03K1003FT | Resistor_SMD:R_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | C46, C80, C81, C82, C83 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | R55, RGS1, RGS2, RGS3, RGS4, RGS5, RGS6 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| gate_inverter.kicad_sch | C69 | 10uF | CGA1206X7R106K250NT | Capacitor_SMD:C_1206_3216Metric | fitted |
| gate_inverter.kicad_sch | RG1, RG2, RG3, RG4, RG5, RG6 | 33R | CRCW060333R0FKEAHP | fpga-servo:Vishay_CRCW0603_HP | fitted |
| gate_inverter.kicad_sch | CBOOT1, CBOOT2, CBOOT3 | 470nF | 0805B474K500NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| gate_inverter.kicad_sch | RSH1, RSH2, RSH3 | 5mR | HoYLR2512-3W-5mR-1% | fpga-servo:HoYLR2512_Kelvin | fitted |
| gate_inverter.kicad_sch | Q1, Q2, Q3, Q4, Q5, Q6 | BSC040N10NS5 | BSC040N10NS5 | Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm | fitted |
| gate_inverter.kicad_sch | U1 | DRV8300DPWR | DRV8300DPWR | Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm | fitted |
| gate_inverter.kicad_sch | J4 | MOTOR_UVW | KF950-9.5-3P | fpga-servo:KEFA_KF950_3_9.50mm_D1.85 | fitted |
| gate_inverter.kicad_sch | U11 | SN74LVC1G11DCKR | SN74LVC1G11DCKR | Package_TO_SOT_SMD:SOT-363_SC-70-6 | fitted |
| gate_inverter.kicad_sch | U8, U9, U10 | SN74LVC2G08DCUR | SN74LVC2G08DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | R89 | 100k | RS-03K1003FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C86, C87, C88, C89, C90, C91, C93 | 100nF | 0603B104K500NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C94 | 100nF | GRT31C5C1H104FA02L | Capacitor_SMD:C_1206_3216Metric | fitted |
| ocp_latch.kicad_sch | R87, R90, R91 | 10k | ABD03K1002FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R88 | 1k | ABD03K1001FT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R93 | 1k | PTFR0603Q1K00N9 | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | C92 | 1nF | 0603CG102J101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | R92 | 3.24k | TD03G3241BT | Resistor_SMD:R_0603_1608Metric | fitted |
| ocp_latch.kicad_sch | TP5 | ARMED | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D1.5mm | fitted |
| ocp_latch.kicad_sch | U23 | SN74LVC1G11 | SN74LVC1G11DCKR | Package_TO_SOT_SMD:SOT-363_SC-70-6 | fitted |
| ocp_latch.kicad_sch | U22 | SN74LVC1G14 | SN74LVC1G14DBVR | Package_TO_SOT_SMD:SOT-23-5 | fitted |
| ocp_latch.kicad_sch | U21 | SN74LVC1G17 | SN74LVC1G17DBVR | Package_TO_SOT_SMD:SOT-23-5 | fitted |
| ocp_latch.kicad_sch | U20 | SN74LVC1G74 | SN74LVC1G74DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | U26 | SN74LVC3G17 | SN74LVC3G17DCUR | fpga-servo:TI_DCU0008A_VSSOP8_P0.5mm | fitted |
| ocp_latch.kicad_sch | U24 | TPS3808G33 | TPS3808G33DBVR | Package_TO_SOT_SMD:SOT-23-6 | fitted |
| ocp_latch.kicad_sch | U25 | TPS389001DSER | TPS389001DSER | fpga-servo:Texas_DSE0006A_WSON-6_1.5x1.5mm | fitted |
| power_input.kicad_sch | C19 | 100nF | 0805B104K101NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| power_input.kicad_sch | C4 | 100nF | C4532C0G2A104JT000N | Capacitor_SMD:C_1812_4532Metric | fitted |
| power_input.kicad_sch | C5 | 10nF | 0603B103K101NT | Capacitor_SMD:C_0603_1608Metric | fitted |
| power_input.kicad_sch | C3 | 1uF | C212E105J6BC000 | Capacitor_THT:C_Rect_L18.0mm_W8.0mm_P15.00mm_FKS3_FKP3 | fitted |
| power_input.kicad_sch | C18 | 220nF | 0805B224K500NT | Capacitor_SMD:C_0805_2012Metric | fitted |
| power_input.kicad_sch | F1 | 25A_0456025.ER | 0456025.ER | fpga-servo:Littelfuse_456_25A_SMD | fitted |
| power_input.kicad_sch | R1, R2 | 280k | PTFR0805B280KP9 | Resistor_SMD:R_0805_2012Metric | fitted |
| power_input.kicad_sch | R3 | 39k | TC0325B3902T5F | Resistor_SMD:R_0603_1608Metric | fitted |
| power_input.kicad_sch | Q7, Q8 | BSC040N10NS5 | BSC040N10NS5 | Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm | fitted |
| power_input.kicad_sch | J3 | DC_IN_48V | 1714971 | fpga-servo:PhoenixContact_MKDS_5_2_9.52mm | fitted |
| power_input.kicad_sch | U18 | LM74502DDFR | LM74502DDFR | fpga-servo:TI_DDF0008A_SOT23_8_P0.65mm | fitted |
| power_input.kicad_sch | J6 | PSU_EXT | TBD | (none) | external |
| power_input.kicad_sch | D1 | SMCJ54A | (generic geometry / DNP) | Diode_SMD:D_SMC | DNP |
| power_input.kicad_sch | TP2 | TP_GND | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
| power_input.kicad_sch | TP1 | TP_VBUS_PROT | (generic geometry / DNP) | TestPoint:TestPoint_Pad_D2.0mm | fitted |
