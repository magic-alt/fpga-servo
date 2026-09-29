EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "Rev.A1 - DC Input & Protection"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "48V-class bus; 15..55V design window; source transient qualification required"
$EndDescr
Text Notes 650 450 0    65   ~ 12
DC INPUT -> FUSE -> LM74502 + BACK-TO-BACK NFET RPP -> LOCAL DC-LINK
$Comp
L ax7010_servo_reva:TERM2 J3
U 1 1 66000001
P 950 1700
F 0 "J3" H 1050 1800 50  0000 C CNN
F 1 "DC_IN_48V" H 1050 1600 50  0000 C CNN
F 2 "TerminalBlock:TerminalBlock_bornier-2_P7.62mm" H 950 1700 50  0001 C CNN
	1    950 1700
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:FUSE F1
U 1 1 66000002
P 2100 1550
F 0 "F1" H 2200 1650 50  0000 C CNN
F 1 "EXT_FUSE_OR_25A_FUSE" H 2200 1450 50  0000 C CNN
F 2 "Fuse:Fuse_2920_7451Metric" H 2100 1550 50  0001 C CNN
	1    2100 1550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:NFET_HORIZ Q7
U 1 1 66000003
P 3600 1550
F 0 "Q7" H 3700 1650 50  0000 C CNN
F 1 "BSC040N10NS5_RPP_Q7" H 3700 1450 50  0000 C CNN
F 2 "Package_DFN_QFN:TDSON-8-1_5x6mm_P1.27mm" H 3600 1550 50  0001 C CNN
	1    3600 1550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:NFET_HORIZ_REV Q8
U 1 1 6ABAF000
P 4850 1550
F 0 "Q8" H 4950 1650 50  0000 C CNN
F 1 "BSC040N10NS5_RPP_Q8" H 4950 1450 50  0000 C CNN
F 2 "Package_DFN_QFN:TDSON-8-1_5x6mm_P1.27mm" H 4850 1550 50  0001 C CNN
	1    4850 1550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C19
U 1 1 6ABAF001
P 5200 3850
F 0 "C19" H 5300 3950 50  0000 C CNN
F 1 "100nF_VS_BYPASS" H 5300 3750 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 5200 3850 50  0001 C CNN
	1    5200 3850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:LM74502 U18
U 1 1 66000004
P 3500 3200
F 0 "U18" H 3600 3300 50  0000 C CNN
F 1 "LM74502DDFR" H 3600 3100 50  0000 C CNN
F 2 "Package_TO_SOT_SMD:SOT-23-8" H 3500 3200 50  0001 C CNN
	1    3500 3200
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C18
U 1 1 66000005
P 4550 3850
F 0 "C18" H 4650 3950 50  0000 C CNN
F 1 "220nF_25V_VCAP" H 4650 3750 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 4550 3850 50  0001 C CNN
	1    4550 3850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TVS D1
U 1 1 66000006
P 5750 2850
F 0 "D1" H 5850 2950 50  0000 C CNN
F 1 "SMCJ54A_DNP_VERIFY_CLAMP" H 5850 2750 50  0000 C CNN
F 2 "Diode_SMD:D_SMC" H 5750 2850 50  0001 C CNN
	1    5750 2850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C1
U 1 1 66000007
P 6600 2850
F 0 "C1" H 6700 2950 50  0000 C CNN
F 1 "100uF_100V" H 6700 2750 50  0000 C CNN
F 2 "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm" H 6600 2850 50  0001 C CNN
	1    6600 2850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C2
U 1 1 66000008
P 7250 2850
F 0 "C2" H 7350 2950 50  0000 C CNN
F 1 "100uF_100V" H 7350 2750 50  0000 C CNN
F 2 "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm" H 7250 2850 50  0001 C CNN
	1    7250 2850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C3
U 1 1 66000009
P 7900 2850
F 0 "C3" H 8000 2950 50  0000 C CNN
F 1 "1uF_100V_FILM" H 8000 2750 50  0000 C CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 7900 2850 50  0001 C CNN
	1    7900 2850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C4
