# AX7010 interface allocation

## Connector naming

Recent ALINX AX7010 documentation calls the two 40-pin PL expansion connectors **J10** and **J11**. The servo board intentionally calls them `AX7010_PL_A` and `AX7010_PL_B` so that older AX7010 board revisions with different silk-reference designators are not confused with the electrical pinout.

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

## PL_B / official J11 mapping

The second connector exposes the optional ADC parallel bus and development/debug signals.

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
- `VIO_FPGA_3V3` only powers FPGA-facing buffers and is not the board's main 3.3 V supply.
- PWM/control outputs pass through local-input buffering and hardware run gating before FD6288.
- ADC/encoder/fault inputs to the FPGA pass through `VIO_FPGA`-powered buffers to reduce partial-power backfeeding.
