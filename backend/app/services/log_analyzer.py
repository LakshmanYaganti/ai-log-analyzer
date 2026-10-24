"""Core log analysis.

Pure functions over a list of log lines — no I/O, no framework —
so the analysis is unit-testable without FastAPI.
"""

import re
from collections import Counter

from .ai_explainer import explain_error

# Timestamp as written by the original analyzer, e.g. "2026-03-03 10:23:45"
# (also tolerates a 'T' separator and fractional seconds).
TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")

# Checked in priority order: a line is counted exactly once, under its
# highest severity. Lines matching none of these count as INFO
# (documented behaviour kept from the original implementation).
_SEVERITIES = ("CRITICAL", "ERROR", "WARNING")


def _severity_of(line: str) -> str:
    upper = line.upper()
    for severity in _SEVERITIES:
        if severity in upper:
            return severity
    return "INFO"


def _is_problem(line: str) -> bool:
    return _severity_of(line) in ("ERROR", "CRITICAL")


def analyze_logs(lines: list[str]) -> dict:
    """Analyze log lines and return a dict matching AnalysisResponse.

    Returns total line count, per-severity counts, the error rate
    (ERROR + CRITICAL as a percentage of all lines), the first and
    last timestamps found, and the top 5 repeated problem lines,
    each with a rule-based explanation.
    """
    severity = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    problem_lines: list[str] = []
    timestamps: list[str] = []

    for line in lines:
        severity[_severity_of(line)] += 1
        if _is_problem(line):
            problem_lines.append(line)
        match = TIMESTAMP_RE.search(line)
        if match:
            timestamps.append(match.group())

    total = len(lines)
    problems = severity["ERROR"] + severity["CRITICAL"]
    error_rate = round((problems / total) * 100, 2) if total else 0.0

    top_errors = [
        {"error": error, "count": count, "explanation": explain_error(error)}
        for error, count in Counter(problem_lines).most_common(5)
    ]

    return {
        "total_lines": total,
        "severity": severity,
        "error_rate": error_rate,
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "top_errors": top_errors,
    }
