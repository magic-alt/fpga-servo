from __future__ import annotations

import re
from dataclasses import dataclass

NUMBER = r"-?\\d+(?:\\.\\d+)?"


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
    pattern = re.compile(r"\\(" + re.escape(head) + r"(?=\\s|\\))")
    forms: list[Form] = []
    for match in pattern.finditer(text):
        end = _scan_balanced(text, match.start())
        forms.append(
            Form(
                text=text[match.start():end],
                line=text.count("\\n", 0, match.start()) + 1,
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
            if chars[i] != "\\n":
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
        r"\\(at\\s+(" + NUMBER + r")\\s+(" + NUMBER + r")(?:\\s+" + NUMBER + r")?\\)",
        form,
    )
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def parse_xy(form: str) -> list[tuple[float, float]]:
    return [
        (float(match.group(1)), float(match.group(2)))
        for match in re.finditer(
            r"\\(xy\\s+(" + NUMBER + r")\\s+(" + NUMBER + r")\\)", form
        )
    ]


def head_string(form: str, head: str) -> str | None:
    match = re.match(
        r"\\(" + re.escape(head) + r'\\s+"((?:\\\\.|[^"\\\\])*)"', form
    )
    return match.group(1) if match else None


def property_value(form: str, name: str) -> str | None:
    match = re.search(
        r'\\(property\\s+"'
        + re.escape(name)
        + r'"\\s+"((?:\\\\.|[^"\\\\])*)"',
        form,
    )
    return match.group(1) if match else None
