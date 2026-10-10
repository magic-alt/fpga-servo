# Rev.A architecture

> **Proposed schematic revision, 2026-10-10:** Three independent low-side shunts replace the former in-line shunts: Q2/Q4/Q6 source → 5 mΩ 2512 resistor → GND; motor outputs connect directly to inverter switch nodes. PCB re-layout and manufacturing gates are OPEN. Prior descriptions below are historical; see [3-shunt migration](low_side_3shunt_migration_2026-10-10.md).

## Design intent

This board is a lab/engineering servo-drive daughter board for the ALINX AX7010. It deliberately keeps the hard real-time PWM, ADC timing and encoder counting in the Zynq PL while leaving high-power switching, signal conditioning and encoder line reception on the daughter board.

## Electrical target

| Item | Rev.A target |
|---|---:|
| DC bus | 24-48 V (confirmed 2026-10-09) |
| Operating bus maximum | 48 V; transient clamp/energy limit pending |
| MOSFET VDS | 100 V |
| PWM | 20 kHz |
| Continuous phase current | 10 A RMS (confirmed 2026-10-10) |
| Peak phase current | 20 A for 30 s (confirmed 2026-10-10); repetition interval pending |
| Maximum ambient | 40 degC (confirmed 2026-10-10) |
| Temperature-rise target | <=50 K; measurement locations pending; does not override lower component qualification limits |
| Cooling | Forced air (confirmed 2026-10-10); airflow and fan-fault behavior pending |
| Current shunt | 5 mOhm, >=5 W, Kelvin |
| Current gain | 20 V/V |
| Current transfer | 0.1 V/A |
| Current output zero | VA_5V / 2; nominal 2.55 V, requires per-channel calibration |
| ADC | 8 ch, simultaneous, 16 bit, 200 kSPS/ch |
| Encoder | 5 V ABZ (confirmed 2026-10-10); existing differential A+/A-, B+/B-, Z+/Z- interface; current/startup/common-mode envelope pending |
| Logic | 3.3 V |
| PCB | 2 layer, 1.6 mm, 2 oz recommended |

The latest user instruction removes the brake circuit from scope (2026-10-10). No board brake is added and PSU regeneration absorption is not assumed. S03 system surge/regeneration qualification remains OPEN; brake sizing is not a prerequisite for the other repair work. See the [thermal and encoder design brief](brake_thermal_design_basis_2026-10-10.md). The 20 A operating peak is distinct from the hardware OCP threshold and its fault overshoot; it is not yet demonstrated as an absolute current ceiling. U26 local free-air temperature must remain <=85 degC to use the current maximum-delay budget; 40 degC ambient permits only 45 K local rise there, pending thermal proof or a qualified redesign.

## Functional blocks

1. **DC-link / protection**
   - external upstream F1: Littelfuse KLKD025.T 25A / 600VDC in LPSM0001Z holder, near source positive; J3 is the fused board input; F1/J6 are system wiring, excluded from PCB
   - confirm actual bus-current/inrush, cable and fault-energy coordination before higher-power operation
   - bulk capacitance close to bridge; D1 TVS is DNP, so no fitted TVS protection or qualified regeneration sink
   - bus-voltage divider to ADC

2. **Three-phase inverter**
   - six BSC040N10NS5 100 V MOSFETs
   - FD6288T TSSOP20 driver
   - per-gate series resistor and gate-source pulldown
   - bootstrap diode/capacitor for each high-side channel

3. **Phase-current measurement**
   - one 5 mOhm two-terminal SMT shunt under each low-side MOSFET (Q2/Q4/Q6), not in each motor phase
   - INA241A2 high-side/bidirectional amplifier per phase
   - REF1=VA_5V, REF2=GND -> nominal 2.55 V zero-current output
   - Kelvin-like two-pad pickup at resistor inside edges, no load current in sense copper; re-layout/DFM validation OPEN

4. **Data acquisition**
   - ADS8588S, 8 simultaneous channels
   - CH1/2/3: IU/IV/IW
   - CH4: VBUS
   - CH5: MOSFET-board NTC
   - CH6: board-mounted NTC2 (legacy net name NTC_MOTOR); no external motor sensor interface exists. S12 remains OPEN until the required sensing location/interface is confirmed.
   - CH7/8: unused, currently tied to GND
   - serial interface uses two DOUT lines; J2 is fitted with VIO/GND connected and unused signal pins NC; it does not implement a parallel-data path
   - serial-mode DB0..6, DB9..13 and DB14/HBEN now visibly grounded; U6 uses the dedicated ADS8588S_SERIAL symbol

