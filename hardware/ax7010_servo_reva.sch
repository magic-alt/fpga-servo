EESchema Schematic File Version 4
LIBS:ax7010_servo_reva
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
Sheet 1 1
Title "AX7010 Servo Drive Rev.A"
Date "2026-09-29"
Rev "A"
Comp "magic-alt/fpga-servo"
Comment1 "12-48V / 15A continuous target / 25A short peak"
Comment2 "Three phase 5mR shunts + INA241A2 + ADS8588S"
$EndDescr
Text Notes 700 650 0    80   ~ 16
DC LINK / AUX POWER
$Comp
L ax7010_servo_reva:TERM2 J3
U 1 1 65000001
P 1100 1350
F 0 "J3" H 1200 1450 50  0000 C CNN
F 1 "DC_IN_12_48V" H 1200 1250 50  0000 C CNN
	1    1100 1350
	1 0 0 -1
$EndComp
Text Label 700 1350 0    40   ~ 0
VBUS
Text Label 1500 1350 0    40   ~ 0
PGND
$Comp
L ax7010_servo_reva:LM5164 U12
U 1 1 65000002
P 2800 1350
F 0 "U12" H 2900 1450 50  0000 C CNN
F 1 "LM5164_48V_TO_12V" H 2900 1250 50  0000 C CNN
	1    2800 1350
	1 0 0 -1
$EndComp
Text Label 2000 1350 0    40   ~ 0
VBUS
Text Label 3600 1350 0    40   ~ 0
12V
Text Label 2800 2250 0    40   ~ 0
PGND
$Comp
L ax7010_servo_reva:POWER_BLOCK U13
U 1 1 65000003
P 4700 1350
F 0 "U13" H 4800 1450 50  0000 C CNN
F 1 "TPS62160_12V_TO_5V" H 4800 1250 50  0000 C CNN
	1    4700 1350
	1 0 0 -1
$EndComp
Text Label 4050 1350 0    40   ~ 0
12V
Text Label 5350 1350 0    40   ~ 0
5V
Text Label 4700 2200 0    40   ~ 0
GND
$Comp
L ax7010_servo_reva:POWER_BLOCK U14
U 1 1 65000004
P 6300 1350
F 0 "U14" H 6400 1450 50  0000 C CNN
F 1 "TLV75533_5V_TO_3V3" H 6400 1250 50  0000 C CNN
	1    6300 1350
	1 0 0 -1
$EndComp
Text Label 5650 1350 0    40   ~ 0
5V
Text Label 6950 1350 0    40   ~ 0
3V3_LOCAL
Text Label 6300 2200 0    40   ~ 0
GND
Text Notes 7400 1050 0    55   ~ 16
External upstream fuse required; TVS + bulk + film caps adjacent to bridge.
Text Notes 7400 1200 0    55   ~ 16
Do not back-power AX7010 5V/3V3 rails from this board.
Text Notes 700 2850 0    80   ~ 16
AX7010 PL INTERFACE (recent official docs J10/J11; neutral board names)
$Comp
L ax7010_servo_reva:HDR_2x20 J1
U 1 1 65000005
P 1500 4550
F 0 "J1" H 1600 4650 50  0000 C CNN
F 1 "AX7010_PL_A" H 1600 4450 50  0000 C CNN
	1    1500 4550
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:HDR_2x20 J2
U 1 1 65000006
P 4100 4550
F 0 "J2" H 4200 4650 50  0000 C CNN
F 1 "AX7010_PL_B" H 4200 4450 50  0000 C CNN
	1    4100 4550
	1 0 0 -1