U 1 1 6600000A
P 8550 2850
F 0 "C4" H 8650 2950 50  0000 C CNN
F 1 "100nF_100V_C0G" H 8650 2750 50  0000 C CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 8550 2850 50  0001 C CNN
	1    8550 2850
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R1
U 1 1 6600000B
P 6100 4550
F 0 "R1" H 6200 4650 50  0000 C CNN
F 1 "280k_0.1%" H 6200 4450 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 6100 4550 50  0001 C CNN
	1    6100 4550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R2
U 1 1 6600000C
P 7000 4550
F 0 "R2" H 7100 4650 50  0000 C CNN
F 1 "280k_0.1%" H 7100 4450 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 7000 4550 50  0001 C CNN
	1    7000 4550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:R R3
U 1 1 6600000D
P 7900 4550
F 0 "R3" H 8000 4650 50  0000 C CNN
F 1 "39k_0.1%" H 8000 4450 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 7900 4550 50  0001 C CNN
	1    7900 4550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:C C5
U 1 1 6600000E
P 8600 5050
F 0 "C5" H 8700 5150 50  0000 C CNN
F 1 "10nF_VBUS_SENSE" H 8700 4950 50  0000 C CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 8600 5050 50  0001 C CNN
	1    8600 5050
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TP TP1
U 1 1 6600000F
P 9600 1550
F 0 "TP1" H 9700 1650 50  0000 C CNN
F 1 "TP_VBUS_PROT" H 9700 1450 50  0000 C CNN
F 2 "TestPoint:TestPoint_Pad_D2.0mm" H 9600 1550 50  0001 C CNN
	1    9600 1550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:TP TP2
U 1 1 66000010
P 9600 3300
F 0 "TP2" H 9700 3400 50  0000 C CNN
F 1 "TP_GND" H 9700 3200 50  0000 C CNN
F 2 "TestPoint:TestPoint_Pad_D2.0mm" H 9600 3300 50  0001 C CNN
	1    9600 3300
	1 0 0 -1
$EndComp
Text HLabel 1550 NaNundefined
VBUS_PROT
Text HLabel 4550 NaNundefined
VBUS_ADC
Text HLabel 3300 NaNundefined
GND
Text Notes 600 5600 0    60   ~ 12
Q7/Q8 are back-to-back N-MOSFETs driven by LM74502 for low-loss reverse-polarity protection. The controller has no reverse-current blocking when enabled, so regeneration can return to a receptive source.
Text Notes 600 5770 0    60   ~ 12
LM74502 OV is tied low in Rev.A1; positive surge is NOT claimed as closed. The 48V source/cable transient must be measured and kept inside the controller/downstream qualification envelope.
Text Notes 600 5940 0    60   ~ 12
D1 remains a DNP TVS footprint until clamping voltage is selected from the actual source impedance. F1 is a local placeholder; upstream source-rated over-current protection is mandatory.
Text Notes 650 6500 0    50   ~ 12
VBUS_ADC divider = 280k + 280k over 39k, plus 10nF at the ADC node. Keep the high-side resistors split for voltage stress and route the sense return away from commutation current.
Text Notes 650 6660 0    50   ~ 12
VISIBLE WIRING: power input and protection pins use explicit wire stubs; unused pins are explicit NoConn.
Wire Wire Line
	400 1700 250 1700
Text Label 1700 NaNundefined
VIN_RAW
Wire Wire Line
	1500 1700 1650 1700
Text Label 1700 NaNundefined
GND
Wire Wire Line
	1800 1550 1650 1550
Text Label 1550 NaNundefined
VIN_RAW
Wire Wire Line
	2400 1550 2550 1550
Text Label 1550 NaNundefined
VIN_FUSED
Wire Wire Line
	3600 2100 3600 2250
Text Label 2250 NaNundefined
RPP_GATE
Wire Wire Line
	4200 1550 4350 1550
Text Label 1550 NaNundefined
RPP_SRC
Wire Wire Line
	3000 1550 2850 1550
