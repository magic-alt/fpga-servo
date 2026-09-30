EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "Rev.A1 - Differential ABZ Encoder"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "RS-422 receiver + selectable termination + interface protection"
$EndDescr
Text HLabel 700 1600 0 50 Input ~ 0
VA_5V
Text HLabel 700 2000 0 50 Input ~ 0
VIO_3V3
Text HLabel 700 2400 0 50 BiDi ~ 0
GND
Text HLabel 9000 3250 2 50 Output ~ 0
ENC_A
Text HLabel 9000 3400 2 50 Output ~ 0
ENC_B
Text HLabel 9000 3600 2 50 Output ~ 0
ENC_Z
$Comp
L ax7010_servo_reva:ENCODER_DIFF J5
U 1 1 6600005B
P 1500 3500
AR Path="/69000006/6600005B" Ref="J5"  Part="1"
F 0 "J5" H 1600 3600 50  0000 C CNN
F 1 "ABZ_DIFF_ENCODER" H 1600 3400 50  0000 C CNN
F 2 "Connector_Generic:Conn_02x05_Odd_Even" H 1500 3500 50  0001 C CNN
	1    1500 3500
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT1
U 1 1 6600005C
P 3300 2700
AR Path="/69000006/6600005C" Ref="RT1"  Part="1"
F 0 "RT1" H 3400 2800 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3400 2600 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3300 2700 50  0001 C CNN
	1    3300 2700
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT2
U 1 1 6600005D
P 3300 3500
AR Path="/69000006/6600005D" Ref="RT2"  Part="1"
F 0 "RT2" H 3400 3600 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3400 3400 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3300 3500 50  0001 C CNN
	1    3300 3500
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R RT3
U 1 1 6600005E
P 3300 4300
AR Path="/69000006/6600005E" Ref="RT3"  Part="1"
F 0 "RT3" H 3400 4400 50  0000 C CNN
F 1 "120R_TERM_DNP" H 3400 4200 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 3300 4300 50  0001 C CNN
	1    3300 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:AM26LV32E U7
U 1 1 6600005F
P 6900 3500
AR Path="/69000006/6600005F" Ref="U7"  Part="1"
F 0 "U7" H 7000 3600 50  0000 C CNN
F 1 "AM26LV32EIPWR" H 7000 3400 50  0000 C CNN
F 2 "Package_SO:TSSOP-16_4.4x5mm_P0.65mm" H 6900 3500 50  0001 C CNN
	1    6900 3500
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:FUSE F2
U 1 1 66000060
P 2100 1600
AR Path="/69000006/66000060" Ref="F2"  Part="1"
F 0 "F2" H 2200 1700 50  0000 C CNN
F 1 "0.5A_PTC_ENCODER_5V" H 2200 1500 50  0000 C CNN
F 2 "Fuse:Fuse_1812_4532Metric" H 2100 1600 50  0001 C CNN
	1    2100 1600
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C70
U 1 1 66000061
P 6900 5200
AR Path="/69000006/66000061" Ref="C70"  Part="1"
F 0 "C70" H 7000 5300 50  0000 C CNN
F 1 "100nF_VIO" H 7000 5100 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 6900 5200 50  0001 C CNN
	1    6900 5200
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C71
U 1 1 66000062
P 7550 5200
AR Path="/69000006/66000062" Ref="C71"  Part="1"
F 0 "C71" H 7650 5300 50  0000 C CNN
F 1 "4.7uF_VIO" H 7650 5100 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 7550 5200 50  0001 C CNN
	1    7550 5200
	1 0 0 -1
$EndComp
Text Notes 650 6500 0    50   ~ 12
A/B/Z are differential RS-422 pairs. 120R termination is fitted only when this board is the cable end.
Text Notes 650 6660 0    50   ~ 12
TPD6E05U06 provides six low-capacitance shunt ESD channels directly at A+/A-/B+/B-/Z+/Z-. Keep it adjacent to J5; exact UQFN footprint remains a fabrication gate.
Text Notes 650 6820 0    50   ~ 12
AM26LV32E is powered from FPGA VIO_3V3 so its outputs cannot over-drive an unpowered AX7010 domain.
$Comp
L ax7010_servo_reva:TPD6E05U06 U19
U 1 1 6ABAF013
P 4700 3500
AR Path="/69000006/6ABAF013" Ref="U19"  Part="1"
F 0 "U19" H 4800 3600 50  0000 C CNN
F 1 "TPD6E05U06RVZR" H 4800 3400 50  0000 C CNN
F 2 "" H 4700 3500 50  0001 C CNN
	1    4700 3500
	1 0 0 -1
$EndComp
Text Notes 650 6980 0    50   ~ 12
VISIBLE WIRING: differential ABZ pairs, termination, ESD, line receiver and encoder power are explicitly wired; receiver outputs go directly to hierarchy ports.
Wire Wire Line
	850 3100 700 3100
Text Label 700 3100 0    40   ~ 0
ENC_A_P
Wire Wire Line
	850 3250 700 3250
