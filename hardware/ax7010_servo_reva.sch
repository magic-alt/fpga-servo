EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "AX7010 Servo Drive Rev.A1 - System"
Date "2026-09-29"
Rev "A1"
Comp "magic-alt/fpga-servo"
Comment1 "48V nominal; 15..55V full-function; A4 hierarchical engineering schematic"
$EndDescr
Text Notes 650 450 0    70   ~ 12
SYSTEM ARCHITECTURE - POWER FLOW / SAFETY FLOW / REAL-TIME I/O
$Sheet
S 700 1100 2100 1400
U 69000001
F0 "DC Input & Protection" 50
F1 "power_input.sch" 50
F2 "VBUS_PROT" O R 2800 1500 50
F3 "VBUS_ADC" O R 2800 1850 50
F4 "GND" B R 2800 2200 50
$EndSheet
$Sheet
S 3400 1100 2200 1400
U 69000002
F0 "Auxiliary Power" 50
F1 "aux_power.sch" 50
F2 "VBUS_PROT" I L 3400 1500 50
F3 "GND" B L 3400 2200 50
F4 "VDRV_12V" O R 5600 1450 50
F5 "VA_5V" O R 5600 1800 50
F6 "PWR_GOOD" O R 5600 2150 50
$EndSheet
$Sheet
S 6600 850 4200 2700
U 69000003
F0 "Gate Driver / Inverter" 50
F1 "gate_inverter.sch" 50
F2 "VBUS_PROT" I L 6600 1100 50
F3 "VDRV_12V" I L 6600 1300 50
F4 "VIO_3V3" I L 6600 1500 50
F5 "PWR_GOOD" I L 6600 1700 50
F6 "OCP_N" I L 6600 1900 50
F7 "GATE_EN" I L 6600 2100 50
F8 "PWM_UH" I L 6600 2300 50
F9 "PWM_UL" I L 6600 2450 50
F10 "PWM_VH" I L 6600 2600 50
F11 "PWM_VL" I L 6600 2750 50
F12 "PWM_WH" I L 6600 2900 50
F13 "PWM_WL" I L 6600 3050 50
F14 "GND" B L 6600 3300 50
F15 "SW_U" O R 10800 1300 50
F16 "PH_U" O R 10800 1500 50
F17 "SW_V" O R 10800 1900 50
F18 "PH_V" O R 10800 2100 50
F19 "SW_W" O R 10800 2500 50
F20 "PH_W" O R 10800 2700 50
$EndSheet
$Sheet
S 700 3850 2500 3000
U 69000004
F0 "AX7010 PL Interface" 50
F1 "ax7010_interface.sch" 50
F2 "VIO_3V3" O R 3200 4050 50
F3 "PWM_UH" O R 3200 4200 50
F4 "PWM_UL" O R 3200 4350 50
F5 "PWM_VH" O R 3200 4500 50
F6 "PWM_VL" O R 3200 4650 50
F7 "PWM_WH" O R 3200 4800 50
F8 "PWM_WL" O R 3200 4950 50
F9 "GATE_EN" O R 3200 5100 50
F10 "FAULT_CLEAR" O R 3200 5250 50
F11 "ADC_CONVST" O R 3200 5450 50
F12 "ADC_SCLK" O R 3200 5600 50
F13 "ADC_CS_N" O R 3200 5750 50
F14 "ADC_RESET" O R 3200 5900 50
F15 "ADC_DOUTA" I R 3200 6100 50
F16 "ADC_DOUTB" I R 3200 6250 50
F17 "ADC_BUSY" I R 3200 6400 50
F18 "ADC_FRSTDATA" I R 3200 6550 50
F19 "ENC_A" I R 3200 6700 50
F20 "ENC_B" I R 3200 6850 50
F21 "ENC_Z" I R 3200 7000 50
F22 "OCP_N" I R 3200 7150 50
F23 "PWR_GOOD" I R 3200 7300 50
F24 "GND" B R 3200 7450 50
$EndSheet
$Sheet
S 4000 3900 3000 2850
U 69000005
F0 "Current Sense / OCP / ADC" 50
F1 "current_adc.sch" 50
F2 "VIO_3V3" I L 4000 4100 50
F3 "VA_5V" I L 4000 4300 50
F4 "GND" B L 4000 4500 50
F5 "VBUS_ADC" I L 4000 4700 50
F6 "ADC_CONVST" I L 4000 4900 50
F7 "ADC_SCLK" I L 4000 5050 50
F8 "ADC_CS_N" I L 4000 5200 50
F9 "ADC_RESET" I L 4000 5350 50
F10 "ADC_DOUTA" O L 4000 5600 50
F11 "ADC_DOUTB" O L 4000 5750 50
F12 "ADC_BUSY" O L 4000 5900 50
F13 "ADC_FRSTDATA" O L 4000 6050 50
F14 "OCP_N" O L 4000 6250 50
F15 "SW_U" I R 7000 4300 50
F16 "PH_U" I R 7000 4500 50
F17 "SW_V" I R 7000 4900 50
F18 "PH_V" I R 7000 5100 50
F19 "SW_W" I R 7000 5500 50
F20 "PH_W" I R 7000 5700 50
$EndSheet
$Sheet
S 8100 4300 2500 1650
U 69000006
F0 "Differential ABZ Encoder" 50
F1 "encoder.sch" 50
F2 "VA_5V" I L 8100 4550 50
F3 "VIO_3V3" I L 8100 4800 50
F4 "GND" B L 8100 5200 50
F5 "ENC_A" O R 10600 4600 50
F6 "ENC_B" O R 10600 4900 50
F7 "ENC_Z" O R 10600 5200 50
$EndSheet
Wire Wire Line
	2800 1500 3400 1500
