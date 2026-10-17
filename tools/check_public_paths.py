"""Reject workstation paths in tracked public text without printing their values."""
from pathlib import Path
import re
import json
from xml.sax.saxutils import escape
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL_PATH = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:(?:\\+|/)(?!/)|/(?:Users|home)/[^/\s\"<>]+/"
)


def path_lines(text: str) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1)
            if LOCAL_PATH.search(line)]


def scan_file(path: Path) -> list[int]:
    if path.name == ".env" or path.name.startswith(".env."):
        return []
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        return []
    return path_lines(data.decode("utf-8", errors="replace"))


def portable_netlist_text(text: str, source: str) -> str:
    """Change only native export source metadata, retaining all graph records."""
    if LOCAL_PATH.search(source) or source.startswith("/") or ".." in Path(source).parts:
        raise ValueError("Export source must be repository relative")
    if "<source>" in text:
        pattern = r"(<design>\s*)<source>[^<]*</source>"
        replacement = "<source>" + escape(source) + "</source>"
    else:
        pattern = r'(\(design\s*)\(source\s+"(?:[^"\\]|\\.)*"\)'
        replacement = "(source " + json.dumps(source) + ")"
    result, count = re.subn(pattern, lambda match: match.group(1) + replacement, text)
    if count != 1:
        raise ValueError("Expected exactly one native design source field")
    return result


def main() -> int:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    failures = []
    for name in names:
        if not name or not (ROOT / name).is_file():
            continue
        for line in scan_file(ROOT / name):
            failures.append(f"{name}:{line}: workstation path must be portable")
    print("PUBLIC PATH CHECK " + ("FAILED" if failures else "PASSED"))
    for failure in failures:
        print(failure)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
