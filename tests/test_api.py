"""Tests for the AI Log Analyzer.

Unit tests cover the pure analysis/explainer functions and always run.
API tests use FastAPI's TestClient and are skipped automatically if
httpx (a TestClient dependency) is not installed.
"""

from pathlib import Path

import pytest

from app.services.ai_explainer import explain_error
from app.services.log_analyzer import analyze_logs

REPO_ROOT = Path(__file__).resolve().parent.parent

SAMPLE_LINES = [
    "2026-03-03 10:23:45 ERROR Database connection failed",
    "2026-03-03 10:23:46 INFO Retrying connection",
    "2026-03-03 10:23:50 ERROR Timeout occurred",
    "2026-03-03 10:24:01 WARNING Disk space low",
    "2026-03-03 10:24:10 ERROR Unable to connect to authentication service",
]


# ------------------------- unit: analyze_logs -------------------------

def test_severity_counts_on_sample_lines():
    result = analyze_logs(SAMPLE_LINES)
    assert result["total_lines"] == 5
    assert result["severity"] == {
        "INFO": 1,
        "WARNING": 1,
        "ERROR": 3,
        "CRITICAL": 0,
    }
    assert result["error_rate"] == 60.0


def test_timestamps_extracted():
    result = analyze_logs(SAMPLE_LINES)
    assert result["first_timestamp"] == "2026-03-03 10:23:45"
    assert result["last_timestamp"] == "2026-03-03 10:24:10"


def test_top_errors_ranked_and_explained():
    lines = SAMPLE_LINES + [SAMPLE_LINES[0], SAMPLE_LINES[0]]
    result = analyze_logs(lines)
    assert result["top_errors"][0]["error"] == SAMPLE_LINES[0]
    assert result["top_errors"][0]["count"] == 3
    assert result["top_errors"][0]["explanation"]  # non-empty


def test_critical_counts_as_problem_and_unrecognized_is_info():
    result = analyze_logs(
        ["CRITICAL System shutting down", "just a plain message line"]
    )
    assert result["severity"]["CRITICAL"] == 1
    assert result["severity"]["INFO"] == 1
    assert result["error_rate"] == 50.0
    assert result["top_errors"][0]["error"] == "CRITICAL System shutting down"


def test_analyze_empty_input():
    result = analyze_logs([])
    assert result["total_lines"] == 0
    assert result["error_rate"] == 0.0
    assert result["first_timestamp"] is None
    assert result["top_errors"] == []


def test_analyze_sample_log_file():
    lines = [
        line
        for line in (REPO_ROOT / "sample.log").read_text().splitlines()
        if line.strip()
    ]
    result = analyze_logs(lines)
    assert result["severity"]["ERROR"] == 3
    assert result["total_lines"] == 5


# ------------------------- unit: explain_error -------------------------

@pytest.mark.parametrize(
    "line,fragment",
    [
        ("ERROR Database connection failed", "database"),
        ("ERROR Timeout occurred", "Timeout"),
        ("ERROR Permission denied for user", "Permission"),
        ("ERROR Authentication failed for service account", "Authentication"),
        ("ERROR 'NoneType' object has no attribute 'id'", "None"),
        ("ERROR Out of memory: killed process", "Memory"),
        ("ERROR Disk space full on /var", "Disk"),
        ("ERROR sample.log: No such file or directory", "does not exist"),
        ("ERROR SSL certificate verify failed", "certificate"),
        ("ERROR 429 rate limit exceeded", "Rate limit"),
    ],
)
def test_explain_error_mappings(line, fragment):
    assert fragment.lower() in explain_error(line).lower()


def test_explain_error_default_and_empty():
    assert "No known pattern" in explain_error("ERROR something odd happened")
    assert explain_error("")  # never crashes, returns the default text
    assert explain_error(None)


# ------------------------- API: TestClient -------------------------

pytest.importorskip("httpx", reason="TestClient requires httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_sample_log():
    with open(REPO_ROOT / "sample.log", "rb") as fh:
        response = client.post(
            "/analyze", files={"file": ("sample.log", fh, "text/plain")}
        )
    assert response.status_code == 200
    body = response.json()
    # The response is the AnalysisResponse itself, not wrapped.
    assert "analysis" not in body
    assert body["total_lines"] == 5
    assert body["severity"]["ERROR"] == 3
    assert body["severity"]["WARNING"] == 1
    assert body["error_rate"] == 60.0
    assert body["first_timestamp"] == "2026-03-03 10:23:45"
    assert body["last_timestamp"] == "2026-03-03 10:24:10"
    assert len(body["top_errors"]) == 3
    assert body["top_errors"][0]["explanation"]


def test_analyze_empty_file_rejected():
    response = client.post(
        "/analyze", files={"file": ("empty.log", b"", "text/plain")}
    )
    assert response.status_code == 400


def test_analyze_binary_file_rejected():
    response = client.post(
        "/analyze",
        files={"file": ("blob.log", b"\x00\x01\x02binary", "application/octet-stream")},
    )
    assert response.status_code == 400
