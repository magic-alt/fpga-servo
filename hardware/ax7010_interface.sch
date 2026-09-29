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
	10600 900 10420 900
Wire Wire Line
	10600 1350 10420 1350
Wire Wire Line
	10600 1550 10420 1550
Wire Wire Line
	10600 1750 10420 1750
Wire Wire Line
	10600 1950 10420 1950
Wire Wire Line
	10600 2150 10420 2150
Wire Wire Line
	10600 2350 10420 2350
Wire Wire Line
	10600 2600 10420 2600
Wire Wire Line
	10600 2800 10420 2800
Wire Wire Line
	10600 3250 10420 3250
Wire Wire Line
	10600 3450 10420 3450
Wire Wire Line
	10600 3650 10420 3650
Wire Wire Line
	10600 3850 10420 3850
Wire Wire Line
	10600 4300 10780 4300
Wire Wire Line
	10600 4500 10780 4500
Wire Wire Line
	10600 4700 10780 4700
Wire Wire Line
	10600 4900 10780 4900
Wire Wire Line
	10600 5350 10780 5350
Wire Wire Line
	10600 5550 10780 5550
Wire Wire Line
	10600 5750 10780 5750
Wire Wire Line
	10600 6100 10780 6100
Wire Wire Line
	10600 6300 10780 6300
Wire Wire Line
	10600 6600 10600 6780
Wire Wire Line
	1800 2120 1695 2120
Text Label 1695 2120 0    40   ~ 0
GND
NoConn ~ 3600 2120
Wire Wire Line
	1800 2265 1695 2265
Text Label 1695 2265 0    40   ~ 0
PWM_UH
Wire Wire Line
	3600 2265 3705 2265
Text Label 3705 2265 0    40   ~ 0
PWM_UL
Wire Wire Line
	1800 2411 1695 2411
Text Label 1695 2411 0    40   ~ 0
PWM_VH
Wire Wire Line
	3600 2411 3705 2411
Text Label 3705 2411 0    40   ~ 0
PWM_VL
Wire Wire Line
	1800 2556 1695 2556
Text Label 1695 2556 0    40   ~ 0
PWM_WH
Wire Wire Line
	3600 2556 3705 2556
Text Label 3705 2556 0    40   ~ 0
PWM_WL
Wire Wire Line
	1800 2701 1695 2701
Text Label 1695 2701 0    40   ~ 0
GATE_EN
Wire Wire Line
	3600 2701 3705 2701
Text Label 3705 2701 0    40   ~ 0
FAULT_CLEAR
Wire Wire Line
	1800 2846 1695 2846
Text Label 1695 2846 0    40   ~ 0
ADC_CONVST
Wire Wire Line
	3600 2846 3705 2846
Text Label 3705 2846 0    40   ~ 0
ADC_SCLK
Wire Wire Line
	1800 2992 1695 2992
Text Label 1695 2992 0    40   ~ 0
ADC_CS_N
Wire Wire Line
	3600 2992 3705 2992
Text Label 3705 2992 0    40   ~ 0
ADC_RESET
Wire Wire Line
	1800 3137 1695 3137
Text Label 1695 3137 0    40   ~ 0
ADC_DOUTA
Wire Wire Line
	3600 3137 3705 3137
Text Label 3705 3137 0    40   ~ 0
ADC_DOUTB
Wire Wire Line
	1800 3282 1695 3282
Text Label 1695 3282 0    40   ~ 0
ADC_BUSY
Wire Wire Line
	3600 3282 3705 3282
Text Label 3705 3282 0    40   ~ 0
ADC_FRSTDATA
Wire Wire Line
	1800 3427 1695 3427
Text Label 1695 3427 0    40   ~ 0
ENC_A
Wire Wire Line
	3600 3427 3705 3427
Text Label 3705 3427 0    40   ~ 0
ENC_B
Wire Wire Line
	1800 3573 1695 3573
Text Label 1695 3573 0    40   ~ 0
ENC_Z
Wire Wire Line
	3600 3573 3705 3573
Text Label 3705 3573 0    40   ~ 0
ENC_FAULT_N
Wire Wire Line
	1800 3718 1695 3718
Text Label 1695 3718 0    40   ~ 0
OCP_N
Wire Wire Line
	3600 3718 3705 3718
Text Label 3705 3718 0    40   ~ 0
PWR_GOOD
Wire Wire Line
	1800 3863 1695 3863
Text Label 1695 3863 0    40   ~ 0
AUX_IN0
Wire Wire Line
	3600 3863 3705 3863
Text Label 3705 3863 0    40   ~ 0
AUX_IN1
Wire Wire Line
	1800 4008 1695 4008
Text Label 1695 4008 0    40   ~ 0
AUX_OUT0
Wire Wire Line
	3600 4008 3705 4008
Text Label 3705 4008 0    40   ~ 0
AUX_OUT1
Wire Wire Line
	1800 4154 1695 4154
Text Label 1695 4154 0    40   ~ 0
SPARE_A0
Wire Wire Line
	3600 4154 3705 4154
Text Label 3705 4154 0    40   ~ 0
SPARE_A1
Wire Wire Line
	1800 4299 1695 4299
Text Label 1695 4299 0    40   ~ 0
SPARE_A2
Wire Wire Line
	3600 4299 3705 4299
Text Label 3705 4299 0    40   ~ 0
SPARE_A3
Wire Wire Line
	1800 4444 1695 4444
Text Label 1695 4444 0    40   ~ 0
SPARE_A4
Wire Wire Line
	3600 4444 3705 4444
