"""Train-only preprocessing for shot-make model features."""

from dataclasses import dataclass
from math import sqrt
from typing import Any

NUMERIC_FEATURES = ("shot_distance", "period", "seconds_remaining")
UNKNOWN_CATEGORY_INDEX = 0


@dataclass(frozen=True)
class ModelInput:
    """One model-ready shot row, with category IDs and scaled numeric features."""

    player_index: int
    shot_zone_index: int
    numeric_features: tuple[float, float, float]
    is_home: float
    target: float | None


@dataclass(frozen=True)
class ShotPreprocessor:
    """Vocabularies and numeric statistics fitted only from training rows."""

    player_vocab: dict[int, int]
    shot_zone_vocab: dict[str, int]
    numeric_means: dict[str, float]
    numeric_scales: dict[str, float]

    @classmethod
    def fit(cls, training_rows: list[dict[str, Any]]) -> ShotPreprocessor:
        """Fit category vocabularies and scaling values from training data only."""
        if not training_rows:
            raise ValueError("Cannot fit preprocessing on an empty training dataset")

        player_vocab = {
            player_id: index
            for index, player_id in enumerate(
                sorted({int(row["player_id"]) for row in training_rows}),
                start=1,
            )
        }
        shot_zone_vocab = {
            shot_zone: index
            for index, shot_zone in enumerate(
                sorted({str(row["shot_zone"]) for row in training_rows}),
                start=1,
            )
        }
        numeric_means = {
            feature: sum(float(row[feature]) for row in training_rows) / len(training_rows)
            for feature in NUMERIC_FEATURES
        }
        numeric_scales = {
            feature: _population_scale(training_rows, feature, numeric_means[feature])
            for feature in NUMERIC_FEATURES
        }
        return cls(player_vocab, shot_zone_vocab, numeric_means, numeric_scales)

    def transform(self, rows: list[dict[str, Any]]) -> list[ModelInput]:
        """Transform rows without updating the fitted vocabularies or statistics."""
        transformed: list[ModelInput] = []
        for row in rows:
            numeric_features = tuple(
                (float(row[feature]) - self.numeric_means[feature]) / self.numeric_scales[feature]
                for feature in NUMERIC_FEATURES
            )
            transformed.append(
                ModelInput(
                    player_index=self.player_vocab.get(
                        int(row["player_id"]), UNKNOWN_CATEGORY_INDEX
                    ),
                    shot_zone_index=self.shot_zone_vocab.get(
                        str(row["shot_zone"]), UNKNOWN_CATEGORY_INDEX
                    ),
                    numeric_features=numeric_features,
                    is_home=float(bool(row["is_home"])),
                    target=float(row["shot_made"]) if "shot_made" in row else None,
                )
            )
        return transformed


def _population_scale(rows: list[dict[str, Any]], feature: str, mean: float) -> float:
    variance = sum((float(row[feature]) - mean) ** 2 for row in rows) / len(rows)
    return sqrt(variance) or 1.0