$EndComp
Text Label 650 3200 0    40   ~ 0
PWM_UH
Text Label 2350 3315 0    40   ~ 0
PWM_UL
Text Label 650 3430 0    40   ~ 0
PWM_VH
Text Label 2350 3545 0    40   ~ 0
PWM_VL
Text Label 650 3660 0    40   ~ 0
PWM_WH
Text Label 2350 3775 0    40   ~ 0
PWM_WL
Text Label 650 3890 0    40   ~ 0
GATE_EN
Text Label 2350 4005 0    40   ~ 0
FAULT_CLEAR
Text Label 650 4120 0    40   ~ 0
ADC_CONVST
Text Label 2350 4235 0    40   ~ 0
ADC_SCLK
Text Label 650 4350 0    40   ~ 0
ADC_CS_N
Text Label 2350 4465 0    40   ~ 0
ADC_RESET
Text Label 650 4580 0    40   ~ 0
ADC_DOUTA
Text Label 2350 4695 0    40   ~ 0
ADC_DOUTB
Text Label 650 4810 0    40   ~ 0
ADC_BUSY
Text Label 2350 4925 0    40   ~ 0
ADC_FRSTDATA
Text Label 650 5040 0    40   ~ 0
ENC_A
Text Label 2350 5155 0    40   ~ 0
ENC_B
Text Label 650 5270 0    40   ~ 0
ENC_Z
Text Label 2350 5385 0    40   ~ 0
ENC_FAULT_N
Text Label 650 5500 0    40   ~ 0
OCP_N
Text Label 2350 5615 0    40   ~ 0
PWR_GOOD
Text Label 3250 3200 0    40   ~ 0
ADC_DB0
Text Label 4950 3315 0    40   ~ 0
ADC_DB1
Text Label 3250 3430 0    40   ~ 0
ADC_DB2
Text Label 4950 3545 0    40   ~ 0
ADC_DB3
Text Label 3250 3660 0    40   ~ 0
ADC_DB4
Text Label 4950 3775 0    40   ~ 0
ADC_DB5
Text Label 3250 3890 0    40   ~ 0
ADC_DB6
Text Label 4950 4005 0    40   ~ 0
ADC_DB7
Text Label 3250 4120 0    40   ~ 0
ADC_DB8
Text Label 4950 4235 0    40   ~ 0
ADC_DB9
Text Label 3250 4350 0    40   ~ 0
ADC_DB10
Text Label 4950 4465 0    40   ~ 0
ADC_DB11
Text Label 3250 4580 0    40   ~ 0
ADC_DB12
Text Label 4950 4695 0    40   ~ 0
ADC_DB13
Text Label 3250 4810 0    40   ~ 0
ADC_DB14
Text Label 4950 4925 0    40   ~ 0
ADC_DB15
Text Label 4950 5100 0    40   ~ 0
ADC_RD_N
Text Label 3250 5190 0    40   ~ 0
ADC_BYTE_SEL
Text Label 4950 5280 0    40   ~ 0
ADC_RANGE
Text Label 3250 5370 0    40   ~ 0
ADC_OS0
Text Label 4950 5460 0    40   ~ 0
ADC_OS1
Text Label 3250 5550 0    40   ~ 0
ADC_OS2
Text Label 4950 5640 0    40   ~ 0
ADC_STBY
Text Label 3250 5730 0    40   ~ 0
ADC_PAR_SER
Text Label 4950 5820 0    40   ~ 0
HALL_U
Text Label 3250 5910 0    40   ~ 0
HALL_V
Text Label 4950 6000 0    40   ~ 0
HALL_W
Text Label 3250 6090 0    40   ~ 0
BRAKE_OUT
Text Label 4950 6180 0    40   ~ 0
EXT_FAULT_N
Text Label 3250 6270 0    40   ~ 0
TEST_TRIG
Text Notes 6100 2850 0    80   ~ 16
PWM HARDWARE GATING + GATE DRIVER
$Comp
L ax7010_servo_reva:AND4 U10
U 1 1 65000007
P 6500 4050
F 0 "U10" H 6600 4150 50  0000 C CNN
F 1 "PWM_GATE_U" H 6600 3950 50  0000 C CNN
	1    6500 4050
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:AND4 U11
U 1 1 65000008
P 7900 4050
F 0 "U11" H 8000 4150 50  0000 C CNN
F 1 "PWM_GATE_VW" H 8000 3950 50  0000 C CNN
	1    7900 4050
	1 0 0 -1
