from fastapi import APIRouter, File, HTTPException, UploadFile

from ..core.config import MAX_UPLOAD_SIZE_MB
from ..models.response_model import AnalysisResponse
from ..services.log_analyzer import analyze_logs

router = APIRouter()

MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_log(file: UploadFile = File(...)):
    """Analyze an uploaded plain-text log file."""
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum size is {MAX_UPLOAD_SIZE_MB} MB.",
        )
    if b"\x00" in content:
        raise HTTPException(
            status_code=400,
            detail="File looks binary. Please upload a plain-text log file.",
        )

    text = content.decode("utf-8", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise HTTPException(
            status_code=400, detail="No readable log lines found in the file."
        )

    result = analyze_logs(lines)
    return AnalysisResponse(**result)
