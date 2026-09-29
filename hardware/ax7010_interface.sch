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
Text HLabel 10600 900 2 50 Output ~ 0
VIO_3V3
Text HLabel 10600 1350 2 50 Output ~ 0
PWM_UH
Text HLabel 10600 1550 2 50 Output ~ 0
PWM_UL
Text HLabel 10600 1750 2 50 Output ~ 0
PWM_VH
Text HLabel 10600 1950 2 50 Output ~ 0
PWM_VL
Text HLabel 10600 2150 2 50 Output ~ 0
PWM_WH
Text HLabel 10600 2350 2 50 Output ~ 0
PWM_WL
Text HLabel 10600 2600 2 50 Output ~ 0
GATE_EN
Text HLabel 10600 2800 2 50 Output ~ 0
FAULT_CLEAR
Text HLabel 10600 3250 2 50 Output ~ 0
ADC_CONVST
Text HLabel 10600 3450 2 50 Output ~ 0
ADC_SCLK
Text HLabel 10600 3650 2 50 Output ~ 0
ADC_CS_N
Text HLabel 10600 3850 2 50 Output ~ 0
ADC_RESET
Text HLabel 10600 4300 0 50 Input ~ 0
ADC_DOUTA
Text HLabel 10600 4500 0 50 Input ~ 0
ADC_DOUTB
Text HLabel 10600 4700 0 50 Input ~ 0
ADC_BUSY
Text HLabel 10600 4900 0 50 Input ~ 0
ADC_FRSTDATA
Text HLabel 10600 5350 0 50 Input ~ 0
ENC_A
Text HLabel 10600 5550 0 50 Input ~ 0
ENC_B
Text HLabel 10600 5750 0 50 Input ~ 0
ENC_Z
Text HLabel 10600 6100 0 50 Input ~ 0
OCP_N
Text HLabel 10600 6300 0 50 Input ~ 0
PWR_GOOD
Text HLabel 10600 6600 1 50 BiDi ~ 0
GND
Text Notes 650 450 0    58   ~ 12
AX7010 PL INTERFACE: J1 = SERVO REAL-TIME / SAFETY; J2 = OPTIONAL PARALLEL ADC / AUXILIARY I/O
Text Notes 1500 950 0    46   ~ 12
J1 - REAL-TIME SERVO, SERIAL ADC, ABZ, SAFETY
Text Notes 4850 950 0    46   ~ 12
J2 - OPTIONAL PARALLEL ADC / HALL / BRAKE / SPARES
Text Notes 9000 1100 0    44   ~ 12
PWM / ENABLE
Text Notes 9000 3000 0    44   ~ 12
ADC CONTROL
Text Notes 9000 4100 0    44   ~ 12
ADC FEEDBACK
Text Notes 9000 5150 0    44   ~ 12
ENCODER FEEDBACK
Text Notes 9000 5950 0    44   ~ 12
SAFETY / STATUS
Text Notes 650 6900 0    42   ~ 12
AX7010 +5V header pins remain deliberately NoConn. Board logic uses only the FPGA VIO_3V3 domain; do not parallel the carrier +5V with local VA_5V.
Text Notes 650 7040 0    42   ~ 12
J1 carries the release-critical servo path. J2 is optional expansion and must not become a hidden dependency for basic PWM/current/encoder operation.
Text Notes 650 7180 0    42   ~ 12
Pin allocation remains cross-checked against fpga/ax7010_servo_reva.xdc and docs/ax7010_interface.md.
Wire Wire Line
	10600 900 10400 900
Wire Wire Line
	10600 1350 10400 1350
Wire Wire Line
	10600 1550 10400 1550
Wire Wire Line
	10600 1750 10400 1750
Wire Wire Line
	10600 1950 10400 1950
Wire Wire Line
	10600 2150 10400 2150
Wire Wire Line
	10600 2350 10400 2350
Wire Wire Line
	10600 2600 10400 2600
Wire Wire Line
	10600 2800 10400 2800