$EndComp
Text Label 5900 3950 0    40   ~ 0
PWM_UH
Text Label 5900 4150 0    40   ~ 0
RUN_OK
Text Label 7100 4050 0    40   ~ 0
HIN_U_SAFE
$Comp
L ax7010_servo_reva:FD6288T U1
U 1 1 65000009
P 9800 4300
F 0 "U1" H 9900 4400 50  0000 C CNN
F 1 "FD6288T" H 9900 4200 50  0000 C CNN
	1    9800 4300
	1 0 0 -1
$EndComp
Text Label 8800 3650 0    40   ~ 0
HIN_U_SAFE
Text Label 8800 3850 0    40   ~ 0
HIN_V_SAFE
Text Label 8800 4050 0    40   ~ 0
HIN_W_SAFE
Text Label 8800 4250 0    40   ~ 0
LIN_U_SAFE
Text Label 8800 4450 0    40   ~ 0
LIN_V_SAFE
Text Label 8800 4650 0    40   ~ 0
LIN_W_SAFE
Text Label 9800 3100 0    40   ~ 0
12V
Text Label 9800 5500 0    40   ~ 0
PGND
Text Label 10800 3500 0    40   ~ 0
GL_W
Text Label 10800 3635 0    40   ~ 0
GL_V
Text Label 10800 3770 0    40   ~ 0
GL_U
Text Label 10800 3905 0    40   ~ 0
SW_W
Text Label 10800 4040 0    40   ~ 0
GH_W
Text Label 10800 4175 0    40   ~ 0
BST_W
Text Label 10800 4310 0    40   ~ 0
SW_V
Text Label 10800 4445 0    40   ~ 0
GH_V
Text Label 10800 4580 0    40   ~ 0
BST_V
Text Label 10800 4715 0    40   ~ 0
SW_U
Text Label 10800 4850 0    40   ~ 0
GH_U
Text Label 10800 4985 0    40   ~ 0
BST_U
Text Notes 6100 4950 0    55   ~ 16
RUN_OK = GATE_EN & PWR_GOOD & OCP_OK; all six PWM inputs forced low when false.
Text Notes 11200 650 0    80   ~ 16
THREE-PHASE 100V MOSFET BRIDGE / INLINE 5mR SHUNTS
$Comp
L ax7010_servo_reva:MOSFET_N Q1
U 1 1 6500000A
P 11700 1650
F 0 "Q1" H 11800 1750 50  0000 C CNN
F 1 "BSC040N10NS5_HS" H 11800 1550 50  0000 C CNN
	1    11700 1650
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:MOSFET_N Q2
U 1 1 6500000B
P 11700 2550
F 0 "Q2" H 11800 2650 50  0000 C CNN
F 1 "BSC040N10NS5_LS" H 11800 2450 50  0000 C CNN
	1    11700 2550
	1 0 0 -1
$EndComp
Text Label 11700 1000 0    40   ~ 0
VBUS
Text Label 10900 1650 0    40   ~ 0
GH_U
Text Label 10900 2550 0    40   ~ 0
GL_U
Text Label 11700 2100 0    40   ~ 0
SW_U
Text Label 11700 3200 0    40   ~ 0
PGND
$Comp
L ax7010_servo_reva:SHUNT_5mR RSHU
U 1 1 6500000C
P 13500 2100
F 0 "RSHU" H 13600 2200 50  0000 C CNN
F 1 "5mR_KELVIN_5W" H 13600 2000 50  0000 C CNN
	1    13500 2100
	1 0 0 -1
