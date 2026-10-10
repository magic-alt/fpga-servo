# Triple low-side shunt schematic conversion and mandatory PCB migration

**STATUS: SCHEMATIC CANDIDATE — NO FABRICATION; PCB HAS OLD INLINE THT SHUNTS.**

Commit redefines the current measurement circuit as three separate low-side shunts, not in-line motor-phase current sense. RALEC LR2512-23R005F4 (LCSC C154688) is a 5mΩ ±1% 3W 2512 alloy SMT, with **two physical terminals**; not an interchangeable four-terminal pad device. TI INA240A1DR (C2060769) is 20V/V with existing SOIC8 pin mapping. LM339LVPWR (C3658338) open-drain comparator OCP speed gate remains OPEN.

| Phase | Motor node | Shunt high/Kelvin positive | Shunt low/Kelvin negative |
|---|---|---|---|
| U | Q1.1/2/3 = Q2.5 = J4.1 (SW_U) | Q2.1/2/3 + RGS2.2 + RSH1.1 + U2.8 (LS_U_SRC) | RSH1.2 + U2.1 = GND |
| V | Q3.1/2/3 = Q4.5 = J4.2 (SW_V) | Q4.1/2/3 + RGS4.2 + RSH2.1 + U3.8 (LS_V_SRC) | RSH2.2 + U3.1 = GND |
| W | Q5.1/2/3 = Q6.5 = J4.3 (SW_W) | Q6.1/2/3 + RGS6.2 + RSH3.1 + U4.8 (LS_W_SRC) | RSH3.2 + U4.1 = GND |

Shunt upper must NOT be shorted to GND by source copper, lower GND plane, RGS pull-down, through-hole remnants or alternate bypass traces. The PWM gate-source pulldown must terminate above the shunt at the respective MOSFET source. Kelvin sense wires must land at both shunt terminal pads, apart from load-current entry/exit; independent physical inspection and a new pad-based copper graph regression are required. Old 4-terminal jumper groups are removed from the schematic; the old PCB/library/test versions are retired, **not accepted**.

## Power calculations and system impacts

- At 10A instantaneous through shunt: 0.5W; at 20A: 2W; R=5mΩ, 20V/V => 0.1V/A. RMS/thermal use conduction-window duty and worst-case steady equivalent, not an assumed full motor phase RMS waveform. 40°C ambient, ≤50K rise, hot spot and resistor derating at >70°C still OPEN. 3W catalog rating is not enough.
- Under SVPWM 20kHz, the three low-side shunt signals do **not** equal phase currents at all switching states. ADS8588S CONVST must sample two or more genuinely conducting lower switches after blanking + INA240 settling + ADS acquisition, or discard and use sector-based reconstruction. Max modulation, 0/100% duty, dynamic braking, reverse/re-generation transitions and severe current transients require bench validation.
- Existing low-side shunts do not guarantee short protection when a lower switch is OFF. A qualified fast hardware overcurrent path (including driver/OCP latency, shoot-through cases and regeneration) remains necessary before power-on. LM339LV typical delay ~600ns, compared with TLV9024 ~100ns; evaluate worst-case with RC analog filter and fault-current rise.
- Check INA240 common-mode upper +80V and negative transients; confirm low-side FD6288 LO and source-referenced gate voltages against switching bounce. Overcurrent comparator nominal ±22.5A thresholds and ADC signal dynamic range should be reassessed.
- This schematic repin requires full PCB re-placement and re-routing of power ground, each 2512 pad and dedicated sense return, no other path around each resistor. Previous 0/0/0 PCB DRC is for the **old topology**, therefore invalid as evidence.
- The current PCB is still the old Ohmite 4T inline design. `check_design.py` deliberately blocks fabrication. Run native KiCad 10 ERC/DRC after PCB changes and regenerate BOM/position/PDF/netlist; verify each shunt, 2-pad-land footprint, 6 sense contacts, thermal/current and OCP safety dynamically. No native KiCad10 in this execution environment; **no ERC/DRC pass is claimed**.

References: [TI TIDA-010023](https://www.ti.com/tool/TIDA-010023), [TIDA-00778](https://www.ti.com/tool/TIDA-00778), [TI low-side shunt caveats](https://www.ti.com/document-viewer/lit/html/sboa627), [RALEC LCSC C154688](https://item.szlcsc.com/166030.html), [INA240](https://www.ti.com/lit/ds/symlink/ina240.pdf).
