from pathlib import Path

from basketball_api.artifacts import load_artifact, predict_probability, save_artifact
from basketball_api.preprocessing import ShotPreprocessor
from basketball_api.training import EvaluationMetrics, evaluate_model, train_model


def _rows(start: int, count: int) -> list[dict[str, object]]:
    return [
        {
            "player_id": 10 if index % 2 else 20,
            "shot_zone": "Restricted Area" if index % 2 else "Above the Break 3",
            "shot_distance": float(2 + index % 20),
            "period": 1 + index % 4,
            "seconds_remaining": 20 + index * 5,
            "is_home": bool(index % 2),
            "shot_made": bool(index % 3),
            "game_id": start + index,
            "game_date": f"2024-10-{index + 1:02}",
        }
        for index in range(count)
    ]


def test_training_is_deterministic_and_returns_valid_metrics() -> None:
    training_rows = _rows(1, 20)
    validation_rows = _rows(21, 8)
    preprocessor = ShotPreprocessor.fit(training_rows)

    first = train_model(training_rows, validation_rows, preprocessor, max_epochs=4, patience=2)
    second = train_model(training_rows, validation_rows, preprocessor, max_epochs=4, patience=2)
    first_metrics = evaluate_model(first.model, validation_rows, preprocessor)

    assert first.epochs_completed <= 4
    assert first.best_validation_loss == second.best_validation_loss
    assert first_metrics.accuracy >= 0.0
    assert first_metrics.roc_auc is not None
    assert 0.0 <= first_metrics.brier_score <= 1.0
    assert 0.0 <= first_metrics.baseline_make_rate <= 1.0


def test_state_dictionary_round_trip_preserves_prediction(tmp_path: Path) -> None:
    training_rows = _rows(1, 20)
    validation_rows = _rows(21, 8)
    preprocessor = ShotPreprocessor.fit(training_rows)
    result = train_model(training_rows, validation_rows, preprocessor, max_epochs=2)
    metrics = EvaluationMetrics(0.5, 0.5, 0.25, 0.5)
    state_path = tmp_path / "shot_model.pt"
    metadata_path = tmp_path / "shot_model.json"

    expected_probability = predict_probability(result.model, preprocessor, validation_rows[0])
    save_artifact(
        result.model,
        preprocessor,
        metrics,
        state_path=state_path,
        metadata_path=metadata_path,
        data_range={"start": "2024-10-01", "end": "2024-12-01"},
    )
    loaded_model, loaded_preprocessor, metadata = load_artifact(state_path, metadata_path)
    actual_probability = predict_probability(loaded_model, loaded_preprocessor, validation_rows[0])

    assert 0.0 <= actual_probability <= 1.0
    assert actual_probability == expected_probability
    assert metadata["model_version"] == "shot-make-v1"
    assert metadata["feature_order"][0] == "player"
