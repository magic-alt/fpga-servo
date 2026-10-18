# AD7606C 12 V total 1 A bench acceptance

Status: **NOT_RUN**. This procedure is a test plan, not measurement evidence or permission to fabricate the unfinished PCB. The current 1 A calculation and its assumptions are in [auxiliary power review](aux_power_review_2026-10-18.md). The manufacturing and dynamic gates in [release_gates.md](../../../docs/release_gates.md) remain applicable.

## Test article and setup

Record the tested PCB revision, source commit, assembled BOM, actual copper stackup, L1 lot, U12 marking, output-capacitor lots, instruments/calibration, ambient and measured airflow. Resolve native PCB DRC/parity and physical footprint review before ordering the board. Use an independently current-limited 24–48 V source and a rated electronic load, with the inverter disabled and no motor during auxiliary-rail qualification. A qualified operator must review the fixture and gate-off interlocks before energizing it.

The requirement is **1.000 A continuous total at VDRV_12V**, including DRV8300 consumption and the input power of the downstream 5.1 V converter. External-load current alone does not establish the total. Measure total output current with a reviewed current-sense fixture in series between L1 output and every output branch, retaining the original output capacitance, feedback pickup and short local return. Document any temporary rework and fixture impedance. Do not infer total DC current from input power, nominal converter efficiency or the LM5164 peak-current limit. A calibrated external 1 A load can establish a conservative lower bound only if every other rail current direction and all possible backfeed sources are recorded; failure above the specified total load must not be misreported as a failure at 1 A.

Use Kelvin voltage sensing at the output capacitor and the most distant 12 V consumer. Probe switching and FB nodes with suitable low-inductance, voltage-rated probes. Record the probe bandwidth/ground method and raw captures. Separate output DC accuracy, switching ripple and load-step excursions.

## Required matrix

| Test | Conditions | Required record / acceptance |
| --- | --- | --- |
| Baseline | VIN = 24, 36, 48 V; total IOUT = minimum operating load, 0.5 A, 1.000 A | Local and remote DC voltage, measured total current, input current, ripple, switching frequency, FB ripple; continuous output 11.4–12.6 V (12 V +/-5% proposed acceptance envelope) |
| Loaded cold start | VIN = 24 and 48 V; minimum and maximum actual downstream capacitance; actual board load + electronic load = total 1 A | Capture VIN, VDRV_12V, total current, SW and gate-off state from zero energy; no sustained hiccup, stalled startup, uncontrolled gate pulse or component overstress; record startup time rather than inventing a limit |
| Hot restart | Repeat the loaded-start cases after thermal equilibrium | Same records and acceptance; include input interruption and reapplication |
| Continuous thermal | VIN = 24 and 48 V; total 1 A; 40 C ambient; documented production cooling | At least 60 minutes and until each monitored hotspot changes less than 1 K over 10 minutes; record U12, L1, D2, input/output capacitors and connector temperatures; target rise <=50 K and satisfy every actual component operating limit with a documented junction-temperature assessment |
| Load transients | Minimum actual load <-> 1 A, 0.5 <-> 1 A; measured edge slew, duty and repetition | Voltage extrema, settling time, peak inductor current and gate-off state; proposed rail envelope 11.4–12.6 V, no sustained oscillation; confirm this envelope against actual downstream limits before closing the gate |
| Input transients | VIN 24 <-> 48 V with measured source slew and cable impedance; total 1 A | Raw voltage/current captures, output extrema, no overstress or lost gate-off; this does not qualify surge or motor regeneration |
| Model assumptions | Worst observed voltage, load and temperature cases | Confirm actual switching-frequency range and FB ripple against the static model; establish hot effective inductance at measured peak current. If the 240–360 kHz / 97.2 uH / coupling assumptions fail, recalculate and revise the design before calling the calculation valid |
| Fault and recovery | Reviewed low-energy output overload/short fixture, energy/current limits set by operator | Current peaks, temperature, recovery and no automatic motor enable; compare actual stress with guaranteed component limits. The static 100 ns delay estimate and typical L1 saturation rating are not fault guarantees |

The +/-5% output and transient envelope is an explicit proposed acceptance criterion, not a new datasheet guarantee. Resolve the actual consumer limits, allowed startup time, load slew and cooling specification before marking these rows PASS. Store raw waveform files and temperature time series next to the completed results. Missing data, approximate screenshots or a software-only calculation stay NOT_RUN or BLOCKED. Do not fill the measurement template with predicted values.

## Completion record

For each matrix row, record PASS/FAIL/NOT_RUN, operator, timestamp, instrument settings, measured values, uncertainty, raw-file hashes and deviations. Close the 1 A physical gate only when every required condition is supported by actual measurements and independent review. This gate does not close inverter current/thermal, OCP latency, ADC accuracy, encoder timing, regeneration or manufacturing qualification.
