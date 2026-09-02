"""PyTorch model architecture for shot-make probability estimation."""

import torch
from torch import nn

PLAYER_EMBEDDING_DIM = 8
SHOT_ZONE_EMBEDDING_DIM = 3
NUMERIC_FEATURE_COUNT = 3


class ShotMakeModel(nn.Module):
    """Small binary classifier that returns one logit per shot scenario."""

    def __init__(self, *, player_vocab_size: int, shot_zone_vocab_size: int) -> None:
        super().__init__()
        if player_vocab_size < 1 or shot_zone_vocab_size < 1:
            raise ValueError("Vocabulary sizes must include the unknown category at index zero")

        self.player_embedding = nn.Embedding(player_vocab_size, PLAYER_EMBEDDING_DIM)
        self.shot_zone_embedding = nn.Embedding(shot_zone_vocab_size, SHOT_ZONE_EMBEDDING_DIM)
        input_size = PLAYER_EMBEDDING_DIM + SHOT_ZONE_EMBEDDING_DIM + NUMERIC_FEATURE_COUNT + 1
        self.hidden = nn.Linear(input_size, 16)
        self.output = nn.Linear(16, 1)

    def forward(
        self,
        player_indices: torch.Tensor,
        shot_zone_indices: torch.Tensor,
        numeric_features: torch.Tensor,
        is_home: torch.Tensor,
    ) -> torch.Tensor:
        """Return unbounded logits; training applies BCEWithLogitsLoss directly."""
        if player_indices.ndim != 1:
            raise ValueError("player_indices must have shape [batch]")
        batch_size = player_indices.shape[0]
        if shot_zone_indices.shape != (batch_size,):
            raise ValueError("shot_zone_indices must have shape [batch]")
        if numeric_features.shape != (batch_size, NUMERIC_FEATURE_COUNT):
            raise ValueError("numeric_features must have shape [batch, 3]")
        if is_home.shape not in {(batch_size,), (batch_size, 1)}:
            raise ValueError("is_home must have shape [batch] or [batch, 1]")

        embedded_players = self.player_embedding(player_indices)
        embedded_zones = self.shot_zone_embedding(shot_zone_indices)
        home_feature = is_home.reshape(batch_size, 1).to(dtype=numeric_features.dtype)
        combined_features = torch.cat(
            (embedded_players, embedded_zones, numeric_features, home_feature),
            dim=1,
        )
        hidden_features = torch.relu(self.hidden(combined_features))
        return self.output(hidden_features).squeeze(1)
