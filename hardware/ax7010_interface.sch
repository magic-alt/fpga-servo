EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
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
P 3300 4300
F 0 "J1" H 3400 4400 50  0000 C CNN
F 1 "AX7010_PL_A" H 3400 4200 50  0000 C CNN
F 2 "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical" H 3300 4300 50  0001 C CNN
	1    3300 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:HDR_2x20 J2
U 1 1 66000064
P 7800 4300
F 0 "J2" H 7900 4400 50  0000 C CNN
F 1 "AX7010_PL_B" H 7900 4200 50  0000 C CNN
F 2 "Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical" H 7800 4300 50  0001 C CNN
	1    7800 4300
	1 0 0 -1
$EndComp
Text HLabel 14500 1300 2    50   Output ~ 0
VIO_3V3
Text HLabel 14500 1800 2    50   Output ~ 0
PWM_UH
Text HLabel 14500 2060 2    50   Output ~ 0
PWM_UL
Text HLabel 14500 2320 2    50   Output ~ 0
PWM_VH
Text HLabel 14500 2580 2    50   Output ~ 0
PWM_VL
Text HLabel 14500 2840 2    50   Output ~ 0
PWM_WH
Text HLabel 14500 3100 2    50   Output ~ 0
PWM_WL
Text HLabel 14500 3360 2    50   Output ~ 0
GATE_EN
Text HLabel 14500 3620 2    50   Output ~ 0
FAULT_CLEAR
Text HLabel 14500 3880 2    50   Output ~ 0
ADC_CONVST
Text HLabel 14500 4140 2    50   Output ~ 0
ADC_SCLK
Text HLabel 14500 4400 2    50   Output ~ 0
ADC_CS_N
Text HLabel 14500 4660 2    50   Output ~ 0
ADC_RESET
Text HLabel 14500 5200 0    50   Input ~ 0
ADC_DOUTA
Text HLabel 14500 5460 0    50   Input ~ 0
ADC_DOUTB
Text HLabel 14500 5720 0    50   Input ~ 0
ADC_BUSY
Text HLabel 14500 5980 0    50   Input ~ 0
ADC_FRSTDATA
Text HLabel 14500 6240 0    50   Input ~ 0
ENC_A
Text HLabel 14500 6500 0    50   Input ~ 0
ENC_B
Text HLabel 14500 6760 0    50   Input ~ 0
ENC_Z
Text HLabel 14500 7020 0    50   Input ~ 0
OCP_N
Text HLabel 14500 7280 0    50   Input ~ 0
PWR_GOOD
Text HLabel 14500 7800 1    50   BiDi ~ 0
GND
Text Notes 600 9000 0    70   ~ 12
Electrical mapping is defined in docs/ax7010_interface.md and fpga/ax7010_servo_reva.xdc.
Text Notes 600 9150 0    70   ~ 12
AX7010 +5V pins remain NC. Header 3.3V pins only feed VIO_3V3 domain; they are not paralleled with board-generated 5V.
Text Notes 600 9300 0    70   ~ 12
PWM/control nets receive 100k pulldown footprints at the destination so FPGA configuration/reset defaults are safe-off.
Text Notes 600 10450 0    55   ~ 12
VISIBLE WIRING: both AX7010 2x20 headers now expose explicit per-pin wire stubs and net names; +5V pins remain NoConn.
Wire Wire Line
	2400 2920 2050 2920
Text Label 2050 2920 0    45   ~ 0
GND
NoConn ~ 4200 2920
Wire Wire Line
	2400 3065 2050 3065
Text Label 2050 3065 0    45   ~ 0
PWM_UH
Wire Wire Line
	4200 3065 4550 3065
Text Label 4550 3065 0    45   ~ 0
PWM_UL
Wire Wire Line
	2400 3211 2050 3211
Text Label 2050 3211 0    45   ~ 0
PWM_VH
Wire Wire Line
	4200 3211 4550 3211
Text Label 4550 3211 0    45   ~ 0
PWM_VL
Wire Wire Line
	2400 3356 2050 3356
