"""Static source-level Rev.A dual-serial ADC contract and timing-budget guard.

This is deliberately NOT a replacement for a fresh KiCad pin-level XML netlist,
native ERC, FPGA STA or scope-verified sampling performance. It catches
reintroduction of unfitted parallel XDC, missing dual-DOUT ports and confusing
a board-mounted NTC with an external motor sensor.

TI ADS8588S SBAS642A: serial tSCLK>=50 ns; 2*4*16-bit -> 64 clocks, both
DOUTs. Conversion max 3.9 us, no oversampling. Post-conversion dual-DOUT
minimum tCYC=9.7 us; overlapped previous-frame read tCYC=5 us.
"""
from __future__ import annotations
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADC_SIGNAL_NAMES = (
    "ADC_CONVST", "ADC_RESET", "ADC_SCLK", "ADC_CS_N",
    "ADC_DOUTA", "ADC_DOUTB", "ADC_BUSY", "ADC_FRSTDATA",
)
FPGA_PINS = {
    "ADC_CONVST": "Y14", "ADC_RESET": "N17", "ADC_SCLK": "W14",
    "ADC_CS_N": "P18", "ADC_DOUTA": "U15", "ADC_DOUTB": "U14",
    "ADC_BUSY": "P16", "ADC_FRSTDATA": "P15",
}
SCLK_MHZ_MAX = 20.0
PWM_KHZ = 20.0
BITS_PER_CHANNEL = 16
CHANNELS = 8
DOUT_LANES = 2
SAMPLE_CYCLE_MIN_US = 5.0
POST_CONVERSION_MIN_CYCLE_US = 9.7
MAX_CONVERSION_US = 3.9


def get_pin_lines(xdc: str) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for line in xdc.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(
            r"set_property\\s+PACKAGE_PIN\\s+(\\w+)\\s+\\[get_ports\\s+([A-Z0-9_]+)\\]",
            line,
        )
        if m:
            seen.setdefault(m.group(2), []).append(m.group(1))
    return seen


def timing():
    """Calculated serialization time (not full conversion-to-current-loop latency)."""
    clocks_dual = CHANNELS // DOUT_LANES * BITS_PER_CHANNEL
    clocks_single = CHANNELS * BITS_PER_CHANNEL
    return {
        "dual_sclk_cycles": clocks_dual,
        "single_sclk_cycles": clocks_single,
        "dual_20mhz_us": clocks_dual / SCLK_MHZ_MAX,
        "dual_10mhz_us": clocks_dual / 10,
        "one_20mhz_us": clocks_single / SCLK_MHZ_MAX,
        "pwm_cycle_us": 1000 / PWM_KHZ,
    }


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    sch = (root / "hardware/current_adc.kicad_sch").read_text(encoding="utf-8")
    interface = (root / "hardware/ax7010_interface.kicad_sch").read_text(encoding="utf-8")
    xdc = (root / "fpga/ax7010_servo_reva.xdc").read_text(encoding="utf-8")
    with (root / "hardware/bom.csv").open(encoding="utf-8", newline="") as fd:
        bom = {r["Ref"]: r for r in csv.DictReader(fd)}

    for name in ADC_SIGNAL_NAMES:
        token = '(hierarchical_label "' + name + '"'
        if token not in sch:
            errors.append(f"current_adc lacks actual hierarchy signal {name}")
        if token not in interface:
            errors.append(f"J10 interface lacks actual hierarchy signal {name}")

    if 'ADS8588S_SERIAL' not in sch or 'ADS8588SIPM' not in sch:
        errors.append("U6 must be the current ADS8588S serial 64-LQFP selection")
    if sch.count('(label "NTC_BOARD_AUX"') != 2 or 'NTC_MOTOR' in sch:
        errors.append("NTC2 must be identified as a local board sensor at both endpoints")
    if bom.get("NTC2", {}).get("Function") != "10k_B3950_BOARD_AUX":
        errors.append("NTC2 BOM must not claim motor-winding temperature")
    if bom.get("C3", {}).get("Function") != "1uF_250V_FILM":
        errors.append("C3 selected 250V film capacitor BOM metadata is stale")
    if bom.get("L1", {}).get("Function") != "68uH_12V_BUCK_L1_IRMS_ISAT_OPEN":
        errors.append("L1 qualification state must remain explicit until Irms/Isat sign-off")

    pins = get_pin_lines(xdc)
    for name, expected_pin in FPGA_PINS.items():
        actual = pins.get(name, [])
        if actual != [expected_pin]:
            errors.append(f"J10 XDC {name} must map once to {expected_pin}: {actual}")
    for name in pins:
        if name.startswith("ADC_DB") or name in {
            "ADC_RD_N", "ADC_BYTE_SEL", "ADC_RANGE",
            "ADC_OS0", "ADC_OS1", "ADC_OS2",
            "ADC_STBY", "ADC_PAR_SER", "BRAKE_OUT",
            "HALL_U", "HALL_V", "HALL_W",
        }:
            errors.append(f"unfitted J11/PL_B placeholder is an active XDC assignment: {name}")

    t = timing()
    if t["dual_sclk_cycles"] != 64 or t["single_sclk_cycles"] != 128:
        errors.append("dual/one lane ADS8588S bit frame regression")
    if abs(t["dual_20mhz_us"] - 3.2) > 1e-9:
        errors.append("incorrect two-lane 20MHz serial timing")
    if t["pwm_cycle_us"] < POST_CONVERSION_MIN_CYCLE_US:
        errors.append("20kHz PWM budget cannot include post-conversion dual-DOUT read")
    if t["dual_20mhz_us"] >= t["pwm_cycle_us"]:
        errors.append("dual-serial frame exceeds 20kHz PWM period")
    return errors


if __name__ == "__main__":
    errs = check()
    if errs:
        print("ADS8588S DUAL-SERIAL CONTRACT FAILED")
        for err in errs:
            print(" -", err)
        sys.exit(1)
    t = timing()
    print("ADS8588S DUAL-SERIAL SOURCE CONTRACT PASS")
    print(
        f"8x16-bit simultaneous, dual DOUT {t['dual_sclk_cycles']} clocks; "
        f"20MHz={t['dual_20mhz_us']:.1f}us; 10MHz={t['dual_10mhz_us']:.1f}us; "
        f"20kHz PWM={t['pwm_cycle_us']:.1f}us. "
        "Native netlist/ERC and device dynamics are separate gates."
    )
