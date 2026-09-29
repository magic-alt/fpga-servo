EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
Sheet 1 1
Title "Rev.A1 - DC Input & Protection"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "48V-class bus; 15..55V design window; source transient qualification required"
$EndDescr
Text Notes 600 500 0    70   ~ 12
DC INPUT -> FUSE -> LM74502 + BACK-TO-BACK NFET RPP -> LOCAL DC-LINK
$Comp
L ax7010_servo_reva:TERM2 J3
U 1 1 66000001
P 1000 1800
F 0 "J3" H 1100 1900 50  0000 C CNN
F 1 "DC_IN_48V" H 1100 1700 50  0000 C CNN
F 2 "TerminalBlock:TerminalBlock_bornier-2_P7.62mm" H 1000 1800 50  0001 C CNN
	1    1000 1800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:FUSE F1
U 1 1 66000002
P 2200 1650
F 0 "F1" H 2300 1750 50  0000 C CNN
F 1 "EXT_FUSE_OR_25A_FUSE" H 2300 1550 50  0000 C CNN
F 2 "Fuse:Fuse_2920_7451Metric" H 2200 1650 50  0001 C CNN
	1    2200 1650
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:NFET_HORIZ Q7
U 1 1 66000003
P 5600 1650
F 0 "Q7" H 5700 1750 50  0000 C CNN
F 1 "BSC040N10NS5_RPP_Q7" H 5700 1550 50  0000 C CNN
F 2 "Package_DFN_QFN:TDSON-8-1_5x6mm_P1.27mm" H 5600 1650 50  0001 C CNN
	1    5600 1650
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:NFET_HORIZ_REV Q8
U 1 1 6ABAF000
P 6800 1650
F 0 "Q8" H 6900 1750 50  0000 C CNN
F 1 "BSC040N10NS5_RPP_Q8" H 6900 1550 50  0000 C CNN
F 2 "Package_DFN_QFN:TDSON-8-1_5x6mm_P1.27mm" H 6800 1650 50  0001 C CNN
	1    6800 1650
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C19
U 1 1 6ABAF001
P 5850 3450
F 0 "C19" H 5950 3550 50  0000 C CNN
F 1 "100nF_VS_BYPASS" H 5950 3350 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 5850 3450 50  0001 C CNN
	1    5850 3450
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:LM74502 U18
U 1 1 66000004
P 4100 2700
F 0 "U18" H 4200 2800 50  0000 C CNN
F 1 "LM74502DDFR" H 4200 2600 50  0000 C CNN
F 2 "Package_TO_SOT_SMD:SOT-23-8" H 4100 2700 50  0001 C CNN
	1    4100 2700
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C18
U 1 1 66000005
P 5000 3350
F 0 "C18" H 5100 3450 50  0000 C CNN
F 1 "220nF_25V_VCAP" H 5100 3250 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 5000 3350 50  0001 C CNN
	1    5000 3350
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TVS D1
U 1 1 66000006
P 6800 2800
F 0 "D1" H 6900 2900 50  0000 C CNN
F 1 "SMCJ54A_DNP_VERIFY_CLAMP" H 6900 2700 50  0000 C CNN
F 2 "Diode_SMD:D_SMC" H 6800 2800 50  0001 C CNN
	1    6800 2800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C1
U 1 1 66000007
P 7800 2800
F 0 "C1" H 7900 2900 50  0000 C CNN
F 1 "100uF_100V" H 7900 2700 50  0000 C CNN
F 2 "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm" H 7800 2800 50  0001 C CNN
	1    7800 2800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C2
U 1 1 66000008
P 8500 2800
F 0 "C2" H 8600 2900 50  0000 C CNN
F 1 "100uF_100V" H 8600 2700 50  0000 C CNN
F 2 "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm" H 8500 2800 50  0001 C CNN
	1    8500 2800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C3
U 1 1 66000009
P 9200 2800
F 0 "C3" H 9300 2900 50  0000 C CNN
F 1 "1uF_100V_FILM" H 9300 2700 50  0000 C CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 9200 2800 50  0001 C CNN
	1    9200 2800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C4
