# LCSC availability-first BOM and schematic optimization (2026-10-10)

> STATUS: **PARTIAL / NOT FABRICATION-APPROVED**. This branch implements two verified pin- and footprint-compatible IC replacements. The 2512 shunt is a purchasing candidate, **not electrically/physically installed**. Legacy THT shunts on the PCB are deprecated. Do not order Gerbers or PCBA from this branch until the shunt redesign is complete and all release gates pass.

## Confirmed revisions

| References | Former | Selected | LCSC | Verification scope |
|---|---|---|---|---|
| U2/U3/U4 | INA241A2ID, gain20 | INA240A1DR, gain20 | C2060769 | same D/SOIC-8 physical pin mapping, unchanged 20 V/V, 5mR => 0.1V/A |
| U15/U16 | TLV9024PWR, open-drain | LM339LVPWR, open-drain | C3658338 | TSSOP14 pin assignment/open-drain verified, slower propagation needs fault validation |
| RSH1/2/3 | 650FPR005E, 4-terminal THT | **candidate** LR2512-23R005F4, RALEC 3W/1%/2512, **2 terminals** | C154688 | NOT drop-in: all force/sense copper, physical pads and thermal compliance remain OPEN |

Data: https://www.lcsc.com/product-detail/Current-Sense-Amplifiers_Texas-Instruments-INA240A1DR_C2060769.html ;
https://www.lcsc.com/product-detail/comparators_ti-lm339lvpwr_C3658338.html ;
https://www.lcsc.com/product-detail/MORNSUN-Guangzhou-S-T_RALEC-LR2512-23R005F4_C154688.html ;
https://www.ti.com/lit/ds/symlink/ina240.pdf ;
https://www.ti.com/product/LM339LV .

LCSC web stock snapshot (not API-reserved stock): INA240A1DR C2060769 20,911; LM339LVPWR C3658338 2,000; RALEC C154688 120 in a recent listing (another stale market snapshot differed). Must re-check **Chinese checkout inventory and 5/10-board quantity** immediately before purchasing.

## Electrical deltas and blocking checks

- INA240A1 is **20 V/V**, NOT INA240A2 (50 V/V). Physical SOIC pinout is identical to the existing INA241 D mapping: IN-1, GND2, REF2-3, NC4, OUT5, VS6, REF1-7, IN+8. Existing grounded NC pin4 is permitted on INA240 D. Supply and REF nodes unchanged.
- Common-mode rating changes from INA241 maximum +110 V to INA240 +80 V. At VBUS 48V, validate U/V/W switch-node ringing, recovery, negative transients, voltage stress and filtering for all gate-switch events. Never assume 100V MOSFET VDS rating makes INA240 adequate.
- LM339LV is open-drain and has approx. 600 ns **typical** propagation versus 100 ns typical on TLV9024. Propagation maximum/overdrive, output pullup R54/R55, rise/fall, filter and hardware latch response must be measured before relying on OCP. Push-pull TLV9034 is NOT an equivalent substitute for the open-drain fault OR.
- Shunt at 10Arms: I²R = 0.5 W; at 20Arms held 30s: 2 W (for 5mΩ). 3W nominal 2512 rating does **not** itself close 40°C ambient, <=50K board-rise or repeated 30s hot-pulse acceptance. RALEC derates above 70°C; solder temperature, copper area and resistance calibration require bench checks. Source datasheet https://item.szlcsc.com/166030.html .
- The current KiCad netlist uses separate physical current pads 1/2 and Kelvin sense pads 3/4, paired by jumper-pin groups. RALEC 2512 has **only two physical terminals**. Never write that 2-terminal part into the 4-terminal through-hole board footprint or reuse its 1/3,2/4 internal jumper metadata. Design and solder-qualify a genuine 2-terminal 2512 footprint with independent sense pickup at each resistor terminal, then reroute/verify the six sense paths and force copper, update schematic net assignments and convert all netlist/PCB Kelvin regressions. Until then legacy board and BOM explicitly block fabrication.

## Stock-first and domestic-first policy

Critical: shunts, gate driver, MOSFETs, ADC/current chain, OCP/safety, power converters, high-current connectors retain proven-grade device/qualification. Do not switch MOSFETs on a similar-looking model name. For low-criticality 0603 resistors, decoupling capacitors, optional diodes and headers, use documented in-stock LCSC Chinese brands such as UNI-ROYAL/RALEC or Fenghua only after locking exact capacitance vs DC bias, tolerance, temperature grade, voltage rating, package and solderability. Price and inventory checks must be date-stamped; unconfirmed parts remain TBD in the source BOM. No made-up C codes or claimed stock.

## Acceptance outstanding

1. Remove ALL remaining old Ohmite/THT shunt footprints and 4-terminal-only symbol semantics from the manufactured design; create 2512 shunt mechanical and electrical integration, and reassign board nets/pad and Kelvin sense topology.
2. Re-export BOM/netlist/placement and KiCad10 ERC0; run no-exclusion DRC0, unconnected0, parity0; run 6 physical Kelvin checks after redesign, plus via, return paths, solder mask/paste and 20A thermal checks.
3. Revalidate ±22.5A nominal OCP thresholds and worst-case shutdown including comparator propagation, INA240 current sensor saturation and 80V common-mode behavior. Freeze reliable turn-off timing before hot-power hardware.
4. Complete 115 unresolved fitted-part exact-MPN qualifications, and rerun LCSC inventory/pricing; defer domestic substitutions of other parts until datasheet/pinout/footprint equivalence and stock are demonstrated.

## Checks this branch can and cannot claim

Textual KiCad symbol/instance/BOM/PCB value strings are updated for the ICs; underlying PCB copper, pads, net names and circuit component counts are intentionally unchanged. A script-level s-expression balance check was performed on generated content; actual KiCad10 ERC/DRC, no-fault OCP dynamics, SMT DFM and component procurement **have not been performed in this session**. Do not claim a safe-to-fabricate production release.
