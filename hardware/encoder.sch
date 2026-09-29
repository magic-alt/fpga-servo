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
Text HLabel 10800 3100 2 50 Output ~ 0
ENC_A
Text HLabel 10800 3500 2 50 Output ~ 0
ENC_B
Text HLabel 10800 3900 2 50 Output ~ 0
ENC_Z
$Comp
L ax7010_servo_reva:ENCODER_DIFF J5
U 1 1 6600005B
P 1500 3500
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
F 0 "U19" H 4800 3600 50  0000 C CNN
F 1 "TPD6E05U06RVZR" H 4800 3400 50  0000 C CNN
F 2 "" H 4700 3500 50  0001 C CNN
	1    4700 3500
	1 0 0 -1
$EndComp
Text Notes 650 6980 0    50   ~ 12
VISIBLE WIRING: differential ABZ pairs, termination, ESD, line receiver and encoder power are explicitly wired.
Wire Wire Line
	850 3100 630 3100
Text Label 630 3100 0    45   ~ 0
ENC_A_P
Wire Wire Line
	850 3260 630 3260
Text Label 630 3260 0    45   ~ 0
ENC_A_N
Wire Wire Line
	850 3420 630 3420
Text Label 630 3420 0    45   ~ 0
ENC_B_P
Wire Wire Line
	850 3580 630 3580
Text Label 630 3580 0    45   ~ 0
ENC_B_N
Wire Wire Line
	850 3740 630 3740
Text Label 630 3740 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	850 3900 630 3900
Text Label 630 3900 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	2150 3260 2370 3260
Text Label 2370 3260 0    45   ~ 0
ENC_5V
Wire Wire Line
	2150 3420 2370 3420
Text Label 2370 3420 0    45   ~ 0
GND
Wire Wire Line
	2150 3580 2370 3580
Text Label 2370 3580 0    45   ~ 0
SHIELD
NoConn ~ 2150 3740
Wire Wire Line
	3000 2700 2780 2700
Text Label 2780 2700 0    45   ~ 0
ENC_A_P
Wire Wire Line
	3600 2700 3820 2700
Text Label 3820 2700 0    45   ~ 0
ENC_A_N
Wire Wire Line
	3000 3500 2780 3500
Text Label 2780 3500 0    45   ~ 0
ENC_B_P
Wire Wire Line
	3600 3500 3820 3500
Text Label 3820 3500 0    45   ~ 0
ENC_B_N
Wire Wire Line
	3000 4300 2780 4300
Text Label 2780 4300 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	3600 4300 3820 4300
Text Label 3820 4300 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	6000 2940 5780 2940
Text Label 5780 2940 0    45   ~ 0
ENC_A_P
Wire Wire Line
	6000 3100 5780 3100
Text Label 5780 3100 0    45   ~ 0
ENC_A_N
Wire Wire Line
	7800 3260 8020 3260
Text Label 8020 3260 0    45   ~ 0
ENC_A
Wire Wire Line
	6000 3260 5780 3260
Text Label 5780 3260 0    45   ~ 0
ENC_B_P
Wire Wire Line
	6000 3420 5780 3420
Text Label 5780 3420 0    45   ~ 0
ENC_B_N
Wire Wire Line
	7800 3420 8020 3420
Text Label 8020 3420 0    45   ~ 0
ENC_B
Wire Wire Line
	6900 2400 6900 2180
Text Label 6900 2180 0    45   ~ 0
VIO_3V3
Wire Wire Line
	6900 4600 6900 4820
Text Label 6900 4820 0    45   ~ 0
GND
Wire Wire Line
	7800 3580 8020 3580
Text Label 8020 3580 0    45   ~ 0
ENC_Z
Wire Wire Line
	6000 3580 5780 3580
Text Label 5780 3580 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	6000 3740 5780 3740
Text Label 5780 3740 0    45   ~ 0
ENC_Z_N
NoConn ~ 7800 3740
NoConn ~ 6000 3900
NoConn ~ 6000 4060
Wire Wire Line
	7060 2400 7060 2180
Text Label 7060 2180 0    45   ~ 0
GND
Wire Wire Line
	6740 2400 6740 2180
Text Label 6740 2180 0    45   ~ 0
VIO_3V3
Wire Wire Line
	1790 1600 1570 1600
Text Label 1570 1600 0    45   ~ 0
VA_5V
Wire Wire Line
	2410 1600 2630 1600
Text Label 2630 1600 0    45   ~ 0
ENC_5V
Wire Wire Line
	6900 4950 6900 4730
Text Label 6900 4730 0    45   ~ 0
VIO_3V3
Wire Wire Line
	6900 5450 6900 5670
Text Label 6900 5670 0    45   ~ 0
GND
Wire Wire Line
	7550 4950 7550 4730
Text Label 7550 4730 0    45   ~ 0
VIO_3V3
Wire Wire Line
	7550 5450 7550 5670
Text Label 7550 5670 0    45   ~ 0
GND
Wire Wire Line
	4000 3000 3780 3000
Text Label 3780 3000 0    45   ~ 0
ENC_A_P
Wire Wire Line
	4000 3200 3780 3200
Text Label 3780 3200 0    45   ~ 0
ENC_A_N
Wire Wire Line
	4000 3400 3780 3400
Text Label 3780 3400 0    45   ~ 0
ENC_B_N
Wire Wire Line
	4000 3600 3780 3600
Text Label 3780 3600 0    45   ~ 0
ENC_B_N
Wire Wire Line
	4000 3800 3780 3800
Text Label 3780 3800 0    45   ~ 0
ENC_Z_P
Wire Wire Line
	4000 4000 3780 4000
Text Label 3780 4000 0    45   ~ 0
ENC_Z_N
Wire Wire Line
	4700 4400 4700 4620
Text Label 4700 4620 0    45   ~ 0
GND
Wire Wire Line
	700 1600 960 1600
Text Label 960 1600 0    45   ~ 0
VA_5V
Wire Wire Line
	700 2000 960 2000
Text Label 960 2000 0    45   ~ 0
VIO_3V3
Wire Wire Line
	700 2400 960 2400
Text Label 960 2400 0    45   ~ 0
GND
Wire Wire Line
	10800 3100 10540 3100
Text Label 10540 3100 0    45   ~ 0
ENC_A
Wire Wire Line
	10800 3500 10540 3500
Text Label 10540 3500 0    45   ~ 0
ENC_B
Wire Wire Line
	10800 3900 10540 3900
Text Label 10540 3900 0    45   ~ 0
ENC_Z
$EndSCHEMATC
