EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
Sheet 1 1
Title "Rev.A1 - Differential ABZ Encoder"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "RS-422 receiver + selectable termination + interface protection"
$EndDescr
Text HLabel 650 2000 0    50   Input ~ 0
VA_5V
Text HLabel 650 2400 0    50   Input ~ 0
VIO_3V3
Text HLabel 650 2800 1    50   BiDi ~ 0
GND
Text HLabel 14500 2200 2    50   Output ~ 0
ENC_A
Text HLabel 14500 2600 2    50   Output ~ 0
ENC_B
Text HLabel 14500 3000 2    50   Output ~ 0
ENC_Z
$Comp
L ax7010_servo_reva:ENCODER_DIFF J5
U 1 1 6600005B
P 1900 4300
F 0 "J5" H 2000 4400 50  0000 C CNN
F 1 "ABZ_DIFF_ENCODER" H 2000 4200 50  0000 C CNN
F 2 "Connector_Generic:Conn_02x05_Odd_Even" H 1900 4300 50  0001 C CNN
	1    1900 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT1
U 1 1 6600005C
P 3800 3300
F 0 "RT1" H 3900 3400 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3900 3200 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3800 3300 50  0001 C CNN
	1    3800 3300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT2
U 1 1 6600005D
P 3800 4200
F 0 "RT2" H 3900 4300 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3900 4100 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3800 4200 50  0001 C CNN
	1    3800 4200
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT3
U 1 1 6600005E
P 3800 5100
F 0 "RT3" H 3900 5200 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3900 5000 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3800 5100 50  0001 C CNN
	1    3800 5100
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:AM26LV32E U7
U 1 1 6600005F
P 7200 4300
F 0 "U7" H 7300 4400 50  0000 C CNN
F 1 "AM26LV32EIPWR" H 7300 4200 50  0000 C CNN
F 2 "Package_SO:TSSOP-16_4.4x5mm_P0.65mm" H 7200 4300 50  0001 C CNN
	1    7200 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:FUSE F2
U 1 1 66000060
P 3000 2100
F 0 "F2" H 3100 2200 50  0000 C CNN
F 1 "0.5A_PTC_ENCODER_5V" H 3100 2000 50  0000 C CNN
F 2 "Fuse:Fuse_1812_4532Metric" H 3000 2100 50  0001 C CNN
	1    3000 2100
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C70
U 1 1 66000061
P 7200 5900
F 0 "C70" H 7300 6000 50  0000 C CNN
F 1 "100nF_VIO" H 7300 5800 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7200 5900 50  0001 C CNN
	1    7200 5900
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C71
U 1 1 66000062
P 7800 5900
F 0 "C71" H 7900 6000 50  0000 C CNN
F 1 "4.7uF_VIO" H 7900 5800 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 7800 5900 50  0001 C CNN
	1    7800 5900
	1 0 0 -1
$EndComp
Text Notes 650 6900 0    70   ~ 12
A/B/Z are differential RS-422 pairs. 120R termination is fitted only when this board is the cable end.
Text Notes 650 7050 0    70   ~ 12
TPD6E05U06 provides six low-capacitance shunt ESD channels directly at A+/A-/B+/B-/Z+/Z-. Keep it adjacent to J5; exact UQFN footprint remains a fabrication gate.
Text Notes 650 7200 0    70   ~ 12
AM26LV32E is powered from FPGA VIO_3V3 so its outputs cannot over-drive an unpowered AX7010 domain.
$Comp
L ax7010_servo_reva:TPD6E05U06 U19
U 1 1 6ABAF013
P 4800 4300
F 0 "U19" H 4900 4400 50  0000 C CNN
F 1 "TPD6E05U06RVZR" H 4900 4200 50  0000 C CNN
F 2 "" H 4800 4300 50  0001 C CNN
	1    4800 4300
	1 0 0 -1
$EndComp
Text Notes 600 10450 0    55   ~ 12
VISIBLE WIRING: differential ABZ pairs, termination, ESD, line receiver and encoder power are explicitly wired.
Wire Wire Line
	1250 3900 900 3900
Text Label 900 3900 0    45   ~ 0
ENC_A_P
Wire Wire Line
	1250 4060 900 4060
Text Label 900 4060 0    45   ~ 0
ENC_A_N
Wire Wire Line
	1250 4220 900 4220
Text Label 900 4220 0    45   ~ 0
ENC_B_P
Wire Wire Line
	1250 4380 900 4380
Text Label 900 4380 0    45   ~ 0
ENC_B_N
Wire Wire Line
	1250 4540 900 4540
Text Label 900 4540 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	1250 4700 900 4700
Text Label 900 4700 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	2550 4060 2900 4060
Text Label 2900 4060 0    45   ~ 0
ENC_5V
Wire Wire Line
	2550 4220 2900 4220