Text Label 1500 NaNundefined
VBUS_PROT
Wire Wire Line
	5600 1450 6600 1300
Text Label 1450 NaNundefined
VDRV_12V
Wire Wire Line
	2800 1850 3000 1850
Text Label 1850 NaNundefined
VBUS_ADC
Wire Wire Line
	2800 2200 3000 2200
Text Label 2200 NaNundefined
GND
Wire Wire Line
	3400 2200 3200 2200
Text Label 2200 NaNundefined
GND
Wire Wire Line
	5600 1800 5800 1800
Text Label 1800 NaNundefined
VA_5V
Wire Wire Line
	5600 2150 5800 2150
Text Label 2150 NaNundefined
PWR_GOOD
Wire Wire Line
	3200 4050 3400 4050
Text Label 4050 NaNundefined
VIO_3V3
Wire Wire Line
	3200 4200 3400 4200
Text Label 4200 NaNundefined
PWM_UH
Wire Wire Line
	3200 4350 3400 4350
Text Label 4350 NaNundefined
PWM_UL
Wire Wire Line
	3200 4500 3400 4500
Text Label 4500 NaNundefined
PWM_VH
Wire Wire Line
	3200 4650 3400 4650
Text Label 4650 NaNundefined
PWM_VL
Wire Wire Line
	3200 4800 3400 4800
Text Label 4800 NaNundefined
PWM_WH
Wire Wire Line
	3200 4950 3400 4950
Text Label 4950 NaNundefined
PWM_WL
Wire Wire Line
	3200 5100 3400 5100
Text Label 5100 NaNundefined
GATE_EN
Wire Wire Line
	3200 5450 3400 5450
Text Label 5450 NaNundefined
ADC_CONVST
Wire Wire Line
	3200 5600 3400 5600
Text Label 5600 NaNundefined
ADC_SCLK
Wire Wire Line
	3200 5750 3400 5750
Text Label 5750 NaNundefined
ADC_CS_N
Wire Wire Line
	3200 5900 3400 5900
Text Label 5900 NaNundefined
ADC_RESET
Wire Wire Line
	3200 6100 3400 6100
Text Label 6100 NaNundefined
ADC_DOUTA
Wire Wire Line
	3200 6250 3400 6250
Text Label 6250 NaNundefined
ADC_DOUTB
Wire Wire Line
	3200 6400 3400 6400
Text Label 6400 NaNundefined
ADC_BUSY
Wire Wire Line
	3200 6550 3400 6550
Text Label 6550 NaNundefined
ADC_FRSTDATA
Wire Wire Line
	3200 6700 3400 6700
Text Label 6700 NaNundefined
ENC_A
Wire Wire Line
	3200 6850 3400 6850
Text Label 6850 NaNundefined
ENC_B
Wire Wire Line
	3200 7000 3400 7000
Text Label 7000 NaNundefined
ENC_Z
Wire Wire Line
	3200 7150 3400 7150
Text Label 7150 NaNundefined
OCP_N
Wire Wire Line
	3200 7300 3400 7300
Text Label 7300 NaNundefined
PWR_GOOD
Wire Wire Line
	3200 7450 3400 7450
Text Label 7450 NaNundefined
GND
NoConn ~ 3200 5250
Wire Wire Line
	4000 4100 3800 4100
Text Label 4100 NaNundefined
VIO_3V3
Wire Wire Line
	4000 4300 3800 4300
Text Label 4300 NaNundefined
VA_5V
Wire Wire Line
	4000 4500 3800 4500
Text Label 4500 NaNundefined
GND
Wire Wire Line
	4000 4700 3800 4700
Text Label 4700 NaNundefined
VBUS_ADC
Wire Wire Line
	4000 4900 3800 4900
