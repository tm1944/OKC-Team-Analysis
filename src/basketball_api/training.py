"""Deterministic training and evaluation for the shot-make model."""

import random
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from basketball_api.model import ShotMakeModel
from basketball_api.preprocessing import ModelInput, ShotPreprocessor

SEED = 42


@dataclass(frozen=True)
class EvaluationMetrics:
    accuracy: float
    roc_auc: float | None
    brier_score: float
    baseline_make_rate: float


@dataclass(frozen=True)
class TrainingResult:
    model: ShotMakeModel
    epochs_completed: int
    best_validation_loss: float


def set_seed(seed: int = SEED) -> None:
    """Set all relevant random seeds for repeatable local training."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def train_model(
    training_rows: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    preprocessor: ShotPreprocessor,
    *,
    max_epochs: int = 50,
    patience: int = 5,
    batch_size: int = 256,
    learning_rate: float = 0.001,
    seed: int = SEED,
) -> TrainingResult:
    """Train with BCE-with-logits and stop after stalled validation loss."""
    if not training_rows or not validation_rows:
        raise ValueError("Training and validation rows must both be nonempty")
    if max_epochs < 1 or patience < 1:
        raise ValueError("max_epochs and patience must be positive")

    set_seed(seed)
    model = ShotMakeModel(
        player_vocab_size=len(preprocessor.player_vocab) + 1,
        shot_zone_vocab_size=len(preprocessor.shot_zone_vocab) + 1,
    )
    training_inputs = preprocessor.transform(training_rows)
    validation_inputs = preprocessor.transform(validation_rows)
    train_loader = DataLoader(
        _dataset(training_inputs),
        batch_size=batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
    )
    validation_tensors = _dataset(validation_inputs).tensors
    loss_function = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    best_state: dict[str, torch.Tensor] | None = None
    best_validation_loss = float("inf")
    epochs_without_improvement = 0
    epochs_completed = 0
    for _epoch in range(max_epochs):
        epochs_completed += 1
        model.train()
        for player_ids, zone_ids, numeric, home, targets in train_loader:
            optimizer.zero_grad()
            loss = loss_function(model(player_ids, zone_ids, numeric, home), targets)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            validation_logits = model(*validation_tensors[:4])
            validation_loss = loss_function(validation_logits, validation_tensors[4]).item()
        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_state = {
                name: value.detach().clone() for name, value in model.state_dict().items()
            }
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                break

    if best_state is None:  # Defensive: a nonempty validation set always establishes a best state.
        raise RuntimeError("Training did not produce a model state")
    model.load_state_dict(best_state)
    return TrainingResult(model, epochs_completed, best_validation_loss)


def evaluate_model(
    model: ShotMakeModel,
    rows: list[dict[str, Any]],
    preprocessor: ShotPreprocessor,
) -> EvaluationMetrics:
    """Evaluate a saved model with probabilities and a make-rate baseline."""
    inputs = preprocessor.transform(rows)
    tensors = _dataset(inputs).tensors
    model.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(model(*tensors[:4])).numpy()
    targets = tensors[4].numpy()
    baseline = float(targets.mean())
    roc_auc = float(roc_auc_score(targets, probabilities)) if len(set(targets)) == 2 else None
    return EvaluationMetrics(
        accuracy=float(accuracy_score(targets, probabilities >= 0.5)),
        roc_auc=roc_auc,
        brier_score=float(brier_score_loss(targets, probabilities)),
        baseline_make_rate=baseline,
    )


def _dataset(inputs: list[ModelInput]) -> TensorDataset:
    if not inputs or any(row.target is None for row in inputs):
        raise ValueError("Model training and evaluation require nonempty labeled rows")
    return TensorDataset(
        torch.tensor([row.player_index for row in inputs], dtype=torch.long),
        torch.tensor([row.shot_zone_index for row in inputs], dtype=torch.long),
        torch.tensor([row.numeric_features for row in inputs], dtype=torch.float32),
        torch.tensor([row.is_home for row in inputs], dtype=torch.float32),
        torch.tensor([row.target for row in inputs], dtype=torch.float32),
    )
