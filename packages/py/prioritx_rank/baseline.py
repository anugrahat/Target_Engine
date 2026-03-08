"""Transparent readiness scoring over metadata-derived contrast features."""

from __future__ import annotations

from typing import Any


def _bounded_sample_component(total_samples: int) -> float:
    """Map sample count into a capped contribution."""
    return min(total_samples / 100.0, 1.0)


def score_contrast_readiness(features: dict[str, Any]) -> dict[str, Any]:
    """Score how suitable a contrast is for first-wave transcriptomics work.

    This is deliberately a contrast-readiness score, not a target score.
    """
    sample_component = 0.35 * _bounded_sample_component(int(features["total_samples"]))
    balance_component = 0.20 * float(features["sample_balance_ratio"])
    verification_component = 0.20 * float(features["verified_status"])
    healthy_control_component = 0.15 * float(features["healthy_like_control"])
    bulk_component = 0.10 * float(features["bulk_rna"])
    adjacent_penalty = -0.10 * float(features["adjacent_control"])
    mixed_penalty = -0.15 * float(features["mixed_disease_risk"])
    curated_public_arm_penalty = -0.05 * float(features["curated_public_arm"])

    score = (
        sample_component
        + balance_component
        + verification_component
        + healthy_control_component
        + bulk_component
        + adjacent_penalty
        + mixed_penalty
        + curated_public_arm_penalty
    )

    return {
        "contrast_id": features["contrast_id"],
        "benchmark_id": features["benchmark_id"],
        "score_name": "contrast_readiness_score",
        "score": round(score, 4),
        "components": {
            "sample_component": round(sample_component, 4),
            "balance_component": round(balance_component, 4),
            "verification_component": round(verification_component, 4),
            "healthy_control_component": round(healthy_control_component, 4),
            "bulk_component": round(bulk_component, 4),
            "adjacent_penalty": round(adjacent_penalty, 4),
            "mixed_penalty": round(mixed_penalty, 4),
            "curated_public_arm_penalty": round(curated_public_arm_penalty, 4),
        },
    }