Text Label 4900 NaNundefined
ADC_CONVST
Wire Wire Line
	4000 5050 3800 5050
Text Label 5050 NaNundefined
ADC_SCLK
Wire Wire Line
	4000 5200 3800 5200
Text Label 5200 NaNundefined
ADC_CS_N
Wire Wire Line
	4000 5350 3800 5350
Text Label 5350 NaNundefined
ADC_RESET
Wire Wire Line
	4000 5600 3800 5600
Text Label 5600 NaNundefined
ADC_DOUTA
Wire Wire Line
	4000 5750 3800 5750
Text Label 5750 NaNundefined
ADC_DOUTB
Wire Wire Line
	4000 5900 3800 5900
Text Label 5900 NaNundefined
ADC_BUSY
Wire Wire Line
	4000 6050 3800 6050
Text Label 6050 NaNundefined
ADC_FRSTDATA
Wire Wire Line
	4000 6250 3800 6250
Text Label 6250 NaNundefined
OCP_N
Wire Wire Line
	7000 4300 7200 4300
Text Label 4300 NaNundefined
SW_U
Wire Wire Line
	7000 4500 7200 4500
Text Label 4500 NaNundefined
PH_U
Wire Wire Line
	7000 4900 7200 4900
Text Label 4900 NaNundefined
SW_V
Wire Wire Line
	7000 5100 7200 5100
Text Label 5100 NaNundefined
PH_V
Wire Wire Line
	7000 5500 7200 5500
Text Label 5500 NaNundefined
SW_W
Wire Wire Line
	7000 5700 7200 5700
Text Label 5700 NaNundefined
PH_W
Wire Wire Line
	6600 1100 6400 1100
Text Label 1100 NaNundefined
VBUS_PROT
Wire Wire Line
	6600 1500 6400 1500
Text Label 1500 NaNundefined
VIO_3V3
Wire Wire Line
	6600 1700 6400 1700
Text Label 1700 NaNundefined
PWR_GOOD
Wire Wire Line
	6600 1900 6400 1900
Text Label 1900 NaNundefined
OCP_N
Wire Wire Line
	6600 2100 6400 2100
Text Label 2100 NaNundefined
GATE_EN
Wire Wire Line
	6600 2300 6400 2300
Text Label 2300 NaNundefined
PWM_UH
Wire Wire Line
	6600 2450 6400 2450
Text Label 2450 NaNundefined
PWM_UL
Wire Wire Line
	6600 2600 6400 2600
Text Label 2600 NaNundefined
PWM_VH
Wire Wire Line
	6600 2750 6400 2750
Text Label 2750 NaNundefined
PWM_VL
Wire Wire Line
	6600 2900 6400 2900
Text Label 2900 NaNundefined
PWM_WH
Wire Wire Line
	6600 3050 6400 3050
Text Label 3050 NaNundefined
PWM_WL
Wire Wire Line
	6600 3300 6400 3300
Text Label 3300 NaNundefined
GND
Wire Wire Line
	10800 1300 11000 1300
Text Label 1300 NaNundefined
SW_U
Wire Wire Line
	10800 1500 11000 1500
Text Label 1500 NaNundefined
PH_U
Wire Wire Line
	10800 1900 11000 1900
Text Label 1900 NaNundefined
SW_V
Wire Wire Line
	10800 2100 11000 2100
Text Label 2100 NaNundefined
PH_V
Wire Wire Line
	10800 2500 11000 2500
Text Label 2500 NaNundefined
SW_W
Wire Wire Line
	10800 2700 11000 2700
Text Label 2700 NaNundefined
PH_W
Wire Wire Line
	8100 4550 7900 4550
Text Label 4550 NaNundefined
VA_5V
Wire Wire Line
	8100 4800 7900 4800
Text Label 4800 NaNundefined
VIO_3V3
Wire Wire Line
	8100 5200 7900 5200
Text Label 5200 NaNundefined
GND
Wire Wire Line
	10600 4600 10800 4600
Text Label 4600 NaNundefined
ENC_A
Wire Wire Line
	10600 4900 10800 4900
Text Label 4900 NaNundefined
ENC_B
Wire Wire Line
	10600 5200 10800 5200
Text Label 5200 NaNundefined
ENC_Z
Text Notes 650 7200 0    48   ~ 12
Major power rails are drawn directly; named stubs keep dense real-time and safety nets readable on A4.
Text Notes 650 7350 0    48   ~ 12
FAULT_CLEAR is reserved at the FPGA interface and intentionally NoConn in Rev.A1.
Text Notes 650 7500 0    48   ~ 12
One continuous GND reference is used; analog/power separation is enforced by placement and return-current geometry.
$EndSCHEMATC
