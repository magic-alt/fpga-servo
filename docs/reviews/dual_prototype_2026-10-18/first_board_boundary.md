# Engineering first-board evidence boundaries

**Fabrication remains BLOCKED until the pre-fabrication design/manufacturing requirements below close.** Engineering prototypes may generate physical evidence after manufacture. This does not authorize known pin-map, footprint, unrouted-copper or fabrication-process defects, and does not weaken [strict release gates](../../release_gates.md).

Both boards use 24–48 V, 20 kHz, 10 Arms continuous phase current / **20 A instantaneous sinusoidal phase amplitude for 30 s (14.142 Arms)**, 40°C forced air and 12 V total 1 A as design inputs, not qualified ratings. The separate conservative 20 Arms bus-envelope calculation does not redefine the phase peak. Both require four layers. Airflow, fan-failure response, peak repetition/cooldown and encoder startup load must be defined before rated-operation acceptance.

## Required before prototype fabrication

| Domain | Required pre-fabrication evidence | Current restriction |
| --- | --- | --- |
| U7 electrical ECO | Correct OEM map in both library/embedded symbols; fresh exports prove exactly authorized physical-pin changes and preserve unrelated connectivity | OEM pin map and exact post-ECO native graph are corrected; current adopted board evidence is linked from the review index. Human engineering approval remains OPEN. |
| Fitted BOM and lands | Exact primary identities plus compatible manufacturer pin/land/drill/paste/body/polarity evidence; deliberate DNP/external exceptions recorded | All 180/202 source objects are inventoried. Confirmed CAD land defects were repaired; generic lands, tolerances, forming/seating and solder-process approval remain OPEN. |
| J1/J5 holes | Exact original JILN drawing plus a fabrication process/order guaranteeing its finished-hole window | Original manufacturer family drawing recovered and viewed; controlled-hole fabrication acceptance is still open. |
| Stackup/DFM/package | Actual orderable JLC stackup/copper/finish and hole rules; CAD conformance; independent Gerber/drill/BOM/CPL review from one frozen source | Published JLC041621-3313 / NP-155F Tg155 / ENIG candidate and exact layer build-up are recorded. Tg155 material acceptance, all-via Type VII POFV and controlled finished holes require written acceptance before order. |
| Copper/connectivity | Both native ERC 0 errors/0 warnings/0 exclusions; all-category DRC 0 violations/0 unconnected/0 parity; every schematic page/PCB layer and critical loops/Kelvin/returns/clearance reviewed | Use fresh source-bound native and wholeboard geometry/CAM records. Earlier zero-DRC candidates with escape/body/In1 defects are preserved as superseded evidence; their zero counts cannot be reused. |
| Current/thermal design | Document hot/nominal/pulse losses and conductor/joint/fuse/shunt/connector/cooling assumptions with credible geometry and margins | Measurements may follow manufacture. Missing calculation or incompatible current path is a design blocker; absence of thermal-soak traces alone is not. |
| DC link/fault/regen | Capacitor ripple allocation, input impedance/prospective fault, fuse interruption/I²t coordination and bus/transient envelope; compatible external containment/commissioning interface | The ten damped 100 uF/100 V branches and J7 containment interface are implemented. Source impedance, fault coordination, external branch protection and a verified 60 V ceiling including overshoot remain explicit acceptance conditions. |
| Auxiliary 1 A | Adopt both authorized 150 µH networks and conditional current-limit/hot-inductance/effective-capacitance/loading assumptions; review local land/keepout | Physical full-load startup remains open; a conditional calculation cannot become a guarantee. |
| Acceptance record | Prototype-ready separate from pcb_release; frozen source hashes, exact evidence, staged board-specific commissioning and explicit NOT_RUN gates | No disabled checks, exclusions, invented signoff or missing-input PASS. |

## Concrete controlled-hole proposal