Text Label 2900 4220 0    45   ~ 0
GND
Wire Wire Line
	2550 4380 2900 4380
Text Label 2900 4380 0    45   ~ 0
SHIELD
NoConn ~ 2550 4540
Wire Wire Line
	2690 2100 2340 2100
Text Label 2340 2100 0    45   ~ 0
VA_5V
Wire Wire Line
	3310 2100 3660 2100
Text Label 3660 2100 0    45   ~ 0
ENC_5V
Wire Wire Line
	3500 3300 3150 3300
Text Label 3150 3300 0    45   ~ 0
ENC_A_P
Wire Wire Line
	4100 3300 4450 3300
Text Label 4450 3300 0    45   ~ 0
ENC_A_N
Wire Wire Line
	3500 4200 3150 4200
Text Label 3150 4200 0    45   ~ 0
ENC_B_P
Wire Wire Line
	4100 4200 4450 4200
Text Label 4450 4200 0    45   ~ 0
ENC_B_N
Wire Wire Line
	3500 5100 3150 5100
Text Label 3150 5100 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	4100 5100 4450 5100
Text Label 4450 5100 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	4100 3800 3750 3800
Text Label 3750 3800 0    45   ~ 0
ENC_A_P
Wire Wire Line
	4100 4000 3750 4000
Text Label 3750 4000 0    45   ~ 0
ENC_A_N
Wire Wire Line
	4100 4200 3750 4200
Text Label 3750 4200 0    45   ~ 0
ENC_B_P
Wire Wire Line
	4100 4400 3750 4400
Text Label 3750 4400 0    45   ~ 0
ENC_B_N
Wire Wire Line
	4100 4600 3750 4600
Text Label 3750 4600 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	4100 4800 3750 4800
Text Label 3750 4800 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	4800 5200 4800 5550
Text Label 4800 5550 0    45   ~ 0
GND
Wire Wire Line
	6300 3740 5950 3740
Text Label 5950 3740 0    45   ~ 0
ENC_A_P
Wire Wire Line
	6300 3900 5950 3900
Text Label 5950 3900 0    45   ~ 0
ENC_A_N
Wire Wire Line
	8100 4060 8450 4060
Text Label 8450 4060 0    45   ~ 0
ENC_A
Wire Wire Line
	6300 4060 5950 4060
Text Label 5950 4060 0    45   ~ 0
ENC_B_P
Wire Wire Line
	6300 4220 5950 4220
Text Label 5950 4220 0    45   ~ 0
ENC_B_N
Wire Wire Line
	8100 4220 8450 4220
Text Label 8450 4220 0    45   ~ 0
ENC_B
Wire Wire Line
	7200 3200 7200 2850
Text Label 7200 2850 0    45   ~ 0
VIO_3V3
Wire Wire Line
	7200 5400 7200 5750
Text Label 7200 5750 0    45   ~ 0
GND
Wire Wire Line
	8100 4380 8450 4380
Text Label 8450 4380 0    45   ~ 0
ENC_Z
Wire Wire Line
	6300 4380 5950 4380
Text Label 5950 4380 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	6300 4540 5950 4540
Text Label 5950 4540 0    45   ~ 0
ENC_Z_N
NoConn ~ 8100 4540
NoConn ~ 6300 4700
NoConn ~ 6300 4860
Wire Wire Line
	7360 3200 7360 2850
Text Label 7360 2850 0    45   ~ 0
GND
Wire Wire Line
	7040 3200 7040 2850
Text Label 7040 2850 0    45   ~ 0
VIO_3V3
Wire Wire Line
	7200 5650 7200 5300
Text Label 7200 5300 0    45   ~ 0
VIO_3V3
Wire Wire Line
	7200 6150 7200 6500
Text Label 7200 6500 0    45   ~ 0
GND
Wire Wire Line
	7800 5650 7800 5300
Text Label 7800 5300 0    45   ~ 0
VIO_3V3
Wire Wire Line
	7800 6150 7800 6500
Text Label 7800 6500 0    45   ~ 0
GND
Wire Wire Line
	650 2000 1100 2000
Text Label 1100 2000 0    45   ~ 0
VA_5V
Wire Wire Line
	650 2400 1100 2400
Text Label 1100 2400 0    45   ~ 0
VIO_3V3
Wire Wire Line
	650 2800 1100 2800
Text Label 1100 2800 0    45   ~ 0
GND
Wire Wire Line
	14500 2200 14050 2200
Text Label 14050 2200 0    45   ~ 0
ENC_A
Wire Wire Line
	14500 2600 14050 2600
Text Label 14050 2600 0    45   ~ 0
ENC_B
Wire Wire Line
	14500 3000 14050 3000
Text Label 14050 3000 0    45   ~ 0
ENC_Z
$EndSCHEMATC