Text Label 1550 NaNundefined
VIN_FUSED
Wire Wire Line
	4850 2100 4850 2250
Text Label 2250 NaNundefined
RPP_GATE
Wire Wire Line
	4250 1550 4100 1550
Text Label 1550 NaNundefined
RPP_SRC
Wire Wire Line
	5450 1550 5600 1550
Text Label 1550 NaNundefined
VBUS_PROT
Wire Wire Line
	5200 3600 5200 3450
Text Label 3450 NaNundefined
VIN_FUSED
Wire Wire Line
	5200 4100 5200 4250
Text Label 4250 NaNundefined
GND
Wire Wire Line
	2750 2900 2600 2900
Text Label 2900 NaNundefined
VIN_FUSED
Wire Wire Line
	3500 3900 3500 4050
Text Label 4050 NaNundefined
GND
NoConn ~ 2750 3500
Wire Wire Line
	4250 3450 4400 3450
Text Label 3450 NaNundefined
VCAP_RPP
Wire Wire Line
	4250 3300 4400 3300
Text Label 3300 NaNundefined
VIN_FUSED
Wire Wire Line
	4250 3100 4400 3100
Text Label 3100 NaNundefined
RPP_GATE
Wire Wire Line
	2750 3300 2600 3300
Text Label 3300 NaNundefined
GND
Wire Wire Line
	4250 2900 4400 2900
Text Label 2900 NaNundefined
RPP_SRC
Wire Wire Line
	4550 3600 4550 3450
Text Label 3450 NaNundefined
VCAP_RPP
Wire Wire Line
	4550 4100 4550 4250
Text Label 4250 NaNundefined
VIN_FUSED
Wire Wire Line
	5750 3150 5750 3300
Text Label 3300 NaNundefined
GND
Wire Wire Line
	5750 2550 5750 2400
Text Label 2400 NaNundefined
VBUS_PROT
Wire Wire Line
	6600 2600 6600 2450
Text Label 2450 NaNundefined
VBUS_PROT
Wire Wire Line
	6600 3100 6600 3250
Text Label 3250 NaNundefined
GND
Wire Wire Line
	7250 2600 7250 2450
Text Label 2450 NaNundefined
VBUS_PROT
Wire Wire Line
	7250 3100 7250 3250
Text Label 3250 NaNundefined
GND
Wire Wire Line
	7900 2600 7900 2450
Text Label 2450 NaNundefined
VBUS_PROT
Wire Wire Line
	7900 3100 7900 3250
Text Label 3250 NaNundefined
GND
Wire Wire Line
	8550 2600 8550 2450
Text Label 2450 NaNundefined
VBUS_PROT
Wire Wire Line
	8550 3100 8550 3250
Text Label 3250 NaNundefined
GND
Wire Wire Line
	5800 4550 5650 4550
Text Label 4550 NaNundefined
VBUS_PROT
Wire Wire Line
	6400 4550 6550 4550
Text Label 4550 NaNundefined
VBUS_DIV_MID
Wire Wire Line
	6700 4550 6550 4550
Text Label 4550 NaNundefined
VBUS_DIV_MID
Wire Wire Line
	7300 4550 7450 4550
Text Label 4550 NaNundefined
VBUS_ADC
Wire Wire Line
	7600 4550 7450 4550
Text Label 4550 NaNundefined
VBUS_ADC
Wire Wire Line
	8200 4550 8350 4550
Text Label 4550 NaNundefined
GND
Wire Wire Line
	8600 4800 8600 4650
Text Label 4650 NaNundefined
VBUS_ADC
Wire Wire Line
	8600 5300 8600 5450
Text Label 5450 NaNundefined
GND
Wire Wire Line
	9600 1800 9600 1950
Text Label 1950 NaNundefined
VBUS_PROT
Wire Wire Line
	9600 3550 9600 3700
Text Label 3700 NaNundefined
GND
Wire Wire Line
	10800 1550 10600 1550
Wire Wire Line
	10800 4550 10600 4550
Wire Wire Line
	10800 3300 10600 3300
$EndSCHEMATC
