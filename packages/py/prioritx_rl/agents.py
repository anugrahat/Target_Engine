"""Simple baseline and contextual bandit agents for PrioriTx."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


def _dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _matvec(matrix: list[list[float]], vector: tuple[float, ...]) -> list[float]:
    return [sum(cell * value for cell, value in zip(row, vector, strict=True)) for row in matrix]


def _quad_form(matrix: list[list[float]], vector: tuple[float, ...]) -> float:
    transformed = _matvec(matrix, vector)
    return sum(value * transformed[index] for index, value in enumerate(vector))


def _identity(size: int, *, scale: float = 1.0) -> list[list[float]]:
    return [[scale if row == col else 0.0 for col in range(size)] for row in range(size)]


@dataclass
class RandomAgent:
    """Uniform random policy."""

    seed: int = 0
    _random: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def select_candidate(self, context: Any, remaining: list[Any], *, step_index: int) -> Any:
        return self._random.choice(remaining)

    def observe(self, context: Any, candidate: Any, *, reward: float) -> None:
        return


@dataclass
class FusedGreedyAgent:
    """Deterministic baseline that follows the current fused score."""

    def select_candidate(self, context: Any, remaining: list[Any], *, step_index: int) -> Any:
        return max(remaining, key=lambda candidate: (candidate.fused_score, -candidate.rank))

    def observe(self, context: Any, candidate: Any, *, reward: float) -> None:
        return


@dataclass
class LinearUCBAgent:
    """Minimal contextual bandit over PrioriTx evidence features."""

    alpha: float = 0.6
    ridge: float = 1.0
    feature_dim: int = 12
    a_inv: list[list[float]] = field(init=False)
    b: list[float] = field(init=False)

    def __post_init__(self) -> None:
        self.a_inv = _identity(self.feature_dim, scale=1.0 / self.ridge)
        self.b = [0.0 for _ in range(self.feature_dim)]

    def _theta(self) -> tuple[float, ...]:
        return tuple(_matvec(self.a_inv, tuple(self.b)))

    def _score(self, feature_vector: tuple[float, ...]) -> float:
        theta = self._theta()
        mean = _dot(theta, feature_vector)
        variance = max(_quad_form(self.a_inv, feature_vector), 0.0)
        bonus = self.alpha * math.sqrt(variance)
        return mean + bonus

    def select_candidate(self, context: Any, remaining: list[Any], *, step_index: int) -> Any:
        return max(
            remaining,
            key=lambda candidate: (
                self._score(candidate.feature_vector),
                candidate.fused_score,
                -candidate.rank,
            ),
        )

    def observe(self, context: Any, candidate: Any, *, reward: float) -> None:
        vector = candidate.feature_vector
        a_inv_x = _matvec(self.a_inv, vector)
        denom = 1.0 + sum(value * a_inv_x[index] for index, value in enumerate(vector))
        if denom <= 0.0:
            return
        self.a_inv = [
            [
                self.a_inv[row][col] - (a_inv_x[row] * a_inv_x[col] / denom)
                for col in range(self.feature_dim)
            ]
            for row in range(self.feature_dim)
        ]
        for index, value in enumerate(vector):
            self.b[index] += reward * value
