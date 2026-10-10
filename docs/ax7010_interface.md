# AX7010 interface allocation

## Confirmed hardware baseline (2026-10-09)

User confirms ALINX AX7010 **2022** hardware and **J10** for the active serial interface (servo J1). Manufacturer V2.0 schematic file, sheets 5/15, was cross-checked visually: J10 pin1/37/38 = GND, pin2 = 5V (NC here), pin39/40 = 3.3V. All 34 signal-pin package mappings in the table below agree with that drawing. The supplied drawing title block is dated 2018; the user's 2022 identity is not a claim that this public PDF is a 2022 release. Physical continuity and bank-voltage verification remain acceptance tests.

Source: [ALINX official hardware schematic folder](https://github.com/alinxalinx/AX7010_2023.1/tree/master/Hardware/01_SCH). Local source PDF/hash and reviewed pages: `artifacts/schematic_opt_2022/`.

Unused servo connector J2 has been removed from the schematic and PCB. J1/J10 physical pin assignments and XDC are unchanged.

## Connector naming

Recent ALINX AX7010 documentation calls the two 40-pin PL expansion connectors **J10** and **J11**. The servo board uses `AX7010_PL_A` (J1) for J10. There is no J2/PL_B connector in this revision.

The servo PCB is designed for **cabled 2x20 2.54 mm connections** in Rev.A. This avoids assuming the exact board-to-board connector spacing of every AX7010 revision. A later mezzanine mechanical variant can reuse the same electrical mapping.

## PL_A / official J10 mapping

| Header pin | Servo signal | Zynq package pin |
|---:|---|---|
| 1 | GND | - |
| 2 | +5V from AX7010 - NC by default | - |
| 3 | PWM_UH | W19 |
| 4 | PWM_UL | W18 |
| 5 | PWM_VH | R14 |
| 6 | PWM_VL | P14 |
| 7 | PWM_WH | Y17 |
| 8 | PWM_WL | Y16 |
| 9 | GATE_EN | W15 |
| 10 | FAULT_CLEAR | V15 |
| 11 | ADC_CONVST | Y14 |
| 12 | ADC_SCLK | W14 |
| 13 | ADC_CS_N | P18 |
| 14 | ADC_RESET | N17 |
| 15 | ADC_DOUTA | U15 |
| 16 | ADC_DOUTB | U14 |
| 17 | ADC_BUSY | P16 |
| 18 | ADC_FRSTDATA | P15 |
| 19 | ENC_A | U17 |
| 20 | ENC_B | T16 |
| 21 | ENC_Z | V18 |
| 22 | ENC_FAULT_N | V17 |
| 23 | OCP_N | T15 |
| 24 | PWR_GOOD | T14 |
| 25 | AUX_IN0 | V13 |
| 26 | AUX_IN1 | U13 |
| 27 | AUX_OUT0 | W13 |
| 28 | AUX_OUT1 | V12 |
| 29 | SPARE_A0 | U12 |
| 30 | SPARE_A1 | T12 |
| 31 | SPARE_A2 | T10 |
| 32 | SPARE_A3 | T11 |
| 33 | SPARE_A4 | A20 |
| 34 | SPARE_A5 | B19 |
| 35 | SPARE_A6 | B20 |
| 36 | SPARE_A7 | C20 |
| 37 | GND | - |
| 38 | GND | - |
| 39 | VIO_FPGA_3V3 | - |
| 40 | VIO_FPGA_3V3 | - |

## Historical PL_B / official J11 allocation (not fitted)

The table below is historical reference only. J2 and its NoConn markers were deleted; none of this allocation is implemented.

| Header pin | Servo signal | Zynq package pin |
|---:|---|---|
| 1 | GND | - |
| 2 | +5V from AX7010 - NC by default | - |
| 3..18 | ADC_DB0..ADC_DB15 | F17,F16,F20,F19,G20,G19,H18,J18,L20,L19,M20,M19,K18,K17,J19,K19 |
| 19 | ADC_RD_N | H20 |
| 20 | ADC_BYTE_SEL | J20 |
| 21 | ADC_RANGE | L17 |
| 22 | ADC_OS0 | L16 |
| 23 | ADC_OS1 | M18 |
| 24 | ADC_OS2 | M17 |
| 25 | ADC_STBY | D20 |
| 26 | ADC_PAR_SER | D19 |
| 27 | HALL_U | E19 |
| 28 | HALL_V | E18 |
| 29 | HALL_W | G18 |
| 30 | BRAKE_OUT | G17 |
| 31 | EXT_FAULT_N | H17 |
| 32 | TEST_TRIG | H16 |
| 33 | SPARE_B0 | G15 |
| 34 | SPARE_B1 | H15 |
| 35 | SPARE_B2 | J14 |
| 36 | SPARE_B3 | K14 |
| 37 | GND | - |
| 38 | GND | - |
| 39 | VIO_FPGA_3V3 | - |
| 40 | VIO_FPGA_3V3 | - |

## Electrical rules

- All PL signals are 3.3 V LVCMOS.
- AX7010 +5 V pins are **not** tied to the servo board 5 V rail by default.
- `VIO_FPGA_3V3` (schematic name `VIO_3V3`) powers U8..U11 safety logic, U7 receiver and U6 DVDD. There is no local 3.3 V LDO.
- PWM outputs pass through U8..U10 hardware AND gating before non-inverting DRV8300DPWR; U11 generates RUN_OK. R80..R86 pull raw PWM/GATE_EN low while FPGA pins are high impedance.
- ADC/encoder outputs connect directly to the FPGA; no standalone buffer array is fitted. Power sequencing and partial-power injection must be verified.
- J1 pin 10 FAULT_CLEAR drives the U20 hardware ARM latch through R87/R88/C92 and U21. Re-arm with GATE_EN low and healthy conditions, CLEAR high/low >=10us, then wait >=10us before enabling; see `ocp_latch_review_2026-10-09.md`. J1 pin 22 and spare/auxiliary pins in the allocation table are NoConn in this revision.

## VA5 supervision update (2026-10-10)

VA_5V is nominally 5.1V after the ADC-validity repair. J1 pin assignments and XDC are unchanged. U25 independently senses VA5 and clears ARMED on undervoltage; FAULT_CLEAR still requires GATE_EN low and healthy supplies. Recovery cannot restart PWM automatically. Encoder supply via F2 shares VA5: qualify the actual encoder voltage range, cable drop and faults. See [repair evidence and acceptance limits](adc_undervoltage_repair_2026-10-10.md).

## Selection update (2026-10-10)

J1 uses JILN 321040SG0ABK00A01 (C601944); J5 uses JILN 321010SG0ABK00A01 (C429962). Local lands retain the original pin map and key orientation; finished plated holes require 1.02 ±0.03 mm. BOOMELE alternatives are conditional on manufacturer confirmation and <=1 A per pin; they are not 3 A substitutes.

J1.23 OCP_N now reports only positive bus overcurrent, nominal +25 A. Phase INA240 measurements remain available through the ADC. The hardware latch/FAULT_CLEAR protocol is unchanged. No reverse-current trip is implemented. F2 uses JDT ASMD1812-050; 0.5 A hold rating is at 25°C, 0.45 A at 40°C, and local ambient must remain <=85°C. Verify encoder running/startup current against the derated limit.
