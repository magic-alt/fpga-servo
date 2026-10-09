# PCB repair implementation plan — 2026-10-09

Goal: recover schematic/PCB parity, qualify real footprints, repair placement/routing and produce honest freeze evidence.

Constraints: existing topic branch; preserve hardware/.history; 130x95mm outline and H1..H4 fixed; connectors movable; 15A continuous/25A <=5s target; 5mOhm >=5W four-terminal shunts; external surge/regeneration protection mandatory; logic -40..85C; two layers/2oz target, fabricator qualification open.

- [x] A: baseline snapshots, fresh netlist/ERC/DRC and classified evidence.
- [ ] B: manufacturer-qualified terminals and shunts, local footprints, BOM and package evidence.
- [x] C: physical-pin parity checker; restore all electrical references and nets while retaining mechanics and audited copper.
- [ ] D: real-package placement, mechanical keepouts, actual netclass assignments.
- [ ] E: power/gate/Kelvin/safety/digital routing, zone refill, all-severity DRC and visual review.
- [ ] Acceptance: five repo checks, netlist safety, OCP behavior, ERC 0/0/0, physical parity clean, DRC 0/unconnected 0/exclusions 0; unresolved physical/bench gates stay open.

The approved conversation plan is the full behavioral specification. No pin assignment changes without matching interface/XDC updates. Do not delete copper to claim closure; replacement routes require matching endpoints. DNP parts retain pads. No guessed MPN or footprint qualification. Freeze depends on actual AX7010 revision, external protection specification, partial-power/OCP bench evidence and thermal qualification.

Execution status: A/C complete; B partial (terminal/shunt selections implemented; AX7010/F1 and remaining vendor qualification open); D preliminary; E and freeze acceptance incomplete. See `docs/pcb_repair_progress_2026-10-09.md`.
