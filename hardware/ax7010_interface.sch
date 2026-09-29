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
Text HLabel 9200 900 2 50 Output ~ 0
VIO_3V3
Text HLabel 9200 1300 2 50 Output ~ 0
PWM_UH
Text HLabel 9200 1500 2 50 Output ~ 0
PWM_UL
Text HLabel 9200 1700 2 50 Output ~ 0
PWM_VH
Text HLabel 9200 1900 2 50 Output ~ 0
PWM_VL
Text HLabel 9200 2100 2 50 Output ~ 0
PWM_WH
Text HLabel 9200 2300 2 50 Output ~ 0
PWM_WL
Text HLabel 9200 2550 2 50 Output ~ 0
GATE_EN
Text HLabel 9200 2750 2 50 Output ~ 0
FAULT_CLEAR
Text HLabel 9200 3100 2 50 Output ~ 0
ADC_CONVST
Text HLabel 9200 3300 2 50 Output ~ 0
ADC_SCLK
Text HLabel 9200 3500 2 50 Output ~ 0
ADC_CS_N
Text HLabel 9200 3700 2 50 Output ~ 0
ADC_RESET
Text HLabel 9200 4150 0 50 Input ~ 0
ADC_DOUTA
Text HLabel 9200 4350 0 50 Input ~ 0
ADC_DOUTB
Text HLabel 9200 4550 0 50 Input ~ 0
ADC_BUSY
Text HLabel 9200 4750 0 50 Input ~ 0
ADC_FRSTDATA
Text HLabel 9200 5150 0 50 Input ~ 0
ENC_A
Text HLabel 9200 5350 0 50 Input ~ 0
ENC_B
Text HLabel 9200 5550 0 50 Input ~ 0
ENC_Z
Text HLabel 9200 5900 0 50 Input ~ 0
OCP_N
Text HLabel 9200 6100 0 50 Input ~ 0
PWR_GOOD
Text HLabel 9200 6400 1 50 BiDi ~ 0
GND
Text Notes 650 6900 0    45   ~ 12
Electrical mapping is defined in docs/ax7010_interface.md and fpga/ax7010_servo_reva.xdc.
Text Notes 650 7035 0    45   ~ 12
AX7010 +5V pins remain NC. Header 3.3V pins only feed VIO_3V3 domain; they are not paralleled with board-generated 5V.
Text Notes 650 7170 0    45   ~ 12
PWM/control nets receive 100k pulldown footprints at the destination so FPGA configuration/reset defaults are safe-off.
Text Notes 650 7305 0    45   ~ 12
VISIBLE WIRING: both AX7010 2x20 headers now expose explicit per-pin wire stubs and net names; +5V pins remain NoConn.
Wire Wire Line
	1800 2120 1620 2120
Text Label 1620 2120 0    40   ~ 0
GND
NoConn ~ 3600 2120
Wire Wire Line
	1800 2265 1620 2265
Text Label 1620 2265 0    40   ~ 0
PWM_UH
Wire Wire Line
	3600 2265 3780 2265
Text Label 3780 2265 0    40   ~ 0
PWM_UL
Wire Wire Line
	1800 2411 1620 2411
Text Label 1620 2411 0    40   ~ 0
PWM_VH
Wire Wire Line
	3600 2411 3780 2411
Text Label 3780 2411 0    40   ~ 0
PWM_VL
Wire Wire Line
	1800 2556 1620 2556
Text Label 1620 2556 0    40   ~ 0
PWM_WH
Wire Wire Line
	3600 2556 3780 2556
Text Label 3780 2556 0    40   ~ 0
PWM_WL
Wire Wire Line
	1800 2701 1620 2701
Text Label 1620 2701 0    40   ~ 0
GATE_EN
Wire Wire Line
	3600 2701 3780 2701
Text Label 3780 2701 0    40   ~ 0
FAULT_CLEAR
Wire Wire Line
	1800 2846 1620 2846