$EndComp
Text Label 12900 2100 0    40   ~ 0
SW_U
Text Label 14100 2100 0    40   ~ 0
PH_U
Text Label 13500 1400 0    40   ~ 0
U_SH_P
Text Label 13500 2800 0    40   ~ 0
U_SH_N
$Comp
L ax7010_servo_reva:MOSFET_N Q3
U 1 1 6500000D
P 11700 3450
F 0 "Q3" H 11800 3550 50  0000 C CNN
F 1 "BSC040N10NS5_HS" H 11800 3350 50  0000 C CNN
	1    11700 3450
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:MOSFET_N Q4
U 1 1 6500000E
P 11700 4350
F 0 "Q4" H 11800 4450 50  0000 C CNN
F 1 "BSC040N10NS5_LS" H 11800 4250 50  0000 C CNN
	1    11700 4350
	1 0 0 -1
$EndComp
Text Label 11700 2800 0    40   ~ 0
VBUS
Text Label 10900 3450 0    40   ~ 0
GH_V
Text Label 10900 4350 0    40   ~ 0
GL_V
Text Label 11700 3900 0    40   ~ 0
SW_V
Text Label 11700 5000 0    40   ~ 0
PGND
$Comp
L ax7010_servo_reva:SHUNT_5mR RSHV
U 1 1 6500000F
P 13500 3900
F 0 "RSHV" H 13600 4000 50  0000 C CNN
F 1 "5mR_KELVIN_5W" H 13600 3800 50  0000 C CNN
	1    13500 3900
	1 0 0 -1
$EndComp
Text Label 12900 3900 0    40   ~ 0
SW_V
Text Label 14100 3900 0    40   ~ 0
PH_V
Text Label 13500 3200 0    40   ~ 0
V_SH_P
Text Label 13500 4600 0    40   ~ 0
V_SH_N
$Comp
L ax7010_servo_reva:MOSFET_N Q5
U 1 1 65000010
P 11700 5250
F 0 "Q5" H 11800 5350 50  0000 C CNN
F 1 "BSC040N10NS5_HS" H 11800 5150 50  0000 C CNN
	1    11700 5250
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:MOSFET_N Q6
U 1 1 65000011
P 11700 6150
F 0 "Q6" H 11800 6250 50  0000 C CNN
F 1 "BSC040N10NS5_LS" H 11800 6050 50  0000 C CNN
	1    11700 6150
	1 0 0 -1
$EndComp
Text Label 11700 4600 0    40   ~ 0
VBUS
Text Label 10900 5250 0    40   ~ 0
GH_W
Text Label 10900 6150 0    40   ~ 0
GL_W
Text Label 11700 5700 0    40   ~ 0
SW_W
Text Label 11700 6800 0    40   ~ 0
PGND
$Comp
L ax7010_servo_reva:SHUNT_5mR RSHW
U 1 1 65000012
P 13500 5700
F 0 "RSHW" H 13600 5800 50  0000 C CNN
F 1 "5mR_KELVIN_5W" H 13600 5600 50  0000 C CNN
	1    13500 5700
	1 0 0 -1
$EndComp
Text Label 12900 5700 0    40   ~ 0
SW_W
Text Label 14100 5700 0    40   ~ 0
PH_W
Text Label 13500 5000 0    40   ~ 0
W_SH_P
Text Label 13500 6400 0    40   ~ 0
W_SH_N
$Comp
L ax7010_servo_reva:TERM3 J4
U 1 1 65000013
P 15100 3900
F 0 "J4" H 15200 4000 50  0000 C CNN
F 1 "MOTOR_UVW" H 15200 3800 50  0000 C CNN
	1    15100 3900
	1 0 0 -1
