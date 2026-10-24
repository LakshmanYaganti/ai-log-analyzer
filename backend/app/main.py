from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(
    title="AI Log Analyzer",
    description="Upload a log file and get severity counts, top repeated "
    "errors, and rule-based explanations for each error pattern.",
    version="1.0.0",
)

# Allow the static frontend (and local tools) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