Text Label 1620 2846 0    40   ~ 0
ADC_CONVST
Wire Wire Line
	3600 2846 3780 2846
Text Label 3780 2846 0    40   ~ 0
ADC_SCLK
Wire Wire Line
	1800 2992 1620 2992
Text Label 1620 2992 0    40   ~ 0
ADC_CS_N
Wire Wire Line
	3600 2992 3780 2992
Text Label 3780 2992 0    40   ~ 0
ADC_RESET
Wire Wire Line
	1800 3137 1620 3137
Text Label 1620 3137 0    40   ~ 0
ADC_DOUTA
Wire Wire Line
	3600 3137 3780 3137
Text Label 3780 3137 0    40   ~ 0
ADC_DOUTB
Wire Wire Line
	1800 3282 1620 3282
Text Label 1620 3282 0    40   ~ 0
ADC_BUSY
Wire Wire Line
	3600 3282 3780 3282
Text Label 3780 3282 0    40   ~ 0
ADC_FRSTDATA
Wire Wire Line
	1800 3427 1620 3427
Text Label 1620 3427 0    40   ~ 0
ENC_A
Wire Wire Line
	3600 3427 3780 3427
Text Label 3780 3427 0    40   ~ 0
ENC_B
Wire Wire Line
	1800 3573 1620 3573
Text Label 1620 3573 0    40   ~ 0
ENC_Z
Wire Wire Line
	3600 3573 3780 3573
Text Label 3780 3573 0    40   ~ 0
ENC_FAULT_N
Wire Wire Line
	1800 3718 1620 3718
Text Label 1620 3718 0    40   ~ 0
OCP_N
Wire Wire Line
	3600 3718 3780 3718
Text Label 3780 3718 0    40   ~ 0
PWR_GOOD
Wire Wire Line
	1800 3863 1620 3863
Text Label 1620 3863 0    40   ~ 0
AUX_IN0
Wire Wire Line
	3600 3863 3780 3863
Text Label 3780 3863 0    40   ~ 0
AUX_IN1
Wire Wire Line
	1800 4008 1620 4008
Text Label 1620 4008 0    40   ~ 0
AUX_OUT0
Wire Wire Line
	3600 4008 3780 4008
Text Label 3780 4008 0    40   ~ 0
AUX_OUT1
Wire Wire Line
	1800 4154 1620 4154
Text Label 1620 4154 0    40   ~ 0
SPARE_A0
Wire Wire Line
	3600 4154 3780 4154
Text Label 3780 4154 0    40   ~ 0
SPARE_A1
Wire Wire Line
	1800 4299 1620 4299
Text Label 1620 4299 0    40   ~ 0
SPARE_A2
Wire Wire Line
	3600 4299 3780 4299
Text Label 3780 4299 0    40   ~ 0
SPARE_A3
Wire Wire Line
	1800 4444 1620 4444
Text Label 1620 4444 0    40   ~ 0
SPARE_A4
Wire Wire Line
	3600 4444 3780 4444
Text Label 3780 4444 0    40   ~ 0
SPARE_A5
Wire Wire Line
	1800 4589 1620 4589
Text Label 1620 4589 0    40   ~ 0
SPARE_A6
Wire Wire Line
	3600 4589 3780 4589
Text Label 3780 4589 0    40   ~ 0
SPARE_A7
Wire Wire Line
	1800 4735 1620 4735
Text Label 1620 4735 0    40   ~ 0
GND
Wire Wire Line
	3600 4735 3780 4735
Text Label 3780 4735 0    40   ~ 0
GND
Wire Wire Line
	1800 4880 1620 4880
Text Label 1620 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	3600 4880 3780 4880
Text Label 3780 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	5100 2120 4920 2120
Text Label 4920 2120 0    40   ~ 0
GND
NoConn ~ 6900 2120
Wire Wire Line
	5100 2265 4920 2265
