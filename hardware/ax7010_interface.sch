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
$EndSCHEMATC
