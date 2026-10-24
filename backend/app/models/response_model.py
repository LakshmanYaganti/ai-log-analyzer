from pydantic import BaseModel


class SeverityCounts(BaseModel):
    INFO: int = 0
    WARNING: int = 0
    ERROR: int = 0
    CRITICAL: int = 0


class TopError(BaseModel):
    error: str
    count: int
    explanation: str


class AnalysisResponse(BaseModel):
    total_lines: int
    severity: SeverityCounts
    error_rate: float
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    top_errors: list[TopError] = []
