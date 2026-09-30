EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "Rev.A1 - AX7010 PL Interface"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "Two 2x20 PL expansion headers; recent AX7010 docs call these J10/J11"
$EndDescr
$Comp
L ax7010_servo_reva:HDR_2x20 J1
U 1 1 66000063
P 2700 3500
F 0 "J1" H 2800 3600 50  0000 C CNN
F 1 "AX7010_PL_A" H 2800 3400 50  0000 C CNN
F 2 "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical" H 2700 3500 50  0001 C CNN
	1    2700 3500
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:HDR_2x20 J2
U 1 1 66000064
P 6000 3500
F 0 "J2" H 6100 3600 50  0000 C CNN
F 1 "AX7010_PL_B" H 6100 3400 50  0000 C CNN
F 2 "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical" H 6000 3500 50  0001 C CNN
	1    6000 3500
	1 0 0 -1
$EndComp
Text Notes 650 650 0    58   ~ 12
AX7010 PL INTERFACE: J1 = SERVO REAL-TIME / SAFETY; J2 = OPTIONAL PARALLEL ADC / AUXILIARY I/O
Text Notes 1500 950 0    46   ~ 12
J1 - REAL-TIME SERVO, SERIAL ADC, ABZ, SAFETY
Text Notes 4850 950 0    46   ~ 12
J2 - OPTIONAL PARALLEL ADC / HALL / BRAKE / SPARES
Text Notes 650 6900 0    42   ~ 12
AX7010 +5V header pins are NoConn; do not tie carrier +5V to VA_5V.
Text Notes 650 7040 0    42   ~ 12
J1 carries core servo I/O; J2 is optional expansion.
Text Notes 650 7180 0    42   ~ 12
Check J1 pin allocation against the XDC and docs/ax7010_interface.md.
Wire Wire Line
	1800 2100 1650 2100
Text Label 1650 2100 0    40   ~ 0
GND
NoConn ~ 3600 2100
Wire Wire Line
	1800 2250 1000 2250
Text HLabel 1000 2250 0 50 Output ~ 0
PWM_UH
Wire Wire Line
	3600 2250 4400 2250
Text HLabel 4400 2250 2 50 Output ~ 0
PWM_UL
Wire Wire Line
	1800 2400 1000 2400
Text HLabel 1000 2400 0 50 Output ~ 0
PWM_VH
Wire Wire Line
	3600 2400 4400 2400
Text HLabel 4400 2400 2 50 Output ~ 0
PWM_VL
Wire Wire Line
	1800 2550 1000 2550
Text HLabel 1000 2550 0 50 Output ~ 0
PWM_WH
Wire Wire Line
	3600 2550 4400 2550
Text HLabel 4400 2550 2 50 Output ~ 0
PWM_WL
Wire Wire Line
	1800 2700 1000 2700
Text HLabel 1000 2700 0 50 Output ~ 0
GATE_EN
Wire Wire Line
	3600 2700 4400 2700
Text HLabel 4400 2700 2 50 Output ~ 0
FAULT_CLEAR
Wire Wire Line
	1800 2850 1000 2850
Text HLabel 1000 2850 0 50 Output ~ 0
ADC_CONVST
Wire Wire Line
	3600 2850 4400 2850
Text HLabel 4400 2850 2 50 Output ~ 0
ADC_SCLK
Wire Wire Line
	1800 3000 1000 3000
Text HLabel 1000 3000 0 50 Output ~ 0
ADC_CS_N
Wire Wire Line
	3600 3000 4400 3000
Text HLabel 4400 3000 2 50 Output ~ 0
ADC_RESET
Wire Wire Line
	1800 3150 1000 3150
Text HLabel 1000 3150 0 50 Input ~ 0
ADC_DOUTA
Wire Wire Line
	3600 3150 4400 3150
Text HLabel 4400 3150 2 50 Input ~ 0
ADC_DOUTB
Wire Wire Line
	1800 3300 1000 3300
Text HLabel 1000 3300 0 50 Input ~ 0
ADC_BUSY
Wire Wire Line
	3600 3300 4400 3300