Text Label 4920 2265 0    40   ~ 0
ADC_DB0
Wire Wire Line
	6900 2265 7080 2265
Text Label 7080 2265 0    40   ~ 0
ADC_DB1
Wire Wire Line
	5100 2411 4920 2411
Text Label 4920 2411 0    40   ~ 0
ADC_DB2
Wire Wire Line
	6900 2411 7080 2411
Text Label 7080 2411 0    40   ~ 0
ADC_DB3
Wire Wire Line
	5100 2556 4920 2556
Text Label 4920 2556 0    40   ~ 0
ADC_DB4
Wire Wire Line
	6900 2556 7080 2556
Text Label 7080 2556 0    40   ~ 0
ADC_DB5
Wire Wire Line
	5100 2701 4920 2701
Text Label 4920 2701 0    40   ~ 0
ADC_DB6
Wire Wire Line
	6900 2701 7080 2701
Text Label 7080 2701 0    40   ~ 0
ADC_DB7
Wire Wire Line
	5100 2846 4920 2846
Text Label 4920 2846 0    40   ~ 0
ADC_DB8
Wire Wire Line
	6900 2846 7080 2846
Text Label 7080 2846 0    40   ~ 0
ADC_DB9
Wire Wire Line
	5100 2992 4920 2992
Text Label 4920 2992 0    40   ~ 0
ADC_DB10
Wire Wire Line
	6900 2992 7080 2992
Text Label 7080 2992 0    40   ~ 0
ADC_DB11
Wire Wire Line
	5100 3137 4920 3137
Text Label 4920 3137 0    40   ~ 0
ADC_DB12
Wire Wire Line
	6900 3137 7080 3137
Text Label 7080 3137 0    40   ~ 0
ADC_DB13
Wire Wire Line
	5100 3282 4920 3282
Text Label 4920 3282 0    40   ~ 0
ADC_DB14
Wire Wire Line
	6900 3282 7080 3282
Text Label 7080 3282 0    40   ~ 0
ADC_DB15
Wire Wire Line
	5100 3427 4920 3427
Text Label 4920 3427 0    40   ~ 0
ADC_RD_N
Wire Wire Line
	6900 3427 7080 3427
Text Label 7080 3427 0    40   ~ 0
ADC_BYTE_SEL
Wire Wire Line
	5100 3573 4920 3573
Text Label 4920 3573 0    40   ~ 0
ADC_RANGE
Wire Wire Line
	6900 3573 7080 3573
Text Label 7080 3573 0    40   ~ 0
ADC_OS0
Wire Wire Line
	5100 3718 4920 3718
Text Label 4920 3718 0    40   ~ 0
ADC_OS1
Wire Wire Line
	6900 3718 7080 3718
Text Label 7080 3718 0    40   ~ 0
ADC_OS2
Wire Wire Line
	5100 3863 4920 3863
Text Label 4920 3863 0    40   ~ 0
ADC_STBY
Wire Wire Line
	6900 3863 7080 3863
Text Label 7080 3863 0    40   ~ 0
ADC_PAR_SER
Wire Wire Line
	5100 4008 4920 4008
Text Label 4920 4008 0    40   ~ 0
HALL_U
Wire Wire Line
	6900 4008 7080 4008
Text Label 7080 4008 0    40   ~ 0
HALL_V
Wire Wire Line
	5100 4154 4920 4154
Text Label 4920 4154 0    40   ~ 0
HALL_W
Wire Wire Line
	6900 4154 7080 4154
Text Label 7080 4154 0    40   ~ 0
BRAKE_OUT
Wire Wire Line
	5100 4299 4920 4299
Text Label 4920 4299 0    40   ~ 0
EXT_FAULT_N
Wire Wire Line
	6900 4299 7080 4299
Text Label 7080 4299 0    40   ~ 0
TEST_TRIG
Wire Wire Line
	5100 4444 4920 4444