The recovered JILN3210 manufacturer drawing (A0,2015-01-28,1/1) specifies recommended PCB holes Ø1.02 mm and PCB board tolerance ±0.05 mm. The earlier 1.02±0.03 mm value was a shared window for different vendor families, not demonstrated JLC regular-process capability. JLC regular PTH tolerance is +0.13/−0.08 mm: at 1.02 mm nominal that permits 0.94–1.15 mm, outside the claimed JILN 0.97–1.07 mm window.

JLC advertises a special **±0.05 mm circular press-fit-hole tolerance for multilayer ENIG**, finished holes 0.55–2.0 mm, requiring identified holes in PCB remarks. Proposed resolution: **primary JILN only; nominal 1.02 mm; guaranteed finished 0.97–1.07 mm; four-layer ENIG; identify every J1/J5 hole in drawing/order**. This requests a dimensional process; it does not call the soldered JILN connector a press-fit part. Obtain fabricator acceptance that this controlled process can be applied to these holes, with appropriate final inspection. Do not claim ±0.03 mm or BOOMELE interchangeability.

The original manufacturer image PDF has now been retrieved and visually inspected (106876 bytes; SHA-256 `cc33060f70b21b6e0791e7bf46a9e4e7384c29e2d08b6dac34ffa207fe665ef9`). Its family ordering code covers the selected 321040SG0ABK00A01 and 321010SG0ABK00A01 variants; this is fresh drawing evidence, not fabricator acceptance. If the controlled process cannot be obtained, select an exact connector with accessible OEM guidance compatible with an accepted process and perform an explicit connector/footprint ECO. Do not enlarge holes by guesswork. [JLC hole capability](https://jlcpcb.com/capabilities/pcb-capabilities), [manufacturer drawing via distributor](https://atta.szlcsc.com/upload/public/pdf/source/20190920/C429963_F9492D44774B1CF9B8CD95C0C24EAA23.pdf), [selected part record](../../sourcing/header_selected_evidence_2026-10-10.json).

## Physical evidence allowed after fabrication

| Domain | May be open for engineering-prototype ordering? | Required restriction until measured acceptance |
| --- | --- | --- |
| Auxiliary startup/thermal/transient | Yes, after reviewed static design and load-fixture plan | Bridge inhibited; start limited energy/load; qualify 24/48 V and total 12 V 1 A before dependent operation. |
| Sense-to-VGS-off, SOA, slew, bootstrap and rail loss | Yes, after static circuit/layout review | No high-energy motor test; use bounded-current/energy fixtures and actual VGS traces. Positive-bus +25 A is nominal, not reverse protection or a maximum fault current. |
| 10 Arms soak / 20 A 30 s | Yes, with credible loss/conductor/cooling budget | No rated-current claim; fix airflow, repetition/cooldown and component temperature limits before accepting those tests. |
| ADC/translator sequence/calibration/FPGA timing | Yes, with correct static pin/rail design | GATE_EN low. No HDL/firmware exists here; separate implementation must prove reset/configuration, fresh frames and fault inhibition before switching. |
| Encoder cable/inrush/ESD/termination | Yes, with bounded source/cable/load plan and mechanical fit already closed | Verify corrected U7, hot behavior/inrush/common-mode; no unspecified cable or PTC-only assurance. |
| External sink/clamp measurements | May be open at ordering only if board/interface design already accommodates specified containment | **No motor operation before independent sink/clamp validation.** Ordinary supplies are not assumed sinks. Define energy/power/voltage/fault envelope and validate fixture first. |
| Production/reliability qualification | Yes for explicitly authorized engineering first prototypes | Full release remains BLOCKED; no production-qualified label. |

See [bring-up procedure](../../bringup.md). Deferring measurements until hardware exists never defers known static-design defects or manufacturing incompatibility. All physical tests remain **NOT_RUN**.

The new J7 protected-bus fixture connection is downstream of F1 and RPP, upstream of RSH4. It preserves access when RPP turns off, but input F1 cannot interrupt current sourced through J7. A source-capable external fixture requires independent coordinated fusing, current/energy limiting and isolation/disconnection. Fixture qualification must include loss of input, wiring disconnection and fault shutdown before motor operation.
