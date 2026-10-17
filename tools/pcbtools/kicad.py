"""Shared KiCad native parsing; no project-specific references."""

import re
from pathlib import Path
from dataclasses import dataclass

NUMBER = r"-?\d+(?:\.\d+)?"


@dataclass(frozen=True)
class Form:
    text: str
    line: int


def _scan_balanced(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
            if depth < 0:
                raise ValueError(f"unexpected ')' at byte {i}")
    raise ValueError(f"unclosed s-expression starting at byte {start}")


def extract_forms(text: str, head: str) -> list[Form]:
    pattern = re.compile(r"\(" + re.escape(head) + r"(?=\s|\))")
    forms: list[Form] = []
    for match in pattern.finditer(text):
        end = _scan_balanced(text, match.start())
        forms.append(
            Form(
                text=text[match.start():end],
                line=text.count("\n", 0, match.start()) + 1,
            )
        )
    return forms


def strip_form(text: str, head: str) -> str:
    forms = extract_forms(text, head)
    if not forms:
        return text
    chars = list(text)
    search_from = 0
    for form in forms:
        idx = text.find(form.text, search_from)
        if idx < 0:
            continue
        for i in range(idx, idx + len(form.text)):
            if chars[i] != "\n":
                chars[i] = " "
        search_from = idx + len(form.text)
    return "".join(chars)


def assert_balanced(text: str) -> None:
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unexpected ')' at byte {i}")
    if in_string:
        raise ValueError("unterminated quoted string")
    if depth != 0:
        raise ValueError(f"unbalanced parentheses: depth={depth}")


def parse_at(form: str) -> tuple[float, float] | None:
    match = re.search(
        r"\(at\s+(" + NUMBER + r")\s+(" + NUMBER + r")(?:\s+" + NUMBER + r")?\)",
        form,
    )
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def parse_xy(form: str) -> list[tuple[float, float]]:
    return [
        (float(match.group(1)), float(match.group(2)))
        for match in re.finditer(
            r"\(xy\s+(" + NUMBER + r")\s+(" + NUMBER + r")\)", form
        )
    ]


def head_string(form: str, head: str) -> str | None:
    match = re.match(
        r"\(" + re.escape(head) + r'\s+"((?:\\.|[^"\\])*)"', form
    )
    return match.group(1) if match else None


def property_value(form: str, name: str) -> str | None:
    match = re.search(
        r'\(property\s+"'
        + re.escape(name)
        + r'"\s+"((?:\\.|[^"\\])*)"',
        form,
    )
    return match.group(1) if match else None


def run_native(command: list[str], cwd: Path, timeout: float = 180) -> dict:
    """Use argument vectors and retain failure evidence without logging env vars."""
    import subprocess
    try:
        p = subprocess.run([str(x) for x in command], cwd=cwd, capture_output=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return {"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                "status": "PASS" if p.returncode == 0 else "FAIL"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": 1, "stdout": "", "stderr": "",
                "status": "NOT_RUN", "error": type(exc).__name__}


def read_xml_summary(path: Path) -> dict:
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    comps = root.findall("./components/comp")
    nets = root.findall("./nets/net")
    if root.tag != "export" or not comps or not nets:
        raise ValueError("Empty or incomplete native XML export")
    refs = [c.get("ref") for c in comps]
    if None in refs or len(set(refs)) != len(refs): raise ValueError("Duplicate/missing component reference")
    pins = set()
    for net in nets:
        if not net.get("name"): raise ValueError("Unnamed native net")
        for node in net.findall("node"):
            key = (node.get("ref"),node.get("pin"))
            if key[0] not in refs or not key[1] or key in pins:
                raise ValueError("Invalid or duplicate physical pin")
            pins.add(key)
    if not pins: raise ValueError("Native XML has no physical pins")
    return {"components":len(comps), "nets":len(nets), "physical_pins":len(pins)}


def portable_netlist(path: Path, source: str) -> None:
    # Export metadata alone is normalized; connectivity records remain exact.
    from xml.sax.saxutils import escape
    import json
    text = path.read_text(encoding="utf-8")
    if "<source>" in text:
        pattern = r"(<design>\s*)<source>[^<]*</source>"
        value = "<source>" + escape(source) + "</source>"
    else:
        pattern = r'(\(design\s*)\(source\s+"(?:[^"\\]|\\.)*"\)'
        value = "(source " + json.dumps(source) + ")"
    text,n = re.subn(pattern, lambda m:m[1]+value, text)
    if n != 1: raise ValueError("Expected exactly one native source metadata field")
    path.write_text(text, encoding="utf-8")
