# AD7606C continuation review - 2026-10-18

Status: SCHEMATIC AUTOMATED GATES PASS; COMPONENT FREEZE / PCB / RELEASE INCOMPLETE.

## Scope and source

Worktree branch: `feat/ad7606c-hardware-completion`, based on `5b5d725`.
The original checkout and its unrelated untracked files were preserved.
No schematic, symbol, BOM, PCB or electrical connectivity changes were made in this step.

The repository is a hardware project. The root `fpga/` directory has been removed:
its original ADS8588S XDC moved unchanged to `hardware/ads8588s_servo/`, and its
historical ADC candidate JSON moved unchanged to `hardware/ad7606c_servo/`.
Current tools, tests, configuration and documentation use the new paths.
Historical evidence and archived tools retain their original recorded paths.
The AD7606C project already had its own XDC beside the schematic; no HDL was added.

## Executed verification

- Interpreter: local Anaconda Python 3.12.4; KiCad CLI / pcbnew 10.0.3.
- Both project schematic static checks: PASS.
- AD7606C schematic verify: fresh XML and KiCad netlist, all-severity ERC,
  baseline project checks/ERC, 18 fault injections, physical-pin, OCP steady-state,
  supply-validity and PDF export checks: PASS.
- AD7606C fresh XML: 181 system objects, 162 nets, 180 board objects and external J6.
- Both projects native ERC: 0 errors, 0 warnings, 0 exclusions.
- Existing ERC settings remain unchanged, including inherited ignored categories
  footprint_filter, four_way_junction, simulation_model_issue, single_global_label.
  No new exclusion, severity reduction or NC workaround was introduced.
- Full regression command: 157 tests, 143 passed, 14 explicitly skipped.
  Separate native pcbnew geometry lane: 39 tests, all passed. This tests tooling
  against fixtures/the retained board; it is not AD7606C PCB DRC evidence.
- Native footprint audit: all 180 board components resolve to actual KiCad library
  footprints; each symbol pin-number set exactly equals its footprint pad-number
  set. J6 is explicitly `exclude_from_board` in fresh XML. Detailed results:
  [component pad audit](component_pad_audit_2026-10-18.json).
- Viewed the fresh 11-page schematic overview and enlarged ADC supply/reference,
  translator power/OE and J10 areas. This is a visual review of unchanged sources,
  not a complete manufacturer or independent electrical sign-off.
- AD7606C PCB DRC/parity/routing: NOT_RUN; there is no AD7606C PCB source yet.
- No hardware, thermal, transient, FPGA STA or manufacturing qualification executed.

## Manufacturer cross-checks and component blockers

[ADI AD7606C-16 Rev.A](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf),
Table 6 and Table 9: VDRIVE must not exceed AVCC+0.3 V; the implemented same-rail
AVCC/VDRIVE and TXU translation avoid the independent-supply static violation.
REGCAP pins 36/39 each require their own 1 uF, and REFCAPA/B 44/45 are tied together
with 10 uF. These match the physical-pin checks. Dynamic power-down remains open.

[TI TXU0204 Rev.A](https://www.ti.com/lit/ds/symlink/txu0204.pdf), Figure 6-1 /
Table 6-1: the selected PW package is 14-pin with two A-to-B and two B-to-A channels.
U27-U29 use that pin/package configuration; this does not qualify cable timing.

[TI LM5164 Rev.D](https://www.ti.com/lit/ds/symlink/lm5164.pdf), electrical
characteristics: peak current-limit range is 1.25/1.5/1.75 A min/typ/max.
The existing 68 uH L1 still lacks complete manufacturer Irms/Isat/thermal proof.
The existing design review also shows that 68 uH with tolerance cannot guarantee
48 V input / 12 V 1 A operation at the illustrative 300 kHz corner. Do not mark
L1 or the whole BOM approved from pin-number matching or a distributor listing.

Further open gates are the actual J10/AX7010 pin continuity and bank voltage,
MPN/package mechanical dimensions and assembly review, shunt/connector/current
and temperature ratings, fuse fault-current coordination, surge/regeneration,
VA5 decay to actual VGS-off timing, OCP dynamics and partial-power behavior.
See [current release gates](../../../docs/release_gates.md).

## Proposed continuation and required PCB inputs

1. Close schematic/component review first: obtain L1 source specifications and
   the actual 12 V continuous/peak load; review manufacturer land drawings for
   all non-generic selected parts. If load must be 1 A, review a power-stage ECO
   instead of silently treating the present inductor as qualified.
2. Confirm mechanical envelope, mount holes, connector positions and layer stack.
   Recommended starting proposal: retain the old board envelope/holes/interfaces
   and review a new four-layer AD7606C board with a continuous reference plane.
   This is a proposal, not an approved stack or reused routed board.
3. After schematic/footprint and mechanical approval, use native KiCad F8 or an
   actually exposed sync tool to create the new board; review every pad/net and
   mechanical object. Present placement and critical-loop review before routing.
4. Route power/driver loops, Kelvin and OCP before sensitive ADC/interface signals.
   Native DRC acceptance: 0 violations, 0 unconnected, 0 schematic parity issues,
   without lowering severities, blanket exceptions or removing connections.
5. Run both project checks and applicable regression/native lanes, review plots,
   and keep bench/manufacturing gates separate from schematic and DRC results.

The session exposes no callable KiCad MCP tool. CLI and pcbnew are available and
were used. Native GUI/MCP synchronization capability and mechanical approval
must be resolved before PCB creation/routing. No empty board was created merely
to obtain an artificial zero DRC result.

## Final migration evidence

Fresh post-migration verify completed with exit code 0. The [native manifest](../../../artifacts/pcb/ad7606c/20261018T012930Z-tm1oghl6/manifest.json) records each gate and source hash. Before/after native XML comparison requires exact component identity, footprint, net names and physical pin memberships; the comparison passed.
