from math import isclose

import pytest

from basketball_api.preprocessing import UNKNOWN_CATEGORY_INDEX, ShotPreprocessor


def _training_rows() -> list[dict[str, object]]:
    return [
        {
            "player_id": 10,
            "shot_zone": "Restricted Area",
            "shot_distance": 5.0,
            "period": 1,
            "seconds_remaining": 120,
            "is_home": True,
            "shot_made": True,
        },
        {
            "player_id": 20,
            "shot_zone": "Above the Break 3",
            "shot_distance": 15.0,
            "period": 3,
            "seconds_remaining": 180,
            "is_home": False,
            "shot_made": False,
        },
    ]


def test_preprocessor_fits_vocabs_and_scaling_on_training_data() -> None:
    preprocessor = ShotPreprocessor.fit(_training_rows())

    assert preprocessor.player_vocab == {10: 1, 20: 2}
    assert preprocessor.shot_zone_vocab == {"Above the Break 3": 1, "Restricted Area": 2}
    assert preprocessor.numeric_means == {
        "shot_distance": 10.0,
        "period": 2.0,
        "seconds_remaining": 150.0,
    }
    assert preprocessor.numeric_scales == {
        "shot_distance": 5.0,
        "period": 1.0,
        "seconds_remaining": 30.0,
    }


def test_preprocessor_uses_unknown_categories_and_does_not_refit() -> None:
    preprocessor = ShotPreprocessor.fit(_training_rows())
    validation_row = {
        "player_id": 999,
        "shot_zone": "Corner 3",
        "shot_distance": 110.0,
        "period": 4,
        "seconds_remaining": 0,
        "is_home": False,
        "shot_made": True,
    }

    transformed = preprocessor.transform([validation_row])[0]

    assert transformed.player_index == UNKNOWN_CATEGORY_INDEX
    assert transformed.shot_zone_index == UNKNOWN_CATEGORY_INDEX
    assert transformed.numeric_features == (20.0, 2.0, -5.0)
    assert transformed.is_home == 0.0
    assert transformed.target == 1.0
    assert preprocessor.numeric_means["shot_distance"] == 10.0


def test_preprocessor_handles_constant_numeric_training_feature() -> None:
    rows = _training_rows()
    for row in rows:
        row["period"] = 2

    preprocessor = ShotPreprocessor.fit(rows)

    assert preprocessor.numeric_scales["period"] == 1.0
    assert preprocessor.transform(rows)[0].numeric_features[1] == 0.0


def test_preprocessor_rejects_empty_training_data() -> None:
    with pytest.raises(ValueError, match="empty training dataset"):
        ShotPreprocessor.fit([])


def test_preprocessor_standardizes_training_rows() -> None:
    transformed = ShotPreprocessor.fit(_training_rows()).transform(_training_rows())

    assert isclose(sum(row.numeric_features[0] for row in transformed), 0.0)