U 1 1 6600000A
P 9900 2800
F 0 "C4" H 10000 2900 50  0000 C CNN
F 1 "100nF_100V_C0G" H 10000 2700 50  0000 C CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 9900 2800 50  0001 C CNN
	1    9900 2800
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R1
U 1 1 6600000B
P 7600 4300
F 0 "R1" H 7700 4400 50  0000 C CNN
F 1 "280k_0.1%" H 7700 4200 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 7600 4300 50  0001 C CNN
	1    7600 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R2
U 1 1 6600000C
P 8600 4300
F 0 "R2" H 8700 4400 50  0000 C CNN
F 1 "280k_0.1%" H 8700 4200 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 8600 4300 50  0001 C CNN
	1    8600 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R3
U 1 1 6600000D
P 9600 4300
F 0 "R3" H 9700 4400 50  0000 C CNN
F 1 "39k_0.1%" H 9700 4200 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 9600 4300 50  0001 C CNN
	1    9600 4300
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C5
U 1 1 6600000E
P 10400 4750
F 0 "C5" H 10500 4850 50  0000 C CNN
F 1 "10nF_VBUS_SENSE" H 10500 4650 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 10400 4750 50  0001 C CNN
	1    10400 4750
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TP TP1
U 1 1 6600000F
P 10900 1650
F 0 "TP1" H 11000 1750 50  0000 C CNN
F 1 "TP_VBUS_PROT" H 11000 1550 50  0000 C CNN
F 2 "TestPoint:TestPoint_Pad_D2.0mm" H 10900 1650 50  0001 C CNN
	1    10900 1650
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TP TP2
U 1 1 66000010
P 10900 3300
F 0 "TP2" H 11000 3400 50  0000 C CNN
F 1 "TP_GND" H 11000 3200 50  0000 C CNN
F 2 "TestPoint:TestPoint_Pad_D2.0mm" H 10900 3300 50  0001 C CNN
	1    10900 3300
	1 0 0 -1
$EndComp
Text HLabel 12100 1650 2    50   Output ~ 0
VBUS_PROT
Text HLabel 12100 4300 2    50   Output ~ 0
VBUS_ADC
Text HLabel 12100 3300 1    50   BiDi ~ 0
GND
Text Notes 600 5600 0    60   ~ 12
Q7/Q8 are back-to-back N-MOSFETs driven by LM74502 for low-loss reverse-polarity protection. The controller has no reverse-current blocking when enabled, so regeneration can return to a receptive source.
Text Notes 600 5770 0    60   ~ 12
LM74502 OV is tied low in Rev.A1; positive surge is NOT claimed as closed. The 48V source/cable transient must be measured and kept inside the controller/downstream qualification envelope.
Text Notes 600 5940 0    60   ~ 12
D1 remains a DNP TVS footprint until clamping voltage is selected from the actual source impedance. F1 is a local placeholder; upstream source-rated over-current protection is mandatory.
Text Notes 600 6110 0    60   ~ 12
VBUS_ADC divider = 280k + 280k over 39k, plus 10nF at the ADC node. Keep the high-side resistors split for voltage stress and route the sense return away from commutation current.
Text Notes 600 10450 0    55   ~ 12
VISIBLE WIRING: power input and protection pins use explicit wire stubs; unused pins are explicit NoConn.
Wire Wire Line
	450 1800 100 1800
Text Label 100 1800 0    45   ~ 0
VIN_RAW
Wire Wire Line
	1550 1800 1900 1800
Text Label 1900 1800 0    45   ~ 0
GND
Wire Wire Line
	1890 1650 1540 1650
Text Label 1540 1650 0    45   ~ 0
VIN_RAW
Wire Wire Line
	2510 1650 2860 1650
Text Label 2860 1650 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	5600 2200 5600 2550
Text Label 5600 2550 0    45   ~ 0
RPP_GATE
Wire Wire Line
	6200 1650 6550 1650
Text Label 6550 1650 0    45   ~ 0
RPP_SRC
Wire Wire Line
	5000 1650 4650 1650