Text Label 2050 3356 0    45   ~ 0
PWM_WH
Wire Wire Line
	4200 3356 4550 3356
Text Label 4550 3356 0    45   ~ 0
PWM_WL
Wire Wire Line
	2400 3501 2050 3501
Text Label 2050 3501 0    45   ~ 0
GATE_EN
Wire Wire Line
	4200 3501 4550 3501
Text Label 4550 3501 0    45   ~ 0
FAULT_CLEAR
Wire Wire Line
	2400 3646 2050 3646
Text Label 2050 3646 0    45   ~ 0
ADC_CONVST
Wire Wire Line
	4200 3646 4550 3646
Text Label 4550 3646 0    45   ~ 0
ADC_SCLK
Wire Wire Line
	2400 3792 2050 3792
Text Label 2050 3792 0    45   ~ 0
ADC_CS_N
Wire Wire Line
	4200 3792 4550 3792
Text Label 4550 3792 0    45   ~ 0
ADC_RESET
Wire Wire Line
	2400 3937 2050 3937
Text Label 2050 3937 0    45   ~ 0
ADC_DOUTA
Wire Wire Line
	4200 3937 4550 3937
Text Label 4550 3937 0    45   ~ 0
ADC_DOUTB
Wire Wire Line
	2400 4082 2050 4082
Text Label 2050 4082 0    45   ~ 0
ADC_BUSY
Wire Wire Line
	4200 4082 4550 4082
Text Label 4550 4082 0    45   ~ 0
ADC_FRSTDATA
Wire Wire Line
	2400 4227 2050 4227
Text Label 2050 4227 0    45   ~ 0
ENC_A
Wire Wire Line
	4200 4227 4550 4227
Text Label 4550 4227 0    45   ~ 0
ENC_B
Wire Wire Line
	2400 4373 2050 4373
Text Label 2050 4373 0    45   ~ 0
ENC_Z
Wire Wire Line
	4200 4373 4550 4373
Text Label 4550 4373 0    45   ~ 0
ENC_FAULT_N
Wire Wire Line
	2400 4518 2050 4518
Text Label 2050 4518 0    45   ~ 0
OCP_N
Wire Wire Line
	4200 4518 4550 4518
Text Label 4550 4518 0    45   ~ 0
PWR_GOOD
Wire Wire Line
	2400 4663 2050 4663
Text Label 2050 4663 0    45   ~ 0
AUX_IN0
Wire Wire Line
	4200 4663 4550 4663
Text Label 4550 4663 0    45   ~ 0
AUX_IN1
Wire Wire Line
	2400 4808 2050 4808
Text Label 2050 4808 0    45   ~ 0
AUX_OUT0
Wire Wire Line
	4200 4808 4550 4808
Text Label 4550 4808 0    45   ~ 0
AUX_OUT1
Wire Wire Line
	2400 4954 2050 4954
Text Label 2050 4954 0    45   ~ 0
SPARE_A0
Wire Wire Line
	4200 4954 4550 4954
Text Label 4550 4954 0    45   ~ 0
SPARE_A1
Wire Wire Line
	2400 5099 2050 5099
Text Label 2050 5099 0    45   ~ 0
SPARE_A2
Wire Wire Line
	4200 5099 4550 5099
Text Label 4550 5099 0    45   ~ 0
SPARE_A3
Wire Wire Line
	2400 5244 2050 5244
Text Label 2050 5244 0    45   ~ 0
SPARE_A4
Wire Wire Line
	4200 5244 4550 5244
Text Label 4550 5244 0    45   ~ 0
SPARE_A5
Wire Wire Line
	2400 5389 2050 5389
Text Label 2050 5389 0    45   ~ 0
SPARE_A6
Wire Wire Line
	4200 5389 4550 5389
Text Label 4550 5389 0    45   ~ 0
SPARE_A7
Wire Wire Line
	2400 5535 2050 5535
Text Label 2050 5535 0    45   ~ 0
GND
Wire Wire Line
	4200 5535 4550 5535
Text Label 4550 5535 0    45   ~ 0
GND
Wire Wire Line
	2400 5680 2050 5680
