"""Stable request and response contracts for the public API."""

from pydantic import BaseModel, Field


class AnalysisFilters(BaseModel):
    last_n_games: int | None = Field(default=None, ge=1, le=82)


class ShotContext(BaseModel):
    shot_distance_ft: float = Field(ge=0, le=94)
    shot_zone: str = Field(min_length=1, max_length=50)
    quarter: int = Field(ge=1, le=10)
    seconds_remaining: int = Field(ge=0, le=720)
    is_home: bool


class AnalyzePlayerRequest(BaseModel):
    player: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=1000)
    filters: AnalysisFilters | None = None
    shot_context: ShotContext | None = None
