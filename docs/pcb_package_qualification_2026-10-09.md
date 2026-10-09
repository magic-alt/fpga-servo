# PCB repair package qualification — 2026-10-09

## Accepted design constraints

130 x 95 mm outline and H1..H4 centers remain fixed. Power connectors may move. Targets remain 15 A continuous and 25 A for <=5 s, with 5 mOhm shunts. Two-layer / 2 oz is a design target pending fabrication and thermal validation. Logic qualification is -40..85 C; this is not an 85 C ambient rating for the assembled board. External surge protection, input fault-current interruption and regeneration absorption are mandatory.

## Power terminal selection

J3: Phoenix Contact 1714971, MKDS 5/2-9,5. J4: 1714984, MKDS 5/3-9,5. Manufacturer documentation specifies 32 A nominal, 9.52 mm pitch, 0.9 x 0.9 mm pins, 1.3 mm PCB holes and 21.5 mm installed height. The dimensioned housing drawing uses 4.76 mm end margin and a 4.6 mm rear offset from the pin row. Project footprints use the conservative 12.5 mm illustrated housing depth. PCB annular pad diameter 3.4 mm and courtyard margin 0.5 mm are engineering choices, not vendor requirements.

Manufacturer PDFs and drawings:
- https://www.phoenixcontact.com/us/products/1714971/pdf (dimension and drill drawings, pages 6-7)
- https://www.phoenixcontact.com/us/products/1714984/pdf (same series drawings, pages 6-7)

The manufacturer's current/temperature curve is for 6 mm2 conductor; qualification must use the actual wire and terminal temperature. 32 A nominal is not an unconditional board-level rating. Support the connector during screw tightening. Housing/assembly clearance and harness access remain subject to mechanical review.

## Four-terminal shunt selection

RSH1..RSH3: Ohmite 650FPR005E, 5 mOhm +/-1%, four terminals, 5 W free-air rating at 25 C. This replaces the earlier 3 W BVB selection without changing current sensitivity or OCP thresholds. The manufacturer's 650 drawing specifies 25.40 +/-0.254 mm longitudinal lead centers, 6.35 +/-0.254 mm transverse spacing and 12 AWG / 2.0574 mm lead diameter. Overall length is up to 35.56 mm and height up to 11.43 mm. A conservative courtyard reserves 37 x 11.6 mm. PCB drill 2.6 mm / pad 4.2 mm is a proposed manufacturing allowance; validate lead samples, plating tolerance and assembly fit before release.

The resistor has no polarity and the mechanical drawing has no numbered pins. Project pin assignment is explicit: left/right force = 1/2 at y=-3.175 mm; left/right sense = 3/4 at y=+3.175 mm; x=-12.7/+12.7 mm. This agrees with the existing symbol's P/N/SP/SN graph. Sense traces must start separately at pads 3/4. Geometric symmetry does not permit a shared-current Kelvin trace.

Manufacturer product confirmation: https://www.ohmite.com/catalog/60-series/650FPR005E/
Manufacturer-authored 60 Series four-terminal datasheet, hosted by distributor: https://www.ic-components.cz/files/13/610FPR002E.pdf
The datasheet explicitly lists 650FPR005E. A local copy and rendered drawing are in artifacts/ohmite_4t.pdf and .png.

Dissipation is 1.125 W at 15 A and 3.125 W at 25 A. The published linear free-air derating gives 3.8 W at 85 C; this is a component-level calculation, not assembled-board thermal proof. The specified +/-100 ppm/C TCR is given for 0..85 C; -40 C current accuracy and OCP tolerance must be qualified separately. The larger, elevated part also requires switching-transient, vibration and thermal review. These gates remain open.

## Other packages and interfaces

The other assigned native schematic footprints were found in official KiCad 10 libraries by the prior physical-pin audit. Updating the PCB to them fixes placeholder geometry and pin numbering, but does not close all manufacturer drawing or thermal gates. In particular AX7010 board revision, FD6288 application qualification, exact F1 choice, high-voltage capacitor MPNs and regulator passive calculations remain open. No board routing freeze is claimed.

## Snapshot / reproducibility

Initial source: fe9b115, fix/ocp-latch-industrial-review. Original board, all 20 tracks, original copper zone and schematic snapshots are preserved under artifacts/pcb_repair_before/ with a SHA-256 manifest. hardware/.history/ is untouched.


## Further critical-package review

INA241A2ID: TI D0008A SOIC, 1.27mm pitch. Manufacturer example lands are 1.55x0.6mm on 5.4mm row centers. The loaded KiCad IPC-style pattern uses 1.95x0.6mm on 4.95mm row centers (similar overall outer land span, more heel allowance); this is not a literal copy of the vendor example. Assembly acceptance remains open. Pin mapping was checked against Table 5-1 and exposed an electrical issue: reserved NC pin 4 requires GND. Corrected U2/U3/U4 symbols, schematic and PCB; fresh netlist has 180 nets. Source: https://www.ti.com/lit/ds/symlink/ina241a.pdf (SBOSA30D, pages 2 and 38-39).

ADS8588SIPM: TI PM0064A LQFP64 example uses 0.5mm pitch, 1.5x0.3mm lands and 11.4mm row centers. The loaded KiCad pattern uses 1.55x0.3mm at 11.35mm centers, preserving the outer span. Stencil, assembly tolerance and full application qualification remain open. Source: https://www.ti.com/lit/ds/symlink/ads8588s.pdf (PM0064A board-layout drawing, page 60).

BSC040N10NS5ATMA1: exact OPN/package identity confirmed from the manufacturer product page and part-specific PG-TDSON-8-7 drawing. The loaded footprint maps source lands 1/2/3, gate 4 and drain/exposed pad 5. Full land-pattern and thermal acceptance remains open. Sources: https://www.infineon.com/part/BSC040N10NS5 and https://www.infineon.com/assets/row/public/documents/24/76/infineon-pg-tdson-8-7-bsc040n10ns5atma1-pd-en.pdf .