Wire Wire Line
	10600 3250 10400 3250
Wire Wire Line
	10600 3450 10400 3450
Wire Wire Line
	10600 3650 10400 3650
Wire Wire Line
	10600 3850 10400 3850
Wire Wire Line
	10600 4300 10800 4300
Wire Wire Line
	10600 4500 10800 4500
Wire Wire Line
	10600 4700 10800 4700
Wire Wire Line
	10600 4900 10800 4900
Wire Wire Line
	10600 5350 10800 5350
Wire Wire Line
	10600 5550 10800 5550
Wire Wire Line
	10600 5750 10800 5750
Wire Wire Line
	10600 6100 10800 6100
Wire Wire Line
	10600 6300 10800 6300
Wire Wire Line
	10600 6600 10600 6800
Wire Wire Line
	1800 2100 1650 2100
Text Label 1650 2100 0    40   ~ 0
GND
NoConn ~ 3600 2100
Wire Wire Line
	1800 2250 1650 2250
Text Label 1650 2250 0    40   ~ 0
PWM_UH
Wire Wire Line
	3600 2250 3750 2250
Text Label 3750 2250 0    40   ~ 0
PWM_UL
Wire Wire Line
	1800 2400 1650 2400
Text Label 1650 2400 0    40   ~ 0
PWM_VH
Wire Wire Line
	3600 2400 3750 2400
Text Label 3750 2400 0    40   ~ 0
PWM_VL
Wire Wire Line
	1800 2550 1650 2550
Text Label 1650 2550 0    40   ~ 0
PWM_WH
Wire Wire Line
	3600 2550 3750 2550
Text Label 3750 2550 0    40   ~ 0
PWM_WL
Wire Wire Line
	1800 2700 1650 2700
Text Label 1650 2700 0    40   ~ 0
GATE_EN
Wire Wire Line
	3600 2700 3750 2700
Text Label 3750 2700 0    40   ~ 0
FAULT_CLEAR
Wire Wire Line
	1800 2850 1650 2850
Text Label 1650 2850 0    40   ~ 0
ADC_CONVST
Wire Wire Line
	3600 2850 3750 2850
Text Label 3750 2850 0    40   ~ 0
ADC_SCLK
Wire Wire Line
	1800 3000 1650 3000
Text Label 1650 3000 0    40   ~ 0
ADC_CS_N
Wire Wire Line
	3600 3000 3750 3000
Text Label 3750 3000 0    40   ~ 0
ADC_RESET
Wire Wire Line
	1800 3150 1650 3150
Text Label 1650 3150 0    40   ~ 0
ADC_DOUTA
Wire Wire Line
	3600 3150 3750 3150
Text Label 3750 3150 0    40   ~ 0
ADC_DOUTB
Wire Wire Line
	1800 3300 1650 3300
Text Label 1650 3300 0    40   ~ 0
ADC_BUSY
Wire Wire Line
	3600 3300 3750 3300
Text Label 3750 3300 0    40   ~ 0
ADC_FRSTDATA
Wire Wire Line
	1800 3450 1650 3450
Text Label 1650 3450 0    40   ~ 0
ENC_A
Wire Wire Line
	3600 3450 3750 3450
Text Label 3750 3450 0    40   ~ 0
ENC_B
Wire Wire Line
	1800 3550 1650 3550
Text Label 1650 3550 0    40   ~ 0
ENC_Z
Wire Wire Line
	3600 3550 3750 3550
Text Label 3750 3550 0    40   ~ 0
ENC_FAULT_N
Wire Wire Line
	1800 3700 1650 3700
Text Label 1650 3700 0    40   ~ 0
OCP_N
Wire Wire Line
	3600 3700 3750 3700
Text Label 3750 3700 0    40   ~ 0
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
	3600 4750 3750 4750
Text Label 3750 4750 0    40   ~ 0
GND
Wire Wire Line
	1800 4900 1650 4900
Text Label 1650 4900 0    40   ~ 0
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
