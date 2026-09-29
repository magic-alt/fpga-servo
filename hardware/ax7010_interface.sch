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
Text Notes 650 450 0    58   ~ 12
AX7010 PL INTERFACE: J1 = SERVO REAL-TIME / SAFETY; J2 = OPTIONAL PARALLEL ADC / AUXILIARY I/O
Text Notes 1500 950 0    46   ~ 12
J1 - REAL-TIME SERVO, SERIAL ADC, ABZ, SAFETY
Text Notes 4850 950 0    46   ~ 12
J2 - OPTIONAL PARALLEL ADC / HALL / BRAKE / SPARES
Text Notes 650 6900 0    42   ~ 12
AX7010 +5V header pins remain deliberately NoConn. Board logic uses only the FPGA VIO_3V3 domain; do not parallel the carrier +5V with local VA_5V.
Text Notes 650 7040 0    42   ~ 12
J1 carries the release-critical servo path. J2 is optional expansion and must not become a hidden dependency for basic PWM/current/encoder operation.
Text Notes 650 7180 0    42   ~ 12
Release-critical J1 hierarchy ports are wired directly beside J1; local net labels are reserved for duplicate rails and optional J2-only signals. Pin allocation remains cross-checked against fpga/ax7010_servo_reva.xdc and docs/ax7010_interface.md.
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
Wire Wire Line
	3600 3550 3750 3550
Text Label 3750 3550 0    40   ~ 0
ENC_FAULT_N
Wire Wire Line
	1800 3700 1000 3700
Text HLabel 1000 3700 0 50 Input ~ 0
OCP_N
Wire Wire Line
	3600 3700 4400 3700
Text HLabel 4400 3700 2 50 Input ~ 0
PWR_GOOD
Wire Wire Line
	1800 3850 1650 3850
Text Label 1650 3850 0    40   ~ 0
AUX_IN0
Wire Wire Line
	3600 3850 3750 3850
Text Label 3750 3850 0    40   ~ 0
AUX_IN1
Wire Wire Line
	1800 4000 1650 4000
Text Label 1650 4000 0    40   ~ 0
AUX_OUT0
Wire Wire Line
	3600 4000 3750 4000
Text Label 3750 4000 0    40   ~ 0
AUX_OUT1
Wire Wire Line
	1800 4150 1650 4150
Text Label 1650 4150 0    40   ~ 0
SPARE_A0
Wire Wire Line
	3600 4150 3750 4150
Text Label 3750 4150 0    40   ~ 0
SPARE_A1
Wire Wire Line
	1800 4300 1650 4300
Text Label 1650 4300 0    40   ~ 0
SPARE_A2
Wire Wire Line
	3600 4300 3750 4300
Text Label 3750 4300 0    40   ~ 0
SPARE_A3
Wire Wire Line
	1800 4450 1650 4450
Text Label 1650 4450 0    40   ~ 0
SPARE_A4
Wire Wire Line
	3600 4450 3750 4450
Text Label 3750 4450 0    40   ~ 0
SPARE_A5
Wire Wire Line
	1800 4600 1650 4600
Text Label 1650 4600 0    40   ~ 0
SPARE_A6
Wire Wire Line
	3600 4600 3750 4600
Text Label 3750 4600 0    40   ~ 0
SPARE_A7
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
Wire Wire Line
	5100 2250 4950 2250
Text Label 4950 2250 0    40   ~ 0
ADC_DB0
Wire Wire Line
	6900 2250 7050 2250
Text Label 7050 2250 0    40   ~ 0
ADC_DB1
Wire Wire Line
	5100 2400 4950 2400
Text Label 4950 2400 0    40   ~ 0
ADC_DB2
Wire Wire Line
	6900 2400 7050 2400
Text Label 7050 2400 0    40   ~ 0
ADC_DB3
Wire Wire Line
	5100 2550 4950 2550
Text Label 4950 2550 0    40   ~ 0
ADC_DB4
Wire Wire Line
	6900 2550 7050 2550
Text Label 7050 2550 0    40   ~ 0
ADC_DB5
Wire Wire Line
	5100 2700 4950 2700
Text Label 4950 2700 0    40   ~ 0
ADC_DB6
Wire Wire Line
	6900 2700 7050 2700
Text Label 7050 2700 0    40   ~ 0
ADC_DB7
Wire Wire Line
	5100 2850 4950 2850
Text Label 4950 2850 0    40   ~ 0
ADC_DB8
Wire Wire Line
	6900 2850 7050 2850
Text Label 7050 2850 0    40   ~ 0
ADC_DB9
Wire Wire Line
	5100 3000 4950 3000
Text Label 4950 3000 0    40   ~ 0
ADC_DB10
Wire Wire Line
	6900 3000 7050 3000
Text Label 7050 3000 0    40   ~ 0
ADC_DB11
Wire Wire Line
	5100 3150 4950 3150
Text Label 4950 3150 0    40   ~ 0
ADC_DB12
Wire Wire Line
	6900 3150 7050 3150
Text Label 7050 3150 0    40   ~ 0
ADC_DB13
Wire Wire Line
	5100 3300 4950 3300
Text Label 4950 3300 0    40   ~ 0
ADC_DB14
Wire Wire Line
	6900 3300 7050 3300
Text Label 7050 3300 0    40   ~ 0
ADC_DB15
Wire Wire Line
	5100 3450 4950 3450
Text Label 4950 3450 0    40   ~ 0
ADC_RD_N
Wire Wire Line
	6900 3450 7050 3450
Text Label 7050 3450 0    40   ~ 0
ADC_BYTE_SEL
Wire Wire Line
	5100 3550 4950 3550
Text Label 4950 3550 0    40   ~ 0
ADC_RANGE
Wire Wire Line
	6900 3550 7050 3550
Text Label 7050 3550 0    40   ~ 0
ADC_OS0
Wire Wire Line
	5100 3700 4950 3700
Text Label 4950 3700 0    40   ~ 0
ADC_OS1
Wire Wire Line
	6900 3700 7050 3700
Text Label 7050 3700 0    40   ~ 0
ADC_OS2
Wire Wire Line
	5100 3850 4950 3850
Text Label 4950 3850 0    40   ~ 0
ADC_STBY
Wire Wire Line
	6900 3850 7050 3850
Text Label 7050 3850 0    40   ~ 0
ADC_PAR_SER
Wire Wire Line
	5100 4000 4950 4000
Text Label 4950 4000 0    40   ~ 0
HALL_U
Wire Wire Line
	6900 4000 7050 4000
Text Label 7050 4000 0    40   ~ 0
HALL_V
Wire Wire Line
	5100 4150 4950 4150
Text Label 4950 4150 0    40   ~ 0
HALL_W
Wire Wire Line
	6900 4150 7050 4150
Text Label 7050 4150 0    40   ~ 0
BRAKE_OUT
Wire Wire Line
	5100 4300 4950 4300
Text Label 4950 4300 0    40   ~ 0
EXT_FAULT_N
Wire Wire Line
	6900 4300 7050 4300
Text Label 7050 4300 0    40   ~ 0
TEST_TRIG
Wire Wire Line
	5100 4450 4950 4450
Text Label 4950 4450 0    40   ~ 0
SPARE_B0
Wire Wire Line
	6900 4450 7050 4450
Text Label 7050 4450 0    40   ~ 0
SPARE_B1
Wire Wire Line
	5100 4600 4950 4600
Text Label 4950 4600 0    40   ~ 0
SPARE_B2
Wire Wire Line
	6900 4600 7050 4600
Text Label 7050 4600 0    40   ~ 0
SPARE_B3
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
$EndSCHEMATC
