"""Versioned state-dictionary artifacts for shot-make inference."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from basketball_api.model import ShotMakeModel
from basketball_api.preprocessing import ShotPreprocessor
from basketball_api.training import EvaluationMetrics

MODEL_VERSION = "shot-make-v1"


def save_artifact(
    model: ShotMakeModel,
    preprocessor: ShotPreprocessor,
    metrics: EvaluationMetrics,
    *,
    state_path: Path,
    metadata_path: Path,
    data_range: dict[str, str],
) -> None:
    """Save weights separately from JSON metadata that explains their inputs."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), state_path)
    metadata = {
        "model_version": MODEL_VERSION,
        "feature_order": [
            "player",
            "shot_zone",
            "shot_distance",
            "period",
            "seconds_remaining",
            "is_home",
        ],
        "player_vocab": {str(key): value for key, value in preprocessor.player_vocab.items()},
        "shot_zone_vocab": preprocessor.shot_zone_vocab,
        "numeric_means": preprocessor.numeric_means,
        "numeric_scales": preprocessor.numeric_scales,
        "data_range": data_range,
        "metrics": asdict(metrics),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def load_artifact(
    state_path: Path, metadata_path: Path
) -> tuple[ShotMakeModel, ShotPreprocessor, dict[str, Any]]:
    """Reload weights and their preprocessing contract without pickling a model class."""
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    preprocessor = ShotPreprocessor(
        player_vocab={int(key): int(value) for key, value in metadata["player_vocab"].items()},
        shot_zone_vocab={
            str(key): int(value) for key, value in metadata["shot_zone_vocab"].items()
        },
        numeric_means={str(key): float(value) for key, value in metadata["numeric_means"].items()},
        numeric_scales={
            str(key): float(value) for key, value in metadata["numeric_scales"].items()
        },
    )
    model = ShotMakeModel(
        player_vocab_size=len(preprocessor.player_vocab) + 1,
        shot_zone_vocab_size=len(preprocessor.shot_zone_vocab) + 1,
    )
    model.load_state_dict(torch.load(state_path, map_location="cpu", weights_only=True))
    model.eval()
    return model, preprocessor, metadata


def predict_probability(
    model: ShotMakeModel,
    preprocessor: ShotPreprocessor,
    row: dict[str, Any],
) -> float:
    """Return a valid probability for a fully specified shot scenario."""
    transformed = preprocessor.transform([row])[0]
    with torch.no_grad():
        logit = model(
            torch.tensor([transformed.player_index], dtype=torch.long),
            torch.tensor([transformed.shot_zone_index], dtype=torch.long),
            torch.tensor([transformed.numeric_features], dtype=torch.float32),
            torch.tensor([transformed.is_home], dtype=torch.float32),
        )
    return float(torch.sigmoid(logit).item())
