"""Check proposed AD7606C-16 high-bandwidth ADC ECO without pretending it is wired.

The existing Rev.A hardware/BOM still uses ADS8588S; this guard validates
the prospective FPGA pin/register contract and stops a candidate from being
mistaken for a committed production schematic. It is not KiCad ERC or STA.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = Path("fpga/ad7606c_fast_candidate_profile_2026-10-12.json")
CANDIDATES = Path("hardware/ad7606c_servo/adc_fast_candidates_2026-10-12.csv")
SOURCE_BOM = Path("hardware/ads8588s_servo/bom.csv")
XDC = Path("fpga/ax7010_servo_reva.xdc")
SCHEMATIC = Path("hardware/ads8588s_servo/current_adc.kicad_sch")

LEGACY = {
    "ADC_CONVST": (11, "Y14"),
    "ADC_SCLK": (12, "W14"),
    "ADC_CS_N": (13, "P18"),
    "ADC_RESET": (14, "N17"),
    "ADC_DOUTA": (15, "U15"),
    "ADC_DOUTB": (16, "U14"),
    "ADC_BUSY": (17, "P16"),
    "ADC_FRSTDATA": (18, "P15"),
}
NEW = {
    "ADC_DOUTC": (29, "U12", "SPARE_A0"),
    "ADC_DOUTD": (30, "T12", "SPARE_A1"),
    "ADC_SDI": (31, "T10", "SPARE_A2"),
}
EXPECTED_REGISTERS = {
    "0x02": 0x10,
    "0x03": 0x55,
    "0x04": 0x65,
    "0x05": 0x66,
    "0x06": 0x66,
    "0x07": 0x0F,
    "0x08": 0x00,
}


def check(root: Path = ROOT) -> list[str]:
    e: list[str] = []
    d = json.loads((root / PROFILE).read_text(encoding="utf-8"))
    adc = d["selection"]
    if d.get("status") != "ECO_CANDIDATE_NOT_PRESENT_IN_WORKING_SCHEMATIC":
        e.append("candidate wrongly claims finished KiCad schematic or release")
    if adc.get("mpn") != "AD7606C-16BSTZ" or adc.get("lcsc") != "C5371769":
        e.append("selected performance ADC MPN / LCSC changed without review")
    if adc.get("packaging_alternate") != "AD7606C-16BSTZ-RL":
        e.append("unqualified ADC packing alternate")
    with (root / CANDIDATES).open(encoding="utf-8", newline="") as fd:
        candidates = {x["MPN"]: x for x in csv.DictReader(fd)}
    if candidates.get("AD7606C-16BSTZ", {}).get("Recommendation") != "PERFORMANCE_PRIMARY":
        e.append("performance sourcing candidate missing or switched")
    if candidates.get("AD7606C-16BSTZ", {}).get("Quote_currency") != "USD":
        e.append("web dollar quotation must not be mislabeled as yuan")
    with (root / SOURCE_BOM).open(encoding="utf-8", newline="") as fd:
        bom = {x["Ref"]: x for x in csv.DictReader(fd)}
    if bom.get("U6", {}).get("MPN") != "ADS8588SIPM":
        e.append("old vs candidate hardware status out of date: U6 BOM MPN differs")
    sch = (root / SCHEMATIC).read_text(encoding="utf-8")
    if '(property "Value" "ADS8588SIPM"' not in sch:
        e.append("old vs candidate hardware status out of date: schematic U6 changed")
    if d.get("mode_straps", {}).get("OS0") != 1 or d["mode_straps"].get("OS1") != 1 or d["mode_straps"].get("OS2") != 1:
        e.append("AD7606C software mode requires OS0=OS1=OS2=1")
    if d["mode_straps"].get("PAR_SER_SEL") != 1:
        e.append("AD7606C parallel-serial selection must be serial for J10")

    for addr, expected in EXPECTED_REGISTERS.items():
        try:
            actual = int(d["configuration"][addr]["value"], 16)
        except (KeyError, TypeError, ValueError):
            actual = None
        if actual != expected:
            e.append(f"AD7606C candidate register {addr} != expected 0x{expected:02x}")
    config = int(d["configuration"]["0x02"]["value"], 16)
    lanes = 1 << ((config >> 3) & 0b11)
    t = d["timing"]
    if lanes != 4 or t.get("serial_lanes") != 4:
        e.append("candidate must use 4 physical DOUT lanes")
    if t.get("adc_channels") != 8 or t.get("resolution_bits") != 16:
        e.append("candidate must carry eight simultaneously sampled 16-bit channels")
    expected_clocks = t["adc_channels"] * t["resolution_bits"] // t["serial_lanes"]
    if t.get("frame_sclk_edges") != expected_clocks or expected_clocks != 32:
        e.append("four-lane frame must use 32 20MHz SCLK periods")
    expected_us = expected_clocks / (t["initial_sclk_hz"] / 1_000_000)
    if abs(t.get("initial_frame_time_us", -1) - expected_us) > 1e-9:
        e.append("initial serial timing doesn't match lane count and SCLK")
    if t.get("analog_3db_bandwidth_khz") != 150:
        e.append("0-5V high-bandwidth option is 150kHz, not 220kHz")

    pins = d.get("external_pins", [])
    if len(pins) != 11:
        e.append("ADC candidate must map 8 existing + 3 new J10 signals")
    refs = {(x["signal"]): x for x in pins}
    if len(refs) != len(pins) or len({x["header_pin"] for x in pins}) != len(pins):
        e.append("duplicate candidate J10 net or header pin")
    if len({x["fpga_pin"] for x in pins}) != len(pins):
        e.append("duplicate Xilinx candidate PACKAGE_PIN")
    for name, (pin, pkg) in LEGACY.items():
        p = refs.get(name, {})
        if p.get("header_pin") != pin or p.get("fpga_pin") != pkg:
            e.append(f"{name}: don't change real J10 mapping silently")
    for name, (pin, pkg, old) in NEW.items():
        p = refs.get(name, {})
        if p.get("header_pin") != pin or p.get("fpga_pin") != pkg or p.get("legacy_signal") != old:
            e.append(f"{name}: future J10 spare allocation incorrect")

    # This is a candidate: new ADC signals MUST NOT already be active in the
    # old XDC until the new physical PCB copper and latest schematic exist.
    xdc = (root / XDC).read_text(encoding="utf-8")
    active = "\n".join(line for line in xdc.splitlines() if line.strip().startswith("set_property"))
    for name in NEW:
        if re.search(r"\[get_ports\s+" + name + r"\]", active):
            e.append(f"{name} erroneously enabled on current unmigrated XDC")

    lanes_expected = {
        "DOUTA": ["IU_ADC", "IV_ADC"],
        "DOUTB": ["IW_ADC", "VBUS_ADC"],
        "DOUTC": ["NTC_BOARD", "NTC_BOARD_AUX"],
        "DOUTD": ["UNUSED_CH7", "UNUSED_CH8"],
    }
    if d.get("data_lanes") != lanes_expected:
        e.append("AD7606C lane/channel order not aligned to FIG 106")
    # Current signal envelope is 2.55 +/- 2.0 V in the stated rated peak.
    if not (0 < (5.1 / 2 - 20 * 0.1) and (5.1 / 2 + 20 * 0.1) < 5.0):
        e.append("phase current amp nominal output overflows 0-5V")
    return e


if __name__ == "__main__":
    errors = check()
    if errors:
        print("AD7606C performance candidate CONTRACT FAILED")
        for msg in errors:
            print(" -", msg)
        raise SystemExit(1)
    print("AD7606C performance candidate CONTRACT PASSED")
    print("Legacy ADS8588S U6 is still source of truth; 4 DOUT x 2 words, 20MHz -> 1.6us; FPGA/PCB ECO is NOT IMPLEMENTED")
