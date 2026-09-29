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
Text HLabel 650 2000 0    50   I ~ 0
VA_5V
Text HLabel 650 2400 0    50   I ~ 0
VIO_3V3
Text HLabel 650 2800 1    50   B ~ 0
GND
Text HLabel 14500 2200 2    50   O ~ 0
ENC_A
Text HLabel 14500 2600 2    50   O ~ 0
ENC_B
Text HLabel 14500 3000 2    50   O ~ 0
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
Connector-side low-capacitance ESD footprint is mandatory before fabrication; exact part is gated by encoder cable voltage/EMC test.
Text Notes 650 7200 0    70   ~ 12
AM26LV32E is powered from FPGA VIO_3V3 so its outputs cannot over-drive an unpowered AX7010 domain.
$EndSCHEMATC
