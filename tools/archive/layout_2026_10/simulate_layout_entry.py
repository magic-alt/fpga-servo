"""Reproducible passive/ideal-source ngspice audit; NOT a vendor IC model.

Use a fresh KiCad XML netlist. Results cannot qualify switching, protection
latency, power sequencing, ADC acquisition, or thermal performance.
"""
import argparse
import ctypes as ct
import hashlib
import json
import math
import os
from pathlib import Path
import xml.etree.ElementTree as ET


class Vector(ct.Structure):
    _fields_ = [("name", ct.c_char_p), ("type", ct.c_int),
                ("flags", ct.c_short), ("real", ct.POINTER(ct.c_double)),
                ("complex", ct.c_void_p), ("length", ct.c_int)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--ngspice-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    root = ET.parse(args.netlist).getroot()
    values = {e.attrib["ref"]: e.findtext("value") for e in root.findall("./components/comp")}
    pins = {(n.attrib["ref"], n.attrib["pin"]): net.attrib["name"]
            for net in root.findall("./nets/net") for n in net.findall("node")}

    def value(ref):
        raw = values[ref].strip().replace("Ohm", "").replace("R", "")
        for suffix, scale in [("uF", 1e-6), ("nF", 1e-9), ("k", 1e3), ("m", 1e-3)]:
            if raw.endswith(suffix):
                return float(raw[:-len(suffix)]) * scale
        return float(raw)

    def same(*nodes):
        nets = [pins[node] for node in nodes]
        if len(set(nets)) != 1:
            raise ValueError(f"Unexpected topology at {nodes}: {nets}")

    # Fail rather than simulate stale assumptions if physical-pin topology changes.
    same(("R1", "2"), ("R2", "1"))
    same(("R2", "2"), ("R3", "1"), ("C5", "1"))
    same(("R3", "2"), ("C5", "2"), ("C1", "2"), ("C2", "2"))
    same(("R1", "1"), ("C1", "1"), ("C2", "1"))
    same(("R50", "2"), ("R53", "1"), ("U15", "3"), ("U15", "6"))
    same(("R53", "2"), ("C40", "2"), ("C92", "2"))
    same(("U2", "5"), ("R40", "1"))
    same(("R40", "2"), ("C40", "1"))
    same(("R88", "2"), ("C92", "1"))
    same(("R88", "1"), ("R87", "1"))
    same(("RSH1", "1"), ("U2", "8"))
    same(("RSH1", "2"), ("U2", "1"))
    expected = {("R1", "1"): "/VBUS_PROT", ("R3", "2"): "/GND",
                ("R50", "1"): "/VA_5V",
                ("R88", "1"): "/FAULT_CLEAR"}
    for pin, net in expected.items():
        if pins[pin] != net:
            raise ValueError(f"Unexpected net at {pin}: {pins[pin]}")
    used = ["R1", "R2", "R3", "C5", "R50", "R53",
            "R40", "C40", "R87", "R88", "C92", "C1", "C2", "RSH1", "RSH4"]
    from gate_ab_verify import require_graph, corner_current_limits, bus_static_error_budget, require_bus_budget_parts
    from check_adc_validity import verify as verify_adc
    require_graph(values, pins)
    require_bus_budget_parts(args.netlist)
    adc_errors, adc_bounds = verify_adc(args.netlist)
    if adc_errors:
        raise ValueError("; ".join(adc_errors))
    v = {ref: value(ref) for ref in used}
    rail_low, rail_high = adc_bounds["regulated_static_V"]
    nominal_rail = .6 * (1 + value("R94") / value("R95"))
    dll_directory = None
    if os.name == "nt":
        dll_directory = os.add_dll_directory(str(args.ngspice_library.resolve().parent))
    lib = ct.CDLL(str(args.ngspice_library.resolve()))
    log = []
    callback_type = ct.CFUNCTYPE(ct.c_int, ct.c_char_p, ct.c_int, ct.c_void_p)

    @callback_type
    def output(message, _ident, _userdata):
        if message:
            log.append(message.decode("utf-8", "replace"))
        return 0

    # KiCad's bundled ngspice-46 faults in the optional pre-init nospinit
    # entry points. Use its standard initialization, then set explicit options
    # for every deck; no user configuration or environment values are logged.
    lib.ngSpice_Init.argtypes = [ct.c_void_p] * 7
    lib.ngSpice_Init.restype = ct.c_int
    if lib.ngSpice_Init(output, None, None, None, None, None, None):
        raise RuntimeError("ngspice initialization failed")
    lib.ngSpice_Command.argtypes = [ct.c_char_p]
    lib.ngSpice_Command.restype = ct.c_int
    lib.ngSpice_Circ.argtypes = [ct.POINTER(ct.c_char_p)]
    lib.ngSpice_Circ.restype = ct.c_int
    lib.ngGet_Vec_Info.argtypes = [ct.c_char_p]
    lib.ngGet_Vec_Info.restype = ct.POINTER(Vector)

    def command(text):
        if lib.ngSpice_Command(text.encode()):
            raise RuntimeError(f"ngspice command failed: {text}")

    command("version")
    version = list(log)

    def run(name, elements, analysis, vectors):
        deck = [f"{name}: ideal passive layout-entry audit", *elements,
                ".options reltol=1e-6 abstol=1e-12 vntol=1e-9 method=trap", ".end"]
        (args.output / f"{name}.cir").write_text("\n".join(deck) + "\n", encoding="utf-8")
        command("destroy all")
        encoded = [line.encode() for line in deck]
        lines = (ct.c_char_p * (len(encoded) + 1))(*encoded, None)
        if lib.ngSpice_Circ(lines):
            raise RuntimeError(f"ngspice rejected {name}")
        command(analysis.lower())
        data = {}
        for name in vectors:
            info = lib.ngGet_Vec_Info(name.encode())
            if not info or not info.contents.real or info.contents.length < 1:
                (args.output / "ngspice.log").write_text("\n".join(log)+"\n", encoding="utf-8")
                raise RuntimeError(f"Missing simulation vector {name}")
            data[name] = [info.contents.real[i] for i in range(info.contents.length)]
        return data

    divider = run("bus_divider", ["Vbus bus 0 0", f"R1 bus mid {v['R1']}",
                  f"R2 mid adc {v['R2']}", f"R3 adc 0 {v['R3']}", f"C5 adc 0 {v['C5']}"],
                  "dc Vbus 24 48 1", ["v-sweep", "v(adc)"])
    refs = run("bus_ocp_reference", ["Vrail rail 0 5.1", f"R50 rail threshold {v['R50']}",
               f"R53 threshold 0 {v['R53']}"],
               f"dc Vrail {rail_low} {rail_high} {(rail_high-rail_low)/20}",
               ["v-sweep", "v(threshold)"])

    def step(name, resistance, capacitance, amplitude, duration, pull=None):
        elements = [f"Vstep source 0 PULSE(0 {amplitude} 0 1p 1p {duration*2} {duration*4})",
                    f"Rseries source filtered {resistance}", f"Cfilter filtered 0 {capacitance} IC=0"]
        if pull is not None:
            elements.append(f"Rpull source 0 {pull}")
        data = run(name, elements, f"tran {duration/1000} {duration} uic", ["time", "v(filtered)"])
        tau = resistance * capacitance
        errors = [abs(y - amplitude * (1 - math.exp(-t/tau)))
                  for t, y in zip(data["time"], data["v(filtered)"]) if t > 1e-10]
        if max(errors) > amplitude * 0.001:
            raise AssertionError(f"RC analytical cross-check failed for {name}: {max(errors)}")
        return data, tau, max(errors)

    bus_step, bus_tau, bus_error = step("bus_filter_step",
        (v['R1']+v['R2'])*v['R3']/(v['R1']+v['R2']+v['R3']), v['C5'], 1, 0.003)
    current = run("phase_current_filter", [
        "Vstep source 0 PWL(0 2.5 1u 2.5 1.001u 4.9 1.4u 4.9)",
        f"R40 source filtered {v['R40']}", f"C40 filtered 0 {v['C40']} IC=2.5"],
        "tran 1n 1.35u uic", ["time", "v(filtered)"])
    current_tau = v['R40'] * v['C40']
    crossing = next(t for t, voltage in zip(current['time'], current['v(filtered)'])
                    if t >= 1e-6 and voltage >= 3.7)
    midstep_analytical = 1.001e-6 + current_tau * math.log(2)
    if abs(crossing-midstep_analytical) > 15e-9:
        raise AssertionError("Phase ADC filter mid-step analytical check failed")
    current_error = abs(crossing-midstep_analytical)
    clear, clear_tau, clear_error = step("clear_filter_step", v['R88'], v['C92'], 3.3, 1e-5, v['R87'])
    capacitance = v['C1'] + v['C2']
    regen = run("regen_ideal_unsunk", ["Iregen 0 bus DC 1", f"Cbus bus 0 {capacitance} IC=48"],
                "tran 1u 1.4m uic", ["time", "v(bus)"])
    gain = v['R3'] / (v['R1'] + v['R2'] + v['R3'])
    for x, y in zip(divider['v-sweep'], divider['v(adc)']):
        if not math.isclose(y, x * gain, rel_tol=1e-8):
            raise AssertionError("Divider analytical cross-check failed")
    for rail, threshold in zip(refs['v-sweep'], refs['v(threshold)']):
        if not math.isclose(threshold, rail*v['R53']/(v['R50']+v['R53']), rel_tol=1e-8):
            raise AssertionError("Bus OCP reference analytical cross-check failed")
    if not math.isclose(regen['v(bus)'][-1], 55, abs_tol=1e-5):
        raise AssertionError("Capacitor charge analytical cross-check failed")
    for ref in ['R50', 'R53']:
        component = root.find(f"./components/comp[@ref='{ref}']")
        description = component.findtext('description', '')
        tolerance = component.findtext("./fields/field[@name='Tolerance']", '')
        if '0.1%' not in description and tolerance != '0.1%':
            raise ValueError(f"Expected explicit 0.1% divider tolerance: {ref}")
    bus_ocp = corner_current_limits(v, rail_range=(rail_low, rail_high), nominal_rail=nominal_rail)
    result = {"scope": "passive/ideal sources only; no vendor active-device or switching models",
        "target": {"bus_V": [24, 48], "continuous_phase_A": 10, "pwm_Hz": 20000},
        "netlist_sha256": hashlib.sha256(args.netlist.read_bytes()).hexdigest(),
        "ngspice_library_sha256": hashlib.sha256(args.ngspice_library.read_bytes()).hexdigest(),
        "ngspice_version_log": version, "netlist_values": {ref: values[ref] for ref in used},
        "bus_divider_V_at_24_48": [divider['v(adc)'][0], divider['v(adc)'][-1]],
        "bus_filter": {"tau_s": bus_tau, "fc_Hz": 1/(2*math.pi*bus_tau), "step_max_error_V": bus_error},
        "bus_ocp": bus_ocp,
        "bus_ocp_static_budget": bus_static_error_budget(v, (rail_low, rail_high)),
        "phase_current_filter": {"tau_s": current_tau, "fc_Hz": 1/(2*math.pi*current_tau),
            "gain_at_20kHz_dB": -10*math.log10(1+(2*math.pi*20000*current_tau)**2),
            "midstep_3p7V_s": crossing, "analytical_midstep_s": midstep_analytical,
            "midstep_error_s": current_error, "scope": "Phase ADC settling only; not bus OCP delay"},
        "clear_filter": {"tau_s": clear_tau, "step_max_error_V": clear_error},
        "regen": {"nominal_capacitance_F": capacitance, "energy_48_to_55V_J": 0.5*capacitance*(55**2-48**2),
            "ideal_1A_time_48_to_55V_s": 0.0014, "simulated_final_V": regen['v(bus)'][-1],
            "warning": "55 V is illustrative overvoltage, not approved operating voltage; no sink/clamp/ESR/ESL modeled"},
        "shunt_at_10A_RMS_W_each": 10**2*v['RSH1'],
        "analytical_cross_checks": "PASS"}
    (args.output / "results.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    (args.output / "ngspice.log").write_text("\n".join(log)+"\n", encoding="utf-8")
    datasets = {"bus_divider": divider, "bus_ocp_reference": refs, "bus_filter_step": bus_step,
                "phase_current_filter": current, "clear_filter_step": clear, "regen_ideal_unsunk": regen}
    for name, data in datasets.items():
        keys = list(data)
        rows = [",".join(keys), *[",".join(f"{x:.12g}" for x in row) for row in zip(*data.values())]]
        (args.output / f"{name}.csv").write_text("\n".join(rows)+"\n", encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    axes[0, 0].plot(divider['v-sweep'], divider['v(adc)'])
    axes[0, 0].set(xlabel="Bus (V)", ylabel="ADC input (V)", title="Native divider: DC sweep")
    axes[0, 1].plot([x*1e9 for x in current['time']], current['v(filtered)'])
    axes[0, 1].set(xlabel="Time (ns)", ylabel="Phase ADC filter (V)", title="Phase ADC 47 ohm / 1 nF step; no OCP delay")
    axes[1, 0].plot([x*1e6 for x in clear['time']], clear['v(filtered)'])
    axes[1, 0].set(xlabel="Time (us)", ylabel="Clear filter (V)", title="Clear RC; ideal GPIO")
    axes[1, 1].plot([x*1e3 for x in regen['time']], regen['v(bus)'])
    axes[1, 1].axhline(48, color="red", linestyle="--", label="Operating maximum")
    axes[1, 1].set(xlabel="Time (ms)", ylabel="Bus (V)", title="Unsunk 1 A regeneration; ideal 200 uF")
    axes[1, 1].legend()
    for axis in axes.flat:
        axis.grid(alpha=0.3)
    fig.suptitle("Layout entry audit: passive / ideal models only")
    fig.savefig(args.output / "simulation_summary.png", dpi=160)
    plt.close(fig)
    print(json.dumps(result, indent=2))
    if dll_directory:
        dll_directory.close()


if __name__ == "__main__":
    main()