Text Label 4920 4444 0    40   ~ 0
SPARE_B0
Wire Wire Line
	6900 4444 7080 4444
Text Label 7080 4444 0    40   ~ 0
SPARE_B1
Wire Wire Line
	5100 4589 4920 4589
Text Label 4920 4589 0    40   ~ 0
SPARE_B2
Wire Wire Line
	6900 4589 7080 4589
Text Label 7080 4589 0    40   ~ 0
SPARE_B3
Wire Wire Line
	5100 4735 4920 4735
Text Label 4920 4735 0    40   ~ 0
GND
Wire Wire Line
	6900 4735 7080 4735
Text Label 7080 4735 0    40   ~ 0
GND
Wire Wire Line
	5100 4880 4920 4880
Text Label 4920 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	6900 4880 7080 4880
Text Label 7080 4880 0    40   ~ 0
VIO_3V3
Wire Wire Line
	9200 900 8980 900
Text Label 8980 900 0    40   ~ 0
VIO_3V3
Wire Wire Line
	9200 1300 8980 1300
Text Label 8980 1300 0    40   ~ 0
PWM_UH
Wire Wire Line
	9200 1500 8980 1500
Text Label 8980 1500 0    40   ~ 0
PWM_UL
Wire Wire Line
	9200 1700 8980 1700
Text Label 8980 1700 0    40   ~ 0
PWM_VH
Wire Wire Line
	9200 1900 8980 1900
Text Label 8980 1900 0    40   ~ 0
PWM_VL
Wire Wire Line
	9200 2100 8980 2100
Text Label 8980 2100 0    40   ~ 0
PWM_WH
Wire Wire Line
	9200 2300 8980 2300
Text Label 8980 2300 0    40   ~ 0
PWM_WL
Wire Wire Line
	9200 2550 8980 2550
Text Label 8980 2550 0    40   ~ 0
GATE_EN
Wire Wire Line
	9200 2750 8980 2750
Text Label 8980 2750 0    40   ~ 0
FAULT_CLEAR
Wire Wire Line
	9200 3100 8980 3100
Text Label 8980 3100 0    40   ~ 0
ADC_CONVST
Wire Wire Line
	9200 3300 8980 3300
Text Label 8980 3300 0    40   ~ 0
ADC_SCLK
Wire Wire Line
	9200 3500 8980 3500
Text Label 8980 3500 0    40   ~ 0
ADC_CS_N
Wire Wire Line
	9200 3700 8980 3700
Text Label 8980 3700 0    40   ~ 0
ADC_RESET
Wire Wire Line
	9200 4150 8980 4150
Text Label 8980 4150 0    40   ~ 0
ADC_DOUTA
Wire Wire Line
	9200 4350 8980 4350
Text Label 8980 4350 0    40   ~ 0
ADC_DOUTB
Wire Wire Line
	9200 4550 8980 4550
Text Label 8980 4550 0    40   ~ 0
ADC_BUSY
Wire Wire Line
	9200 4750 8980 4750
Text Label 8980 4750 0    40   ~ 0
ADC_FRSTDATA
Wire Wire Line
	9200 5150 8980 5150
Text Label 8980 5150 0    40   ~ 0
ENC_A
Wire Wire Line
	9200 5350 8980 5350
Text Label 8980 5350 0    40   ~ 0
ENC_B
Wire Wire Line
	9200 5550 8980 5550
Text Label 8980 5550 0    40   ~ 0
ENC_Z
Wire Wire Line
	9200 5900 8980 5900
Text Label 8980 5900 0    40   ~ 0
OCP_N
Wire Wire Line
	9200 6100 8980 6100
Text Label 8980 6100 0    40   ~ 0
PWR_GOOD
Wire Wire Line
	9200 6400 8980 6400
Text Label 8980 6400 0    40   ~ 0
GND
$EndSCHEMATC
