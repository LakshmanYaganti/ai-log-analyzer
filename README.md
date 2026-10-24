# AI Log Analyzer

Upload a log file, get an instant health report: severity counts, error rate, the time window covered, the most repeated errors — and a plain-English explanation of what each error pattern usually means and how to fix it.

The "AI" here is a **rule-based explanation engine**: deterministic, offline, and free. No API key, no network call, no per-request cost — explanations are generated from curated patterns for the failures that actually show up in production logs (database/connection failures, timeouts, auth and permission problems, OOM, disk-full, SSL errors, rate limits, and more).

## Features

- **Severity breakdown** — every line classified as INFO / WARNING / ERROR / CRITICAL
- **Error rate** — (ERROR + CRITICAL) as a percentage of all lines
- **Top repeated errors** — the 5 most frequent problem lines, ranked by count
- **Rule-based explanations** — each top error comes with a likely cause and concrete next steps
- **Time window** — first and last timestamps found in the file
- **Upload validation** — empty files, binary files, and files over 5 MB are rejected with a clear error
- **Zero-config** — works fully offline; Docker Compose brings up the whole stack in one command

## Architecture

```
┌────────────────┐   POST /analyze    ┌──────────────────────────────┐
│  Frontend      │ ─────────────────▶ │  Backend (FastAPI)           │
│  static HTML   │   multipart upload │                              │
│  nginx :3000   │ ◀───────────────── │  api/routes.py  (validation) │
└────────────────┘   JSON response    │  services/log_analyzer.py    │
                                      │  services/ai_explainer.py    │
                                      └──────────────────────────────┘
```

## Tech stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| Frontend | Single-page HTML/CSS/JS, nginx     |
| Infra    | Docker, Docker Compose              |
| Tests    | pytest, FastAPI TestClient          |

## Quick start

### With Docker Compose (recommended)

```bash
git clone https://github.com/LakshmanYaganti/ai-log-analyzer.git
cd ai-log-analyzer
docker compose up --build
```

Then open **http://localhost:3000**, drop in `sample.log` from this repo, and click **Analyze Logs**.

### Locally (no Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs (Swagger UI): http://localhost:8000/docs — and open `frontend/index.html` in a browser (it calls `http://localhost:8000/analyze`).

## API

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /analyze`

Multipart upload, form field `file` (plain-text log, max 5 MB).

```bash
curl -X POST http://localhost:8000/analyze -F "file=@sample.log"
```

Response for the included `sample.log`:

```json
{
  "total_lines": 5,
  "severity": { "INFO": 1, "WARNING": 1, "ERROR": 3, "CRITICAL": 0 },
  "error_rate": 60.0,
  "first_timestamp": "2026-03-03 10:23:45",
  "last_timestamp": "2026-03-03 10:24:10",
  "top_errors": [
    {
      "error": "2026-03-03 10:23:45 ERROR Database connection failed",
      "count": 1,
      "explanation": "Connectivity / database problem. The application cannot reach the database or an upstream service. Check that the service is up, the host/port are correct, and there is no firewall or DNS issue."
    },
    {
      "error": "2026-03-03 10:23:50 ERROR Timeout occurred",
      "count": 1,
      "explanation": "Timeout. A request or query took longer than the allowed limit. Possible causes: network latency, an overloaded downstream service, or a slow query. Check downstream health before raising the timeout."
    },
    {
      "error": "2026-03-03 10:24:10 ERROR Unable to connect to authentication service",
      "count": 1,
      "explanation": "Authentication failure. Credentials are missing, wrong, or expired. Verify the API key / service account, check token expiry, and confirm the account is not locked."
    }
  ]
}
```

Errors: `400` for an empty or binary file, `413` for a file over the size limit.

**How severity is counted:** each line is counted exactly once, under its highest severity (CRITICAL > ERROR > WARNING). Lines matching none of those count as INFO.

## How the explanation engine works

`backend/app/services/ai_explainer.py` holds an ordered list of rules — `(keywords, explanation)` — covering:

- SSL / certificate problems
- Rate limits (429, throttling)
- Missing files
- Authentication failures (401, expired tokens)
- Permission / access denied (403)
- Database & connection failures
- Timeouts
- Memory / OOM
- Disk / storage full
- Null / `NoneType` errors

The first matching rule wins, so specific patterns sit above general ones; anything unmatched gets a sensible "how to investigate" default.

**Extending it:** add one entry to `RULES` in `ai_explainer.py` and a case in `tests/test_api.py`. No other code changes are needed.

An optional LLM-backed explainer can be layered on later: `backend/app/core/config.py` already reads an optional key and model name (`gpt-4o-mini`) from the environment. The core flow never depends on it.

## Project structure

```
ai-log-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app: CORS, /health, router
│   │   ├── api/routes.py         # POST /analyze + upload validation
│   │   ├── core/config.py        # Optional env-based settings
│   │   ├── models/response_model.py  # AnalysisResponse schema
│   │   └── services/
│   │       ├── log_analyzer.py   # Severity counts, error rate, top errors
│   │       └── ai_explainer.py   # Rule-based explanation engine
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html                # Upload UI + rendered report
│   └── Dockerfile                # nginx serving the page
├── tests/
│   ├── conftest.py
│   └── test_api.py               # Unit + API tests
├── docker-compose.yml            # Backend :8000, frontend :3000
├── sample.log                    # Example log to try
└── test.log                      # Second example log
```

## Testing

```bash
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv pytest httpx
pytest tests/
```

Unit tests cover severity counts, timestamp extraction, top-error ranking, and every explanation rule; API tests cover `/health`, `/analyze` on `sample.log`, and the empty/binary upload rejections.

## Security notes

- **No API key is required** and none is shipped with this repo. `.env` is gitignored; `backend/.env.example` shows the optional variables with placeholder values only.
- Uploads are size-capped (5 MB, configurable via `MAX_UPLOAD_SIZE_MB`) and binary content is rejected.
- Log lines are rendered in the frontend as text, never as HTML.

## License

MIT — see [LICENSE](LICENSE). © 2026 Lakshman Sai Yaganti.