Text Label 2050 5680 0    45   ~ 0
VIO_3V3
Wire Wire Line
	4200 5680 4550 5680
Text Label 4550 5680 0    45   ~ 0
VIO_3V3
Wire Wire Line
	6900 2920 6550 2920
Text Label 6550 2920 0    45   ~ 0
GND
NoConn ~ 8700 2920
Wire Wire Line
	6900 3065 6550 3065
Text Label 6550 3065 0    45   ~ 0
ADC_DB0
Wire Wire Line
	8700 3065 9050 3065
Text Label 9050 3065 0    45   ~ 0
ADC_DB1
Wire Wire Line
	6900 3211 6550 3211
Text Label 6550 3211 0    45   ~ 0
ADC_DB2
Wire Wire Line
	8700 3211 9050 3211
Text Label 9050 3211 0    45   ~ 0
ADC_DB3
Wire Wire Line
	6900 3356 6550 3356
Text Label 6550 3356 0    45   ~ 0
ADC_DB4
Wire Wire Line
	8700 3356 9050 3356
Text Label 9050 3356 0    45   ~ 0
ADC_DB5
Wire Wire Line
	6900 3501 6550 3501
Text Label 6550 3501 0    45   ~ 0
ADC_DB6
Wire Wire Line
	8700 3501 9050 3501
Text Label 9050 3501 0    45   ~ 0
ADC_DB7
Wire Wire Line
	6900 3646 6550 3646
Text Label 6550 3646 0    45   ~ 0
ADC_DB8
Wire Wire Line
	8700 3646 9050 3646
Text Label 9050 3646 0    45   ~ 0
ADC_DB9
Wire Wire Line
	6900 3792 6550 3792
Text Label 6550 3792 0    45   ~ 0
ADC_DB10
Wire Wire Line
	8700 3792 9050 3792
Text Label 9050 3792 0    45   ~ 0
ADC_DB11
Wire Wire Line
	6900 3937 6550 3937
Text Label 6550 3937 0    45   ~ 0
ADC_DB12
Wire Wire Line
	8700 3937 9050 3937
Text Label 9050 3937 0    45   ~ 0
ADC_DB13
Wire Wire Line
	6900 4082 6550 4082
Text Label 6550 4082 0    45   ~ 0
ADC_DB14
Wire Wire Line
	8700 4082 9050 4082
Text Label 9050 4082 0    45   ~ 0
ADC_DB15
Wire Wire Line
	6900 4227 6550 4227
Text Label 6550 4227 0    45   ~ 0
ADC_RD_N
Wire Wire Line
	8700 4227 9050 4227
Text Label 9050 4227 0    45   ~ 0
ADC_BYTE_SEL
Wire Wire Line
	6900 4373 6550 4373
Text Label 6550 4373 0    45   ~ 0
ADC_RANGE
Wire Wire Line
	8700 4373 9050 4373
Text Label 9050 4373 0    45   ~ 0
ADC_OS0
Wire Wire Line
	6900 4518 6550 4518
Text Label 6550 4518 0    45   ~ 0
ADC_OS1
Wire Wire Line
	8700 4518 9050 4518
Text Label 9050 4518 0    45   ~ 0
ADC_OS2
Wire Wire Line
	6900 4663 6550 4663
Text Label 6550 4663 0    45   ~ 0
ADC_STBY
Wire Wire Line
	8700 4663 9050 4663
Text Label 9050 4663 0    45   ~ 0
ADC_PAR_SER
Wire Wire Line
	6900 4808 6550 4808
Text Label 6550 4808 0    45   ~ 0
HALL_U
Wire Wire Line
	8700 4808 9050 4808
Text Label 9050 4808 0    45   ~ 0
HALL_V
Wire Wire Line
	6900 4954 6550 4954
Text Label 6550 4954 0    45   ~ 0
HALL_W
Wire Wire Line
	8700 4954 9050 4954
Text Label 9050 4954 0    45   ~ 0
BRAKE_OUT
Wire Wire Line
	6900 5099 6550 5099
Text Label 6550 5099 0    45   ~ 0
EXT_FAULT_N
Wire Wire Line
	8700 5099 9050 5099
