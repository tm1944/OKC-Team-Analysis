# ruff: noqa: E501
"""Database-backed orchestration for player decision-support responses."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from basketball_api.artifacts import load_artifact, predict_probability
from basketball_api.config import Settings
from basketball_api.openai_clients import OpenAIEmbedder, OpenAIGenerator
from basketball_api.planner import plan_question
from basketball_api.rag import retrieve
from basketball_api.schemas import AnalyzePlayerRequest


class AnalysisError(Exception):
    status_code = 500


class NotFoundError(AnalysisError):
    status_code = 404


class AmbiguousPlayerError(AnalysisError):
    status_code = 409

    def __init__(self, candidates: list[str]) -> None:
        super().__init__("Player name is ambiguous")
        self.candidates = candidates


class DatabaseAnalysisService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, request: AnalyzePlayerRequest) -> dict[str, Any]:
        with psycopg.connect(self.settings.database_url, row_factory=dict_row) as conn:
            player = self._resolve_player(conn, request.player)
            plan = plan_question(request.question, request.filters.last_n_games if request.filters else None)
            last_n_games = request.filters.last_n_games if request.filters else plan.default_last_n_games
            statistics = self._statistics(conn, int(player["id"]), plan.shot_zone, last_n_games)
            evidence: list[dict[str, Any]] = []
            analysis = "OpenAI is not configured; structured statistics are returned without generated prose."
            if self.settings.openai_api_key:
                embedder = OpenAIEmbedder(self.settings.openai_api_key, self.settings.openai_embedding_model)
                chunks = retrieve(conn, request.question, embedder)
                evidence = [
                    {"evidence_id": item.evidence_id, "document_id": item.document_id, "content": item.content,
                     "similarity": item.similarity}
                    for item in chunks
                ]
                analysis = OpenAIGenerator(
                    self.settings.openai_api_key, self.settings.openai_generation_model
                ).generate(request.question, statistics, chunks)
            prediction: dict[str, Any] = {"status": "not_requested"}
            if request.shot_context:
                model, preprocessor, metadata = load_artifact(
                    self.settings.model_artifact_path, self.settings.model_metadata_path
                )
                scenario = {
                    "player_id": player["id"], "shot_zone": request.shot_context.shot_zone,
                    "shot_distance": request.shot_context.shot_distance_ft,
                    "period": request.shot_context.quarter,
                    "seconds_remaining": request.shot_context.seconds_remaining,
                    "is_home": request.shot_context.is_home,
                }
                prediction = {"status": "ok", "probability": predict_probability(model, preprocessor, scenario),
                              "scenario": request.shot_context.model_dump(), "model_version": metadata["model_version"]}
            limitations = ["This dataset has no possession-level defensive-coverage labels."] if plan.coverage_question else []
            return {"player": player, "question": request.question, "filters_applied": {"last_n_games": last_n_games, "shot_zone": plan.shot_zone}, "statistics": statistics, "model_prediction": prediction, "retrieved_evidence": evidence, "generated_analysis": analysis, "limitations": limitations}

    @staticmethod
    def _resolve_player(conn: Any, name: str) -> dict[str, Any]:
        rows = conn.execute("SELECT id, nba_player_id, first_name || ' ' || last_name AS name FROM players WHERE lower(first_name || ' ' || last_name) = lower(%s)", (name.strip(),)).fetchall()
        if not rows:
            raise NotFoundError("Player not found")
        if len(rows) > 1:
            raise AmbiguousPlayerError([str(row["name"]) for row in rows])
        return dict(rows[0])

    @staticmethod
    def _statistics(conn: Any, player_id: int, zone: str | None, last_n_games: int | None) -> dict[str, Any]:
        rows = conn.execute("SELECT s.shot_made, s.shot_type FROM shots s JOIN games g ON g.id=s.game_id WHERE s.player_id=%s ORDER BY g.game_date DESC, s.id DESC", (player_id,)).fetchall()
        if last_n_games:
            rows = rows[:last_n_games * 30]
        if zone:
            rows = [row for row in rows if row["shot_type"] == zone]
        attempts = len(rows)
        makes = sum(bool(row["shot_made"]) for row in rows)
        return {"attempts": attempts, "makes": makes, "field_goal_percentage": makes / attempts if attempts else None, "zone": zone}
