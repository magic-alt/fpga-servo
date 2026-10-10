# Rev.A architecture

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
| Phase-current shunts | 5 mOhm, 3 W two-terminal SMD, independent Kelvin pickup; mounted thermal qualification open |
| Bus OCP shunt | 2 mOhm, independent Kelvin pickup; nominal positive +25 A trip only |
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
   - onboard F1: Littelfuse 0456025.ER, 25 A SMD, 72 VDC / 500 A interrupt rating; J3.1 enters VIN_RAW, F1 feeds VIN_FUSED; J6 alone is an excluded external system interface. No external fuse/holder
   - confirm actual bus current/inrush, source fault current <=500 A, bus surge/regeneration <=72 V, cable energy and fuse thermal coordination before higher-power operation
   - bulk capacitance close to bridge; D1 TVS is DNP, so no fitted TVS protection or qualified regeneration sink
   - bus-voltage divider to ADC

2. **Three-phase inverter**
   - six BSC040N10NS5 100 V MOSFETs
   - DRV8300DPWR non-inverted TSSOP20 driver; DI variant is not interchangeable
   - per-gate series resistor and gate-source pulldown
   - integrated bootstrap diodes; 470 nF CBOOT per high-side channel; external D2..D4 removed

3. **Phase-current measurement**
   - one 5 mOhm two-terminal SMD shunt in each motor phase
   - INA240A1 high-side/bidirectional amplifier per phase
   - REF1=VA_5V, REF2=GND -> nominal 2.55 V zero-current output
   - Kelvin sense traces, no load current in sense copper

4. **Data acquisition**
   - ADS8588S, 8 simultaneous channels
   - CH1/2/3: IU/IV/IW
   - CH4: VBUS
   - CH5: MOSFET-board NTC
   - CH6: board-mounted NTC2 (legacy net name NTC_MOTOR); no external motor sensor interface exists. S12 remains OPEN until the required sensing location/interface is confirmed.
   - CH7/8: unused, currently tied to GND
   - serial interface uses two DOUT lines; J2 is removed; only J1 connects the active AX7010 J10 signals
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

All six non-inverted DRV8300DPWR PWM inputs are hardware-gated before the driver. `RUN_OK = GATE_EN & PWR_READY & ARMED`; any missing condition forces all six driver input commands low. FPGA deadtime remains at least 500 ns, with switching and shoot-through verification still required. CBOOT1..3=470 nF connect BST to each switch node; the driver has integrated bootstrap diodes. RG1..6=33 ohm and gate-source pulldowns=10 kohm require measured waveform validation.

The latest authorized hardware OCP detects **positive bus current only**, independently of the phase ADC. RSH4=2 mOhm separates VBUS_PROT from VBUS_BRIDGE, which supplies the high-side MOSFET drains. U5 INA240A1DR senses upstream minus downstream with both reference pins grounded, producing ideal 0.04 V/A for positive current. U15 LM393LVDDFR compares this output at pin 2 against R50=8.2k/R53=2k threshold at pin 3. At VA5=5.1 V, 1.0 V threshold gives nominal +25 A trip and pulls OCP_N low above threshold. U16/R51/R52 are removed. Reverse-current and phase-current window OCP are not provided.

The fresh passive calculation gives +24.357135..+25.659766 A using regulated VA5 bounds, divider +/-0.1% and shunt +/-1%. Adding selected-part TCR and published INA/comparator error terms expands the conditional static engineering estimate to +23.935464..+26.107636 A for +25..+125 degC component temperature and 24..48 V DC common-mode. This is not a permitted operating-temperature range or a guaranteed trip interval: supply test-condition applicability, grounded-reference errors, assembly/aging drift and dynamic effects remain open. See [the error budget and OEM limits](design_calculations.md). Bus current is not phase current, so this threshold is not an absolute ceiling for the 20 A phase operating peak. The FPGA diagnostic path remains available but does not replace hardware OCP.

Phase INA240A1 U2..U4 retain REF1=VA_5V and REF2=GND, nominal 2.55 V zero and 0.1 V/A sensitivity; R40..R42/C40..C42 serve the ADC only, with no OCP taps. ADS8588S straps remain `OS=000`, `PAR/SER=1`, `STBY=1`, `RANGE=0` (bipolar 5 V), `REFSEL=1`, and `DB15/BYTE_SEL=0`. Each phase and bus shunt's sense traces must reach the inner terminal lands independently of force copper.

## Grounding strategy

The PCB uses one continuous ground reference on the bottom layer. High-current bridge return paths stay local to the DC-link negative node and do not share narrow traces with ADC/encoder return currents. The analog section is physically isolated from switch nodes rather than separated with a slit plane.

## Configuration-time default and restart policy

R80..R85 pull the six raw PWM inputs to GND through 10k. R86 pulls GATE_EN to GND through 10k. With VIO valid and FPGA outputs high impedance, the AND gates have defined low commands and RUN_OK remains low. R56..R61 are separate pull-downs on the already gated driver inputs. C80..C83 bypass the four safety logic supplies; C84 bypasses bus INA240 U5 and C85 bypasses LM393LV U15. C43..C45 bypass INA240 supply pins to GND.

U20 implements hardware ARM latching, with supervised VIO/VA5 reset and raw OCP/PWR_GOOD asynchronous clear. Fault recovery alone cannot resume PWM. J1.10 FAULT_CLEAR re-arms on a rising edge with GATE_EN low. See `ocp_latch_review_2026-10-09.md` for the required clear protocol, timing conditions and bench gates. The bus detector has a nominal 1.000 V threshold (+25 A positive bus current). Response time, fault overshoot and complete error budget remain open.

U26 SN74LVC3G17 applies Schmitt conditioning to the open-drain supervisor reset, raw OCP_N and raw PWR_GOOD before ordinary CMOS logic. The conditioned PWR_READY feeds U11/U23; raw diagnostic nets and their original pull-ups remain intact.

U25 is now TPS389001DSER, independently powered by VIO and sensing VA5 through R92=3.24k/R93=1k. Undervoltage asynchronously clears ARM; recovery alone cannot re-arm. See [2026-10-10 repair](adc_undervoltage_repair_2026-10-10.md) for physical pin maps, static margins and open dynamic qualification. R92 uses the reviewed +/-0.702% static budget; the minimum falling threshold is 4.791889 V, maximum recovery 5.001931 V, and static VA5 range 5.026621..5.173923 V. These values do not qualify rapid droop or gate-off latency. ADC current-zero calibration and encoder supply acceptance must use the 5.1 V nominal rail.