Text Label 9050 5099 0    45   ~ 0
TEST_TRIG
Wire Wire Line
	6900 5244 6550 5244
Text Label 6550 5244 0    45   ~ 0
SPARE_B0
Wire Wire Line
	8700 5244 9050 5244
Text Label 9050 5244 0    45   ~ 0
SPARE_B1
Wire Wire Line
	6900 5389 6550 5389
Text Label 6550 5389 0    45   ~ 0
SPARE_B2
Wire Wire Line
	8700 5389 9050 5389
Text Label 9050 5389 0    45   ~ 0
SPARE_B3
Wire Wire Line
	6900 5535 6550 5535
Text Label 6550 5535 0    45   ~ 0
GND
Wire Wire Line
	8700 5535 9050 5535
Text Label 9050 5535 0    45   ~ 0
GND
Wire Wire Line
	6900 5680 6550 5680
Text Label 6550 5680 0    45   ~ 0
VIO_3V3
Wire Wire Line
	8700 5680 9050 5680
Text Label 9050 5680 0    45   ~ 0
VIO_3V3
Wire Wire Line
	14500 1300 14050 1300
Text Label 14050 1300 0    45   ~ 0
VIO_3V3
Wire Wire Line
	14500 1800 14050 1800
Text Label 14050 1800 0    45   ~ 0
PWM_UH
Wire Wire Line
	14500 2060 14050 2060
Text Label 14050 2060 0    45   ~ 0
PWM_UL
Wire Wire Line
	14500 2320 14050 2320
Text Label 14050 2320 0    45   ~ 0
PWM_VH
Wire Wire Line
	14500 2580 14050 2580
Text Label 14050 2580 0    45   ~ 0
PWM_VL
Wire Wire Line
	14500 2840 14050 2840
Text Label 14050 2840 0    45   ~ 0
PWM_WH
Wire Wire Line
	14500 3100 14050 3100
Text Label 14050 3100 0    45   ~ 0
PWM_WL
Wire Wire Line
	14500 3360 14050 3360
Text Label 14050 3360 0    45   ~ 0
GATE_EN
Wire Wire Line
	14500 3620 14050 3620
Text Label 14050 3620 0    45   ~ 0
FAULT_CLEAR
Wire Wire Line
	14500 3880 14050 3880
Text Label 14050 3880 0    45   ~ 0
ADC_CONVST
Wire Wire Line
	14500 4140 14050 4140
Text Label 14050 4140 0    45   ~ 0
ADC_SCLK
Wire Wire Line
	14500 4400 14050 4400
Text Label 14050 4400 0    45   ~ 0
ADC_CS_N
Wire Wire Line
	14500 4660 14050 4660
Text Label 14050 4660 0    45   ~ 0
ADC_RESET
Wire Wire Line
	14500 5200 14050 5200
Text Label 14050 5200 0    45   ~ 0
ADC_DOUTA
Wire Wire Line
	14500 5460 14050 5460
Text Label 14050 5460 0    45   ~ 0
ADC_DOUTB
Wire Wire Line
	14500 5720 14050 5720
Text Label 14050 5720 0    45   ~ 0
ADC_BUSY
Wire Wire Line
	14500 5980 14050 5980
Text Label 14050 5980 0    45   ~ 0
ADC_FRSTDATA
Wire Wire Line
	14500 6240 14050 6240
Text Label 14050 6240 0    45   ~ 0
ENC_A
Wire Wire Line
	14500 6500 14050 6500
Text Label 14050 6500 0    45   ~ 0
ENC_B
Wire Wire Line
	14500 6760 14050 6760
Text Label 14050 6760 0    45   ~ 0
ENC_Z
Wire Wire Line
	14500 7020 14050 7020
Text Label 14050 7020 0    45   ~ 0
OCP_N
Wire Wire Line
	14500 7280 14050 7280
Text Label 14050 7280 0    45   ~ 0
PWR_GOOD
Wire Wire Line
	14500 7800 14050 7800
Text Label 14050 7800 0    45   ~ 0
GND
$EndSCHEMATC