Text Label 3705 4444 0    40   ~ 0
SPARE_A5
Wire Wire Line
	1800 4589 1695 4589
Text Label 1695 4589 0    40   ~ 0
SPARE_A6
Wire Wire Line
	3600 4589 3705 4589
Text Label 3705 4589 0    40   ~ 0
SPARE_A7
Wire Wire Line
	1800 4735 1695 4735
Text Label 1695 4735 0    40   ~ 0
GND
Wire Wire Line
	3600 4735 3705 4735
Text Label 3705 4735 0    40   ~ 0
GND
Wire Wire Line
	1800 4880 1695 4880
Text Label 1695 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	3600 4880 3705 4880
Text Label 3705 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	5100 2120 4995 2120
Text Label 4995 2120 0    40   ~ 0
GND
NoConn ~ 6900 2120
Wire Wire Line
	5100 2265 4995 2265
Text Label 4995 2265 0    40   ~ 0
ADC_DB0
Wire Wire Line
	6900 2265 7005 2265
Text Label 7005 2265 0    40   ~ 0
ADC_DB1
Wire Wire Line
	5100 2411 4995 2411
Text Label 4995 2411 0    40   ~ 0
ADC_DB2
Wire Wire Line
	6900 2411 7005 2411
Text Label 7005 2411 0    40   ~ 0
ADC_DB3
Wire Wire Line
	5100 2556 4995 2556
Text Label 4995 2556 0    40   ~ 0
ADC_DB4
Wire Wire Line
	6900 2556 7005 2556
Text Label 7005 2556 0    40   ~ 0
ADC_DB5
Wire Wire Line
	5100 2701 4995 2701
Text Label 4995 2701 0    40   ~ 0
ADC_DB6
Wire Wire Line
	6900 2701 7005 2701
Text Label 7005 2701 0    40   ~ 0
ADC_DB7
Wire Wire Line
	5100 2846 4995 2846
Text Label 4995 2846 0    40   ~ 0
ADC_DB8
Wire Wire Line
	6900 2846 7005 2846
Text Label 7005 2846 0    40   ~ 0
ADC_DB9
Wire Wire Line
	5100 2992 4995 2992
Text Label 4995 2992 0    40   ~ 0
ADC_DB10
Wire Wire Line
	6900 2992 7005 2992
Text Label 7005 2992 0    40   ~ 0
ADC_DB11
Wire Wire Line
	5100 3137 4995 3137
Text Label 4995 3137 0    40   ~ 0
ADC_DB12
Wire Wire Line
	6900 3137 7005 3137
Text Label 7005 3137 0    40   ~ 0
ADC_DB13
Wire Wire Line
	5100 3282 4995 3282
Text Label 4995 3282 0    40   ~ 0
ADC_DB14
Wire Wire Line
	6900 3282 7005 3282
Text Label 7005 3282 0    40   ~ 0
ADC_DB15
Wire Wire Line
	5100 3427 4995 3427
Text Label 4995 3427 0    40   ~ 0
ADC_RD_N
Wire Wire Line
	6900 3427 7005 3427
Text Label 7005 3427 0    40   ~ 0
ADC_BYTE_SEL
Wire Wire Line
	5100 3573 4995 3573
Text Label 4995 3573 0    40   ~ 0
ADC_RANGE
Wire Wire Line
	6900 3573 7005 3573
Text Label 7005 3573 0    40   ~ 0
ADC_OS0
Wire Wire Line
	5100 3718 4995 3718
Text Label 4995 3718 0    40   ~ 0
ADC_OS1
Wire Wire Line
	6900 3718 7005 3718
Text Label 7005 3718 0    40   ~ 0
ADC_OS2
Wire Wire Line
	5100 3863 4995 3863
Text Label 4995 3863 0    40   ~ 0
ADC_STBY
Wire Wire Line
	6900 3863 7005 3863
Text Label 7005 3863 0    40   ~ 0
ADC_PAR_SER
Wire Wire Line
	5100 4008 4995 4008
Text Label 4995 4008 0    40   ~ 0
HALL_U
Wire Wire Line
	6900 4008 7005 4008
Text Label 7005 4008 0    40   ~ 0
HALL_V
Wire Wire Line
	5100 4154 4995 4154
Text Label 4995 4154 0    40   ~ 0
HALL_W
Wire Wire Line
	6900 4154 7005 4154
Text Label 7005 4154 0    40   ~ 0
BRAKE_OUT
Wire Wire Line
	5100 4299 4995 4299
Text Label 4995 4299 0    40   ~ 0
EXT_FAULT_N
Wire Wire Line
	6900 4299 7005 4299
Text Label 7005 4299 0    40   ~ 0
TEST_TRIG
Wire Wire Line
	5100 4444 4995 4444
Text Label 4995 4444 0    40   ~ 0
SPARE_B0
Wire Wire Line
	6900 4444 7005 4444
Text Label 7005 4444 0    40   ~ 0
SPARE_B1
Wire Wire Line
	5100 4589 4995 4589
Text Label 4995 4589 0    40   ~ 0
SPARE_B2
Wire Wire Line
	6900 4589 7005 4589
Text Label 7005 4589 0    40   ~ 0
SPARE_B3
Wire Wire Line
	5100 4735 4995 4735
Text Label 4995 4735 0    40   ~ 0
GND
Wire Wire Line
	6900 4735 7005 4735
Text Label 7005 4735 0    40   ~ 0
GND
Wire Wire Line
	5100 4880 4995 4880
Text Label 4995 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	6900 4880 7005 4880
Text Label 7005 4880 0    40   ~ 0
VIO_3V3
$EndSCHEMATC