Text Label 700 3250 0    40   ~ 0
ENC_A_N
Wire Wire Line
	850 3400 700 3400
Text Label 700 3400 0    40   ~ 0
ENC_B_P
Wire Wire Line
	850 3600 700 3600
Text Label 700 3600 0    40   ~ 0
ENC_B_N
Wire Wire Line
	850 3750 700 3750
Text Label 700 3750 0    40   ~ 0
ENC_Z_P
Wire Wire Line
	850 3900 700 3900
Text Label 700 3900 0    40   ~ 0
ENC_Z_N
Wire Wire Line
	2150 3250 2300 3250
Text Label 2300 3250 0    40   ~ 0
ENC_5V
Wire Wire Line
	2150 3400 2300 3400
Text Label 2300 3400 0    40   ~ 0
GND
Wire Wire Line
	2150 3600 2300 3600
Text Label 2300 3600 0    40   ~ 0
SHIELD
NoConn ~ 2150 3750
Wire Wire Line
	3000 2700 2850 2700
Text Label 2850 2700 0    40   ~ 0
ENC_A_P
Wire Wire Line
	3600 2700 3750 2700
Text Label 3750 2700 0    40   ~ 0
ENC_A_N
Wire Wire Line
	3000 3500 2850 3500
Text Label 2850 3500 0    40   ~ 0
ENC_B_P
Wire Wire Line
	3600 3500 3750 3500
Text Label 3750 3500 0    40   ~ 0
ENC_B_N
Wire Wire Line
	3000 4300 2850 4300
Text Label 2850 4300 0    40   ~ 0
ENC_Z_P
Wire Wire Line
	3600 4300 3750 4300
Text Label 3750 4300 0    40   ~ 0
ENC_Z_N
Wire Wire Line
	6000 2950 5850 2950
Text Label 5850 2950 0    40   ~ 0
ENC_A_P
Wire Wire Line
	6000 3100 5850 3100
Text Label 5850 3100 0    40   ~ 0
ENC_A_N
Wire Wire Line
	7800 3250 9000 3250
Wire Wire Line
	6000 3250 5850 3250
Text Label 5850 3250 0    40   ~ 0
ENC_B_P
Wire Wire Line
	6000 3400 5850 3400
Text Label 5850 3400 0    40   ~ 0
ENC_B_N
Wire Wire Line
	7800 3400 9000 3400
Wire Wire Line
	6900 2400 6900 2250
Text Label 6900 2250 0    40   ~ 0
VIO_3V3
Wire Wire Line
	6900 4600 6900 4750
Text Label 6900 4750 0    40   ~ 0
GND
Wire Wire Line
	7800 3600 9000 3600
Wire Wire Line
	6000 3600 5850 3600
Text Label 5850 3600 0    40   ~ 0
ENC_Z_P
Wire Wire Line
	6000 3750 5850 3750
Text Label 5850 3750 0    40   ~ 0
ENC_Z_N
NoConn ~ 7800 3750
NoConn ~ 6000 3900
NoConn ~ 6000 4050
Wire Wire Line
	7050 2400 7050 2250
Text Label 7050 2250 0    40   ~ 0
GND
Wire Wire Line
	6750 2400 6750 2250
Text Label 6750 2250 0    40   ~ 0
VIO_3V3
Wire Wire Line
	1800 1600 1650 1600
Text Label 1650 1600 0    40   ~ 0
VA_5V
Wire Wire Line
	2400 1600 2550 1600
Text Label 2550 1600 0    40   ~ 0
ENC_5V
Wire Wire Line
	6900 4950 6900 4800
Text Label 6900 4800 0    40   ~ 0
VIO_3V3
Wire Wire Line
	6900 5450 6900 5600
Text Label 6900 5600 0    40   ~ 0
GND
Wire Wire Line
	7550 4950 7550 4800
Text Label 7550 4800 0    40   ~ 0
VIO_3V3
Wire Wire Line
	7550 5450 7550 5600
Text Label 7550 5600 0    40   ~ 0
GND
Wire Wire Line
	4000 3000 3850 3000
Text Label 3850 3000 0    40   ~ 0
ENC_A_P
Wire Wire Line
	4000 3200 3850 3200
Text Label 3850 3200 0    40   ~ 0
ENC_A_N
Wire Wire Line
	4000 3400 3850 3400
Text Label 3850 3400 0    40   ~ 0
ENC_B_P
Wire Wire Line
	4000 3600 3850 3600
Text Label 3850 3600 0    40   ~ 0
ENC_B_N
Wire Wire Line
	4000 3800 3850 3800
Text Label 3850 3800 0    40   ~ 0
ENC_Z_P
Wire Wire Line
	4000 4000 3850 4000
Text Label 3850 4000 0    40   ~ 0
ENC_Z_N
Wire Wire Line
	4700 4400 4700 4550
Text Label 4700 4550 0    40   ~ 0
GND
Wire Wire Line
	700 1600 900 1600
Wire Wire Line
	700 2000 900 2000
Wire Wire Line
	700 2400 900 2400
$EndSCHEMATC