Text HLabel 4400 3300 2 50 Input ~ 0
ADC_FRSTDATA
Wire Wire Line
	1800 3450 1000 3450
Text HLabel 1000 3450 0 50 Input ~ 0
ENC_A
Wire Wire Line
	3600 3450 4400 3450
Text HLabel 4400 3450 2 50 Input ~ 0
ENC_B
Wire Wire Line
	1800 3550 1000 3550
Text HLabel 1000 3550 0 50 Input ~ 0
ENC_Z
NoConn ~ 3600 3550
Wire Wire Line
	1800 3700 1000 3700
Text HLabel 1000 3700 0 50 Input ~ 0
OCP_N
Wire Wire Line
	3600 3700 4400 3700
Text HLabel 4400 3700 2 50 Input ~ 0
PWR_GOOD
NoConn ~ 1800 3850
NoConn ~ 3600 3850
NoConn ~ 1800 4000
NoConn ~ 3600 4000
NoConn ~ 1800 4150
NoConn ~ 3600 4150
NoConn ~ 1800 4300
NoConn ~ 3600 4300
NoConn ~ 1800 4450
NoConn ~ 3600 4450
NoConn ~ 1800 4600
NoConn ~ 3600 4600
Wire Wire Line
	1800 4750 1650 4750
Text Label 1650 4750 0    40   ~ 0
GND
Wire Wire Line
	3600 4750 4400 4750
Text HLabel 4400 4750 2 50 BiDi ~ 0
GND
Wire Wire Line
	1800 4900 1000 4900
Text HLabel 1000 4900 0 50 Output ~ 0
VIO_3V3
Wire Wire Line
	3600 4900 3750 4900
Text Label 3750 4900 0    40   ~ 0
VIO_3V3
Wire Wire Line
	5100 2100 4950 2100
Text Label 4950 2100 0    40   ~ 0
GND
NoConn ~ 6900 2100
NoConn ~ 5100 2250
NoConn ~ 6900 2250
NoConn ~ 5100 2400
NoConn ~ 6900 2400
NoConn ~ 5100 2550
NoConn ~ 6900 2550
NoConn ~ 5100 2700
NoConn ~ 6900 2700
NoConn ~ 5100 2850
NoConn ~ 6900 2850
NoConn ~ 5100 3000
NoConn ~ 6900 3000
NoConn ~ 5100 3150
NoConn ~ 6900 3150
NoConn ~ 5100 3300
NoConn ~ 6900 3300
NoConn ~ 5100 3450
NoConn ~ 6900 3450
NoConn ~ 5100 3550
NoConn ~ 6900 3550
NoConn ~ 5100 3700
NoConn ~ 6900 3700
NoConn ~ 5100 3850
NoConn ~ 6900 3850
NoConn ~ 5100 4000
NoConn ~ 6900 4000
NoConn ~ 5100 4150
NoConn ~ 6900 4150
NoConn ~ 5100 4300
NoConn ~ 6900 4300
NoConn ~ 5100 4450
NoConn ~ 6900 4450
NoConn ~ 5100 4600
NoConn ~ 6900 4600
Wire Wire Line
	5100 4750 4950 4750
Text Label 4950 4750 0    40   ~ 0
GND
Wire Wire Line
	6900 4750 7050 4750
Text Label 7050 4750 0    40   ~ 0
GND
Wire Wire Line
	5100 4900 4950 4900
Text Label 4950 4900 0    40   ~ 0
VIO_3V3
Wire Wire Line
	6900 4900 7050 4900
Text Label 7050 4900 0    40   ~ 0
VIO_3V3
$Comp
L ax7010_servo_reva:PWR_FLAG #FLG0106
U 1 1 6AC00006
P 3750 4900
F 0 "#FLG0106" H 3750 4975 40  0001 C CNN
F 1 "PWR_FLAG" H 3750 5075 40  0000 C CNN
	1    3750 4900
	1 0 0 -1
$EndComp
$EndSCHEMATC
