"""Deterministic question interpretation; no LLM-generated SQL."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionPlan:
    shot_zone: str | None
    default_last_n_games: int | None
    coverage_question: bool


def plan_question(question: str, requested_last_n_games: int | None) -> QuestionPlan:
    lowered = question.lower()
    zone = None
    if "near the rim" in lowered or "rim" in lowered:
        zone = "Restricted Area"
    elif "three" in lowered or "3-point" in lowered or "3 point" in lowered:
        zone = "Above the Break 3"
    elif "mid-range" in lowered or "midrange" in lowered:
        zone = "Mid-Range"
    return QuestionPlan(
        shot_zone=zone,
        default_last_n_games=10 if "recent" in lowered and requested_last_n_games is None else None,
        coverage_question="coverage" in lowered or "drop" in lowered,
    )