5. **Encoder**
   - AM26LV32E quad RS-422 receiver at 3.3 V
   - 120 ohm termination footprints on A/B/Z are currently DNP; fit decision depends on actual cable/encoder
   - shared VA_5V encoder supply through F2 PTC; exact PTC and short-circuit isolation remain unqualified

6. **Auxiliary power**
   - LM5164: DC bus -> 12 V gate/aux rail
   - TPS62901RPJR external-feedback 12 V -> nominal 5.1 V VA_5V rail; R94=75k/R95=10k, MODE=VIN (forced PWM 2.5MHz), VOS=output
   - 3.3 V logic is supplied by AX7010 VIO; there is no local 3.3 V LDO in the current schematic
   - safety AND gates and encoder receiver run from AX7010 `VIO_3V3`; ADC DVDD also uses this rail
   - dedicated digital isolation/buffer arrays are not fitted; partial-power behavior remains a qualification gate

## Safety state

FD6288 has no single global hardware enable pin, so all six PWM inputs are hardware-gated before the driver. `RUN_OK` is defined as the logical AND of FPGA enable, auxiliary-power-good and the hardware ARMED latch. Any missing condition forces all six FD6288 input commands low.

Hardware over-current detection is based on the conditioned current-sense outputs and a window-comparator network. The FPGA fault path remains a second, independent diagnostic path.

The INA241A2 references use `REF1=VA_5V` and `REF2=GND`, placing zero current near 2.55 V. The 5 mOhm shunt and 20 V/V gain give 0.1 V/A. ADS8588S straps are `OS=000`, `PAR/SER=1`, `STBY=1`, `RANGE=0` (bipolar 5 V), and `REFSEL=1`; `DB15/BYTE_SEL` is low for serial mode. Dedicated TLV9024 comparators and an open-drain fault OR implement OCP without relying on FPGA firmware or ADC conversion. Comparator threshold and latch behavior still require tolerance and bench validation.

`RUN_OK = GATE_EN & PWR_READY & ARMED`. FPGA deadtime is at least 500 ns; FD6288 internal deadtime is not the primary mechanism. Each high-side bootstrap path runs from `VDRV_12V` through a diode to `BST_x`, with `CBOOT` between `BST_x` and `SW_x`. Gate series resistors start at 10 ohm and gate-source pull-downs at 10 kohm; tune from measured switching waveforms. Shunt Kelvin paths share the force nets electrically but must reach the shunt pads independently in PCB copper.

## Grounding strategy

The PCB uses one continuous ground reference on the bottom layer. High-current bridge return paths stay local to the DC-link negative node and do not share narrow traces with ADC/encoder return currents. The analog section is physically isolated from switch nodes rather than separated with a slit plane.

## Configuration-time default and restart policy

R80..R85 pull the six raw PWM inputs to GND through 10k. R86 pulls GATE_EN to GND through 10k. With VIO valid and FPGA outputs high impedance, the AND gates have defined low commands and RUN_OK remains low. R56..R61 are separate pull-downs on the already gated driver inputs. C80..C83 bypass the four safety logic supplies; C84/C85 bypass the two OCP comparators. C43..C45 bypass INA241 supply pins to GND.

U20 implements hardware ARM latching, with supervised VIO/VA5 reset and raw OCP/PWR_GOOD asynchronous clear. Fault recovery alone cannot resume PWM. J1.10 FAULT_CLEAR re-arms on a rising edge with GATE_EN low. See `ocp_latch_review_2026-10-09.md` for the required clear protocol, timing conditions and bench gates. Nominal thresholds at the new 5.1V rail are 0.3000V and 4.8000V (approximately +/-22.5A); tolerance, filtering, response time and test evidence remain open.

U26 SN74LVC3G17 applies Schmitt conditioning to the open-drain supervisor reset, raw OCP_N and raw PWR_GOOD before ordinary CMOS logic. The conditioned PWR_READY feeds U11/U23; raw diagnostic nets and their original pull-ups remain intact.

U25 is now TPS389001DSER, independently powered by VIO and sensing VA5 through R92=3.24k/R93=1k. Undervoltage asynchronously clears ARM; recovery alone cannot re-arm. See [2026-10-10 repair](adc_undervoltage_repair_2026-10-10.md) for physical pin maps, static margins and open dynamic qualification. ADC current-zero calibration and encoder supply acceptance must use the new 5.1V nominal rail.
