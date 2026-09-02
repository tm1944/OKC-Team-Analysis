import pytest
import torch

from basketball_api.model import (
    PLAYER_EMBEDDING_DIM,
    SHOT_ZONE_EMBEDDING_DIM,
    ShotMakeModel,
)


def test_shot_make_model_has_requested_architecture_and_output_shape() -> None:
    model = ShotMakeModel(player_vocab_size=5, shot_zone_vocab_size=4)

    logits = model(
        player_indices=torch.tensor([0, 1, 4]),
        shot_zone_indices=torch.tensor([0, 2, 3]),
        numeric_features=torch.tensor([[0.0, 1.0, -1.0], [0.5, 0.0, 1.5], [1.0, -1.0, 0.0]]),
        is_home=torch.tensor([1.0, 0.0, 1.0]),
    )

    assert model.player_embedding.embedding_dim == PLAYER_EMBEDDING_DIM == 8
    assert model.shot_zone_embedding.embedding_dim == SHOT_ZONE_EMBEDDING_DIM == 3
    assert model.hidden.in_features == 15
    assert model.hidden.out_features == 16
    assert logits.shape == (3,)


def test_shot_make_model_accepts_unknown_category_indices() -> None:
    model = ShotMakeModel(player_vocab_size=2, shot_zone_vocab_size=2)

    logits = model(
        player_indices=torch.tensor([0]),
        shot_zone_indices=torch.tensor([0]),
        numeric_features=torch.zeros((1, 3)),
        is_home=torch.ones((1, 1)),
    )

    assert logits.shape == (1,)


def test_shot_make_model_rejects_invalid_numeric_shape() -> None:
    model = ShotMakeModel(player_vocab_size=2, shot_zone_vocab_size=2)

    with pytest.raises(ValueError, match=r"numeric_features must have shape \[batch, 3\]"):
        model(
            player_indices=torch.tensor([0]),
            shot_zone_indices=torch.tensor([0]),
            numeric_features=torch.zeros((1, 2)),
            is_home=torch.ones(1),
        )
