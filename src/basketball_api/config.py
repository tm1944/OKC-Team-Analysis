from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://basketball:basketball@localhost:5433/basketball"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_generation_model: str = "gpt-5.4-mini"
    nba_season: str = "2024-25"
    nba_team_id: int = 1_610_612_760
    nba_team_abbreviation: str = "OKC"
    model_artifact_path: Path = Field(default=Path("artifacts/shot_model.pt"))
    model_metadata_path: Path = Field(default=Path("artifacts/shot_model.json"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
