# ruff: noqa: E501
import psycopg
from fastapi import Depends, FastAPI, HTTPException

from basketball_api.analysis import AmbiguousPlayerError, AnalysisError, DatabaseAnalysisService
from basketball_api.config import get_settings
from basketball_api.schemas import AnalyzePlayerRequest

app = FastAPI(
    title="Basketball Decision Support API",
    version="0.1.0",
    description="Grounded player analysis from NBA data, a shot model, and retrieval.",
)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    settings = get_settings()
    try:
        with psycopg.connect(settings.database_url) as conn:
            extension = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()
            migrations = conn.execute("SELECT count(*) FROM schema_migrations").fetchone()
        if extension is None or migrations is None or not settings.model_artifact_path.exists():
            raise RuntimeError("required dependency is unavailable")
    except Exception as error:
        raise HTTPException(status_code=503, detail={"error": "not_ready", "message": str(error)}) from error
    return {"status": "ok"}


def get_analysis_service() -> DatabaseAnalysisService:
    return DatabaseAnalysisService(get_settings())


@app.post("/analyze-player", tags=["analysis"])
def analyze_player(
    request: AnalyzePlayerRequest,
    service: DatabaseAnalysisService = Depends(get_analysis_service),  # noqa: B008
) -> dict[str, object]:
    try:
        return service.analyze(request)
    except AmbiguousPlayerError as error:
        raise HTTPException(status_code=409, detail={"error": "ambiguous_player", "candidates": error.candidates}) from error
    except AnalysisError as error:
        raise HTTPException(status_code=error.status_code, detail={"error": str(error)}) from error
