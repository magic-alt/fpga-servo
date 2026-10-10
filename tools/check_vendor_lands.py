"""Verify TI copper lands and bounded same-package pad rules, not release readiness."""

from pathlib import Path
import argparse
import re
from kicad_native import extract_forms, property_value, head_string

ROOT = Path(__file__).resolve().parents[1]
LANDS = {}
for ref in ("U8", "U9", "U10", "U20", "U26"):
    LANDS[ref] = ("TI_DCU0008A_VSSOP8_P0.5mm", (0.85, 0.30), 1.55, 0.50)
LANDS["U18"] = ("TI_DDF0008A_SOT23_8_P0.65mm", (1.05, 0.45), 1.30, 0.65)
for ref in ("U2", "U3", "U4"):
    LANDS[ref] = ("TI_D0008A_SOIC8_P1.27mm", (1.55, 0.60), 2.70, 1.27)
INTERNAL_GAPS = {
    **{f"Q{i}": 0.60 for i in range(1, 9)},
    **{f"U{i}": 0.65 for i in (2, 3, 4)},
    "U1": 0.25,
    "U6": 0.20,
    "U18": 0.20,
}


def check(text):
    errors, found = [], set()
    for footprint in extract_forms(text, "footprint"):
        ref = property_value(footprint.text, "Reference")
        if ref not in LANDS:
            continue
        found.add(ref)
        name, size, x, pitch = LANDS[ref]
        if head_string(footprint.text, "footprint") != "fpga-servo:" + name:
            errors.append(ref + ": expected manufacturer land-pattern identifier")
        pads = extract_forms(footprint.text, "pad")
        if {head_string(p.text, "pad") for p in pads} != set("12345678") or len(
            pads
        ) != 8:
            errors.append(ref + ": expected physical pads 1..8 exactly once")
            continue
        for pad in pads:
            number = int(head_string(pad.text, "pad"))
            pos = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)", pad.text)
            dimensions = re.search(r"\(size\s+([-\d.]+)\s+([-\d.]+)", pad.text)
            expected = (
                (-x, -1.5 * pitch + pitch * (number - 1))
                if number <= 4
                else (x, 1.5 * pitch - pitch * (number - 5))
            )
            if not pos or any(
                abs(float(v) - e) > 1e-6 for v, e in zip(pos.groups(), expected)
            ):
                errors.append(
                    f"{ref}.{number}: pad center differs from manufacturer lands"
                )
            if not dimensions or any(
                abs(float(v) - e) > 1e-6 for v, e in zip(dimensions.groups(), size)
            ):
                errors.append(
                    f"{ref}.{number}: copper land differs from manufacturer dimensions"
                )
    errors.extend(ref + ": missing footprint" for ref in sorted(set(LANDS) - found))
    return errors


def check_internal_pad_rules(text):
    """Reject scope expansion to tracks/vias/other instances or reduced minima."""
    errors = []
    rules = extract_forms(text, "rule")
    expected = {ref + " internal lands": ref for ref in INTERNAL_GAPS}
    names = [head_string(rule.text, "rule") for rule in rules]
    if set(names) != set(expected) or len(names) != len(expected):
        errors.append(
            "internal pad rules: expected exactly the reviewed fourteen rules"
        )
    for rule in rules:
        name = head_string(rule.text, "rule")
        if name not in expected:
            continue
        ref = expected[name]
        conditions = extract_forms(rule.text, "condition")
        intended = f"A.Type == 'Pad' && B.Type == 'Pad' && A.Reference == '{ref}' && B.Reference == '{ref}'"
        if (
            len(conditions) != 1
            or head_string(conditions[0].text, "condition") != intended
        ):
            errors.append(
                ref
                + ": internal clearance must apply only to two pads of this exact instance"
            )
        minimum = re.search(
            r"\(constraint\s+clearance\s+\(min\s+([\d.]+)mm\)\)", rule.text
        )
        if not minimum or abs(float(minimum[1]) - INTERNAL_GAPS[ref]) > 1e-9:
            errors.append(ref + ": internal clearance differs from reviewed minimum")
        if re.search(r"\(severity\b", rule.text):
            errors.append(ref + ": severity override is prohibited")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "board",
        nargs="?",
        type=Path,
        default=ROOT / "hardware/ax7010_servo_reva.kicad_pcb",
    )
    args = parser.parse_args()
    errors = check(args.board.read_text(encoding="utf-8"))
    rules = args.board.with_suffix(".kicad_dru")
    errors.extend(
        check_internal_pad_rules(
            rules.read_text(encoding="utf-8") if rules.exists() else ""
        )
    )
    print("TI LANDS / INTERNAL PAD RULES " + ("FAILED" if errors else "PASSED"))
    for error in errors:
        print(" - " + error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