$EndComp
Text Label 14600 3700 0    40   ~ 0
PH_U
Text Label 14600 3900 0    40   ~ 0
PH_V
Text Label 14600 4100 0    40   ~ 0
PH_W
Text Notes 11100 6550 0    55   ~ 16
Kelvin-sense each 5mR shunt independently; keep switch loops compact.
Text Notes 6000 6750 0    80   ~ 16
CURRENT SENSE / SIMULTANEOUS ADC
$Comp
L ax7010_servo_reva:INA241A2 U2
U 1 1 65000014
P 6800 7900
F 0 "U2" H 6900 8000 50  0000 C CNN
F 1 "INA241A2_U" H 6900 7800 50  0000 C CNN
	1    6800 7900
	1 0 0 -1
$EndComp
Text Label 6000 7700 0    40   ~ 0
U_SH_P
Text Label 6000 8050 0    40   ~ 0
U_SH_N
Text Label 7600 7900 0    40   ~ 0
IU_ADC
Text Label 6800 7000 0    40   ~ 0
5V
Text Label 6800 8800 0    40   ~ 0
GND
$Comp
L ax7010_servo_reva:INA241A2 U3
U 1 1 65000015
P 8300 7900
F 0 "U3" H 8400 8000 50  0000 C CNN
F 1 "INA241A2_V" H 8400 7800 50  0000 C CNN
	1    8300 7900
	1 0 0 -1
$EndComp
Text Label 7500 7700 0    40   ~ 0
V_SH_P
Text Label 7500 8050 0    40   ~ 0
V_SH_N
Text Label 9100 7900 0    40   ~ 0
IV_ADC
Text Label 8300 7000 0    40   ~ 0
5V
Text Label 8300 8800 0    40   ~ 0
GND
$Comp
L ax7010_servo_reva:INA241A2 U4
U 1 1 65000016
P 9800 7900
F 0 "U4" H 9900 8000 50  0000 C CNN
F 1 "INA241A2_W" H 9900 7800 50  0000 C CNN
	1    9800 7900
	1 0 0 -1
$EndComp
Text Label 9000 7700 0    40   ~ 0
W_SH_P
Text Label 9000 8050 0    40   ~ 0
W_SH_N
Text Label 10600 7900 0    40   ~ 0
IW_ADC
Text Label 9800 7000 0    40   ~ 0
5V
Text Label 9800 8800 0    40   ~ 0
GND
$Comp
L ax7010_servo_reva:ADS8588S U6
U 1 1 65000017
P 12200 8200
F 0 "U6" H 12300 8300 50  0000 C CNN
F 1 "ADS8588S" H 12300 8100 50  0000 C CNN
	1    12200 8200
	1 0 0 -1
