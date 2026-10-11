# INA240 phase-current selection implementation

Approved specification: user-approved conversation plan, 2026-10-10.

## Constraints
Target branch feat/lcsc-part-selection-schematic-20261010 at f8c8d22. 24–48V, 20kHz, 10Arms continuous, 20A instantaneous phase peak for 30s, 40C ambient, <=50K rise, forced air. Three INA240A1DR channels, 5mOhm SMD shunts. Latest user revision: remove phase-current OCP comparisons; only positive +25 A DC-bus current OCP. Preserve the hardware ARM latch and manual-clear shutdown chain. Replace the external fuse with an onboard fuse; no external fuse holder. Shoot-through timing, source fault envelope and regeneration remain open. Remove J2. Five boards plus 20% spares. Noncritical parts need different-manufacturer same-land-pattern alternatives; critical single-source exceptions require reasons. No unverified Chinese inventory marked available.

## Tasks
1. Qualify purchasable primary/alternate candidates and record evidence.
2. Replace obsolete four-terminal shunts with real two-terminal SMD symbols/lands; remove J2 and its exclusive objects. Update source BOM fields and tests.
3. Audit electrical corners and all eight sheets; update architecture and release evidence.
4. Native schematic-to-PCB sync after schematic checks; preserve mechanics and repair affected routing; native ERC/DRC and Kelvin validation.
5. Fresh independent review, resolve important findings, deliver exact limitations.

## Acceptance
Six project checks, native netlist safety and OCP regression, before/after physical-pin diff with explicit authorized changes, fresh all-severity ERC, visual sheet review, native board parity and DRC. Purchasing acceptance separate from schematic and fabrication acceptance.

## Approved scope revisions during implementation

- User: “不外置保险丝”. Implement an onboard fuse, preserving input overcurrent protection. Compact Littelfuse 0456025.ER is the prototype candidate: verified 25 A /72 VDC /500 A interruption at72 V; the catalogue125V field does not qualify125VDC interruption for this25A variant. Source fault current, surge/regeneration below72V and thermal/coordination evidence remain open. External holder removed from purchasing scope.
- User: delete redundant OCP on the current-sense sheet; protect only using bus current. Later explicitly “母线电流为直流电源提供，仅正向+25A”. Retain three INA240A1 phase ADC channels. Replace six phase-window comparisons with one active bus comparator and retain the existing latched shutdown/re-arm logic.
- Bus prototype: fourth INA240A1, grounded REF pins, 2mOhm HoYLR2512 3W SMD shunt, 0.04V/A. Positive25A corresponds1.000V. The 5.1V-referenced8.2k/2.0k divider gives1.000V nominal. Final purchased resistor tolerance and all analog corners must be recalculated; 25A is nominal, not a guaranteed upper fault current.
- Shunt goes between the DC-link capacitor bus and the bridge positive supply. Any downstream capacitance, analog delays, switching transients and SOA remain dynamic qualification items. No reverse-current OCP is claimed.
- LM393LVDDFR critical comparator candidate has explicitly supply-independent input/output voltage capability. One comparator is used; the unused half is tied to defined levels with its output NC. An unused package half is not an extra protection path.
- Driver replacement candidate DRV8300DPWR is non-inverting. DRV8300DI is rejected because all-low shutdown would turn its low-side outputs on. DP requires internal bootstrap diodes (D2..D4 removed),470nF/50V X7R bootstrap capacitors and33ohm initial gate resistors. Slew<=2V/ns and full shutdown delay are not established by these nominal values; bench qualification remains open.

## Final scope revision

User explicitly deferred layout completion after BOM and schematic completion. Stop PCB routing and do not adopt the unfinished bus-OCP candidate. Deliver fresh schematic/BOM/ERC/netlist evidence; report check_design/PCB parity failures caused by the deferred board honestly. Earlier working-board development edits are retained. User subsequently explicitly requested remote push and PR creation. Preserve the separately advanced low-side branch/PR #14; publish this reviewed phase-inline implementation on a new topic branch. PCB development edits remain local and are excluded from this schematic/BOM PR.
