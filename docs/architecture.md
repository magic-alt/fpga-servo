# Rev.A architecture

## Design intent

This board is a lab/engineering servo-drive daughter board for the ALINX AX7010. It deliberately keeps the hard real-time PWM, ADC timing and encoder counting in the Zynq PL while leaving high-power switching, signal conditioning and encoder line reception on the daughter board.

## Electrical target

| Item | Rev.A target |
|---|---:|
| DC bus | 12-48 V nominal |
| Recommended continuous bus max | 55 V |
| MOSFET VDS | 100 V |
| PWM | 10-40 kHz, 20 kHz nominal |
| Continuous phase current | 15 A with validated airflow/copper |
| Short peak phase current | 25 A, <=5 s target |
| Current shunt | 5 mOhm, >=5 W, Kelvin |
| Current gain | 20 V/V |
| Current transfer | 0.1 V/A |
| Current output zero | 2.5 V |
| ADC | 8 ch, simultaneous, 16 bit, 200 kSPS/ch |
| Encoder | differential A+/A-, B+/B-, Z+/Z- |
| Logic | 3.3 V |
| PCB | 2 layer, 1.6 mm, 2 oz recommended |

## Functional blocks

1. **DC-link / protection**
   - external upstream F1: Littelfuse KLKD025.T 25A / 600VDC in LPSM0001Z holder, near source positive; J3 is the fused board input; F1/J6 are system wiring, excluded from PCB
   - confirm actual bus-current/inrush, cable and fault-energy coordination before higher-power operation
   - input TVS and bulk capacitance close to bridge
   - bus-voltage divider to ADC

2. **Three-phase inverter**
   - six BSC040N10NS5 100 V MOSFETs
   - FD6288T TSSOP20 driver
   - per-gate series resistor and gate-source pulldown
   - bootstrap diode/capacitor for each high-side channel

3. **Phase-current measurement**
   - one 5 mOhm four-terminal shunt in each motor phase
   - INA241A2 high-side/bidirectional amplifier per phase
   - REF1=5 V, REF2=GND -> 2.5 V zero-current output
   - Kelvin sense traces, no load current in sense copper

4. **Data acquisition**
   - ADS8588S, 8 simultaneous channels
   - CH1/2/3: IU/IV/IW
   - CH4: VBUS
   - CH5: MOSFET-board NTC
   - CH6: motor/connector NTC
   - CH7/8: spare analog inputs
   - serial interface is the default FPGA interface; the second AX7010 connector exposes parallel data as an optional development path

5. **Encoder**
   - AM26LV32E quad RS-422 receiver at 3.3 V
   - 120 ohm termination footprints on A/B/Z, default fitted only when board is the line end
   - connector provides protected 5 V encoder power

6. **Auxiliary power**
   - LM5164: DC bus -> 12 V gate/aux rail
   - TPS62160-class 12 V -> 5 V rail
   - 3.3 V logic is supplied by AX7010 VIO; there is no local 3.3 V LDO in the current schematic
   - safety AND gates and encoder receiver run from AX7010 `VIO_3V3`; ADC DVDD also uses this rail
   - dedicated digital isolation/buffer arrays are not fitted; partial-power behavior remains a qualification gate

## Safety state

FD6288 has no single global hardware enable pin, so all six PWM inputs are hardware-gated before the driver. `RUN_OK` is defined as the logical AND of FPGA enable, auxiliary-power-good and the hardware ARMED latch. Any missing condition forces all six FD6288 input commands low.

Hardware over-current detection is based on the conditioned current-sense outputs and a window-comparator network. The FPGA fault path remains a second, independent diagnostic path.

The INA241A2 references use `REF1=VA_5V` and `REF2=GND`, placing zero current near 2.5 V. The 5 mOhm shunt and 20 V/V gain give 0.1 V/A. ADS8588S straps are `OS=000`, `PAR/SER=1`, `STBY=1`, `RANGE=0` (bipolar 5 V), and `REFSEL=1`; `DB15/BYTE_SEL` is low for serial mode. Dedicated TLV9024 comparators and an open-drain fault OR implement OCP without relying on FPGA firmware or ADC conversion. Comparator threshold and latch behavior still require tolerance and bench validation.

`RUN_OK = GATE_EN & PWR_READY & ARMED`. FPGA deadtime is at least 500 ns; FD6288 internal deadtime is not the primary mechanism. Each high-side bootstrap path runs from `VDRV_12V` through a diode to `BST_x`, with `CBOOT` between `BST_x` and `SW_x`. Gate series resistors start at 10 ohm and gate-source pull-downs at 10 kohm; tune from measured switching waveforms. Shunt Kelvin paths share the force nets electrically but must reach the shunt pads independently in PCB copper.

## Grounding strategy

The PCB uses one continuous ground reference on the bottom layer. High-current bridge return paths stay local to the DC-link negative node and do not share narrow traces with ADC/encoder return currents. The analog section is physically isolated from switch nodes rather than separated with a slit plane.

## Configuration-time default and restart policy

R80..R85 pull the six raw PWM inputs to GND through 10k. R86 pulls GATE_EN to GND through 10k. With VIO valid and FPGA outputs high impedance, the AND gates have defined low commands and RUN_OK remains low. R56..R61 are separate pull-downs on the already gated driver inputs. C80..C83 bypass the four safety logic supplies; C84/C85 bypass the two OCP comparators. C43..C45 bypass INA241 supply pins to GND.

U20 implements hardware ARM latching, with supervised VIO/VA5 reset and raw OCP/PWR_GOOD asynchronous clear. Fault recovery alone cannot resume PWM. J1.10 FAULT_CLEAR re-arms on a rising edge with GATE_EN low. See `ocp_latch_review_2026-10-09.md` for the required clear protocol, timing conditions and bench gates. Nominal thresholds are 0.2941V and 4.7059V (approximately +/-22.06A); tolerance, filtering, response time and test evidence remain open.

U26 SN74LVC3G17 applies Schmitt conditioning to the open-drain supervisor reset, raw OCP_N and raw PWR_GOOD before ordinary CMOS logic. The conditioned PWR_READY feeds U11/U23; raw diagnostic nets and their original pull-ups remain intact.