$EndComp
Text Label 11000 7250 0    40   ~ 0
IU_ADC
Text Label 11000 7440 0    40   ~ 0
IV_ADC
Text Label 11000 7630 0    40   ~ 0
IW_ADC
Text Label 11000 7820 0    40   ~ 0
VBUS_ADC
Text Label 11000 8010 0    40   ~ 0
NTC_BOARD
Text Label 11000 8200 0    40   ~ 0
NTC_MOTOR
Text Label 11000 8390 0    40   ~ 0
AIN_SPARE0
Text Label 11000 8580 0    40   ~ 0
AIN_SPARE1
Text Label 13500 7200 0    40   ~ 0
ADC_BUSY
Text Label 13500 7300 0    40   ~ 0
ADC_FRSTDATA
Text Label 13500 7400 0    40   ~ 0
ADC_DOUTA
Text Label 13500 7500 0    40   ~ 0
ADC_DOUTB
Text Label 13500 7600 0    40   ~ 0
ADC_DB0
Text Label 13500 7700 0    40   ~ 0
ADC_DB1
Text Label 13500 7800 0    40   ~ 0
ADC_DB2
Text Label 13500 7900 0    40   ~ 0
ADC_DB3
Text Label 13500 8000 0    40   ~ 0
ADC_DB4
Text Label 13500 8100 0    40   ~ 0
ADC_DB5
Text Label 13500 8200 0    40   ~ 0
ADC_DB6
Text Label 13500 8300 0    40   ~ 0
ADC_DB7
Text Label 13500 8400 0    40   ~ 0
ADC_DB8
Text Label 13500 8500 0    40   ~ 0
ADC_DB9
Text Label 13500 8600 0    40   ~ 0
ADC_DB10
Text Label 13500 8700 0    40   ~ 0
ADC_DB11
Text Label 13500 8800 0    40   ~ 0
ADC_DB12
Text Label 13500 8900 0    40   ~ 0
ADC_DB13
Text Label 13500 9000 0    40   ~ 0
ADC_DB14
Text Label 13500 9100 0    40   ~ 0
ADC_DB15
Text Label 11500 9500 0    40   ~ 0
ADC_CONVST
Text Label 11700 9500 0    40   ~ 0
ADC_SCLK
Text Label 11900 9500 0    40   ~ 0
ADC_CS_N
Text Label 12100 9500 0    40   ~ 0
ADC_RESET
Text Label 12300 9500 0    40   ~ 0
ADC_RANGE
Text Label 12500 9500 0    40   ~ 0
ADC_PAR_SER
Text Notes 6000 9100 0    55   ~ 16
INA241A2 gain=20, 5mR => 0.1V/A; REF1=5V, REF2=GND => ~2.5V at zero current.
Text Notes 700 7200 0    80   ~ 16
DIFFERENTIAL ABZ ENCODER / HARDWARE OCP
$Comp
L ax7010_servo_reva:ENCODER_DIFF J5
U 1 1 65000018
P 1400 8200
F 0 "J5" H 1500 8300 50  0000 C CNN
F 1 "ABZ_DIFF_ENCODER" H 1500 8100 50  0000 C CNN
	1    1400 8200
	1 0 0 -1
$EndComp
$Comp
L ax7010_servo_reva:AM26LV32E U7
U 1 1 65000019
P 3700 8200
F 0 "U7" H 3800 8300 50  0000 C CNN
F 1 "AM26LV32E" H 3800 8100 50  0000 C CNN
	1    3700 8200
	1 0 0 -1
$EndComp
Text Label 2300 7600 0    40   ~ 0
ENC_A_P
Text Label 2300 7780 0    40   ~ 0
ENC_A_N
Text Label 2300 7960 0    40   ~ 0
ENC_B_P
Text Label 2300 8140 0    40   ~ 0
ENC_B_N
Text Label 2300 8320 0    40   ~ 0
ENC_Z_P
Text Label 2300 8500 0    40   ~ 0
ENC_Z_N
Text Label 4600 7800 0    40   ~ 0
ENC_A
Text Label 4600 8100 0    40   ~ 0
ENC_B
Text Label 4600 8400 0    40   ~ 0
ENC_Z
Text Label 3700 7000 0    40   ~ 0
3V3_LOCAL
Text Label 3700 9300 0    40   ~ 0
GND
$Comp
L ax7010_servo_reva:COMP_WINDOW U15
U 1 1 6500001A
P 5100 10000
F 0 "U15" H 5200 10100 50  0000 C CNN
F 1 "OCP_WINDOW" H 5200 9900 50  0000 C CNN
	1    5100 10000
	1 0 0 -1
$EndComp
Text Label 4400 9600 0    40   ~ 0
IU_ADC
Text Label 4400 9800 0    40   ~ 0
IV_ADC
Text Label 4400 10000 0    40   ~ 0
IW_ADC
Text Label 5800 10000 0    40   ~ 0
OCP_N
Text Notes 700 9400 0    55   ~ 16
ABZ inputs use selectable 120R line termination; encoder +5V is fused/protected.
Text Notes 7500 10400 0    60   ~ 16
FAB GATE: exact AX7010 revision, vendor footprints, ERC/DRC, gate ringing, OCP, thermal and backfeed tests.
$EndSCHEMATC
