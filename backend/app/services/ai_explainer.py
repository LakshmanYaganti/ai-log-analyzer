"""Rule-based error explanation engine.

Maps a log line to a plain-English explanation using keyword rules.
It is deliberately offline and deterministic: no API key, no network
call, no cost. Rules are checked in order and the first match wins,
so keep more specific patterns above more general ones.

To extend it, add an entry to ``RULES``: (keywords, explanation).
"""

# (keywords, explanation) — first match wins.
RULES = [
    (
        ("ssl", "certificate", "certverify", "handshake"),
        "SSL/TLS problem. The certificate may be expired, self-signed, or "
        "issued for a different host. Verify the certificate chain and the "
        "system clock, and check whether a proxy is intercepting TLS.",
    ),
    (
        ("rate limit", "too many requests", "429", "throttl", "quota exceeded"),
        "Rate limit hit. The service is rejecting requests because they are "
        "arriving too fast. Add backoff/retry with jitter, batch requests, "
        "or ask the provider to raise the quota.",
    ),
    (
        ("no such file", "file not found", "filenotfound", "not found on disk"),
        "A required file or path does not exist. Check the configured path, "
        "working directory, mounted volumes, and whether an earlier step "
        "was supposed to create the file.",
    ),
    (
        ("authentication", "unauthorized", "401", "invalid credentials",
         "invalid token", "token expired", "login failed"),
        "Authentication failure. Credentials are missing, wrong, or expired. "
        "Verify the API key / service account, check token expiry, and "
        "confirm the account is not locked.",
    ),
    (
        ("permission", "access denied", "forbidden", "403", "not authorized",
         "operation not permitted"),
        "Permission problem. The process or user does not have access to a "
        "required resource. Verify file/API permissions, user roles, and "
        "ownership of the target resource.",
    ),
    (
        ("database", "connection", "connect", "unreachable", "refused",
         "could not resolve", "name resolution"),
        "Connectivity / database problem. The application cannot reach the "
        "database or an upstream service. Check that the service is up, the "
        "host/port are correct, and there is no firewall or DNS issue.",
    ),
    (
        ("timeout", "timed out", "deadline exceeded"),
        "Timeout. A request or query took longer than the allowed limit. "
        "Possible causes: network latency, an overloaded downstream "
        "service, or a slow query. Check downstream health before raising "
        "the timeout.",
    ),
    (
        ("out of memory", "oom", "memoryerror", "memory"),
        "Memory pressure. The process is using more RAM than allowed and "
        "may be killed by the OS (OOM). Look for unbounded data loads, "
        "memory leaks, or raise the container/host memory limit.",
    ),
    (
        ("no space left", "disk", "storage", "errno 28"),
        "Disk / storage problem. The disk may be full or unwritable. Check "
        "free space, log rotation, temp directories, and storage quotas.",
    ),
    (
        ("nullpointer", "nonetype", "null", "none"),
        "A null/None value was used where a real object was expected. "
        "Usually caused by a failed lookup, missing initialisation, or an "
        "upstream call returning nothing. Add a guard where the value is "
        "produced, not just where it crashes.",
    ),
]

DEFAULT_EXPLANATION = (
    "No known pattern matched this error. Look at the surrounding log "
    "lines for the first occurrence, check recent deploys or config "
    "changes, and search the full message in the service's issue tracker."
)


def explain_error(error: str | None) -> str:
    """Return a plain-English explanation for one error log line."""
    if not error:
        return DEFAULT_EXPLANATION
    text = error.lower()
    for keywords, explanation in RULES:
        if any(keyword in text for keyword in keywords):
            return explanation
    return DEFAULT_EXPLANATION
