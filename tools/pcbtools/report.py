"""Machine-readable findings with fail-closed aggregation."""
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

STATUSES = {"PASS", "FAIL", "NOT_RUN", "NOT_APPLICABLE"}
@dataclass
class Finding:
    rule_id: str
    status: str
    message: str
    details: dict = field(default_factory=dict)
    def __post_init__(self):
        if self.status not in STATUSES: raise ValueError("Invalid finding status")
        if self.status == "NOT_APPLICABLE" and not self.details.get("reason"):
            raise ValueError("NOT_APPLICABLE requires a configured reason")

@dataclass
class RunReport:
    project_id: str
    findings: list[Finding]
    evidence: dict
    release_status: str = "NOT_EVALUATED"

def exit_code(report: RunReport) -> int:
    if not report.findings or any(f.status in {"FAIL", "NOT_RUN"} for f in report.findings): return 1
    return 2 if report.release_status == "BLOCKED" else 0

def write_report(report: RunReport, path: Path) -> None:
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