Text Label 4650 1650 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	6800 2200 6800 2550
Text Label 6800 2550 0    45   ~ 0
RPP_GATE
Wire Wire Line
	6200 1650 5850 1650
Text Label 5850 1650 0    45   ~ 0
RPP_SRC
Wire Wire Line
	7400 1650 7750 1650
Text Label 7750 1650 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	3350 2420 3000 2420
Text Label 3000 2420 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	4100 3420 4100 3770
Text Label 4100 3770 0    45   ~ 0
GND
NoConn ~ 3350 2980
Wire Wire Line
	4850 2960 5200 2960
Text Label 5200 2960 0    45   ~ 0
VCAP_RPP
Wire Wire Line
	4850 2780 5200 2780
Text Label 5200 2780 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	4850 2600 5200 2600
Text Label 5200 2600 0    45   ~ 0
RPP_GATE
Wire Wire Line
	3350 2780 3000 2780
Text Label 3000 2780 0    45   ~ 0
GND
Wire Wire Line
	4850 2420 5200 2420
Text Label 5200 2420 0    45   ~ 0
RPP_SRC
Wire Wire Line
	5000 3100 5000 2750
Text Label 5000 2750 0    45   ~ 0
VCAP_RPP
Wire Wire Line
	5000 3600 5000 3950
Text Label 5000 3950 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	5850 3200 5850 2850
Text Label 5850 2850 0    45   ~ 0
VIN_FUSED
Wire Wire Line
	5850 3700 5850 4050
Text Label 5850 4050 0    45   ~ 0
GND
Wire Wire Line
	6800 3100 6800 3450
Text Label 6800 3450 0    45   ~ 0
GND
Wire Wire Line
	6800 2500 6800 2150
Text Label 6800 2150 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	7800 2550 7800 2200
Text Label 7800 2200 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	7800 3050 7800 3400
Text Label 7800 3400 0    45   ~ 0
GND
Wire Wire Line
	8500 2550 8500 2200
Text Label 8500 2200 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	8500 3050 8500 3400
Text Label 8500 3400 0    45   ~ 0
GND
Wire Wire Line
	9200 2550 9200 2200
Text Label 9200 2200 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	9200 3050 9200 3400
Text Label 9200 3400 0    45   ~ 0
GND
Wire Wire Line
	9900 2550 9900 2200
Text Label 9900 2200 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	9900 3050 9900 3400
Text Label 9900 3400 0    45   ~ 0
GND
Wire Wire Line
	7300 4300 6950 4300
Text Label 6950 4300 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	7900 4300 8250 4300
Text Label 8250 4300 0    45   ~ 0
VBUS_DIV_MID
Wire Wire Line
	8300 4300 7950 4300
Text Label 7950 4300 0    45   ~ 0
VBUS_DIV_MID
Wire Wire Line
	8900 4300 9250 4300
Text Label 9250 4300 0    45   ~ 0
VBUS_ADC
Wire Wire Line
	9300 4300 8950 4300
Text Label 8950 4300 0    45   ~ 0
VBUS_ADC
Wire Wire Line
	9900 4300 10250 4300
Text Label 10250 4300 0    45   ~ 0
GND
Wire Wire Line
	10400 4500 10400 4150
Text Label 10400 4150 0    45   ~ 0
VBUS_ADC
Wire Wire Line
	10400 5000 10400 5350
Text Label 10400 5350 0    45   ~ 0
GND
Wire Wire Line
	10900 1900 10900 2250
Text Label 10900 2250 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	10900 3550 10900 3900
Text Label 10900 3900 0    45   ~ 0
GND
Wire Wire Line
	12100 1650 11650 1650
Text Label 11650 1650 0    45   ~ 0
VBUS_PROT
Wire Wire Line
	12100 4300 11650 4300
Text Label 11650 4300 0    45   ~ 0
VBUS_ADC
Wire Wire Line
	12100 3300 11650 3300
Text Label 11650 3300 0    45   ~ 0
GND
$EndSCHEMATC
