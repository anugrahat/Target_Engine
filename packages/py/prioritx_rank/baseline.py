"""Transparent readiness scoring over metadata-derived contrast features."""

from __future__ import annotations

import math
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


def score_gene_transcriptomics(features: dict[str, Any]) -> dict[str, Any]:
    """Score one gene from illustrative transcriptomics fixture features."""
    effect_component = 0.6 * min(float(features["absolute_log2_fold_change"]) / 3.0, 1.0)
    significance_component = 0.4 * min(float(features["significance_score"]) / 10.0, 1.0)

    score = effect_component + significance_component
    return {
        "contrast_id": features["contrast_id"],
        "benchmark_id": features["benchmark_id"],
        "dataset_id": features["dataset_id"],
        "gene_symbol": features["gene_symbol"],
        "score_name": "fixture_transcriptomics_gene_score",
        "score": round(score, 4),
        "components": {
            "effect_component": round(effect_component, 4),
            "significance_component": round(significance_component, 4),
        },
        "fixture_status": features["fixture_status"],
    }


def score_real_gene_transcriptomics(features: dict[str, Any]) -> dict[str, Any]:
    """Score accession-backed transcriptomics evidence from real GEO counts."""
    effect_component = 0.5 * min(float(features["absolute_log2_fold_change"]) / 3.0, 1.0)
    standardized_component = 0.35 * min(float(features["absolute_standardized_mean_difference"]) / 3.0, 1.0)
    count_component = 0.15 * min(math.log10(float(features["mean_raw_count"]) + 1.0) / 4.0, 1.0)

    score = effect_component + standardized_component + count_component
    return {
        "contrast_id": features["contrast_id"],
        "benchmark_id": features["benchmark_id"],
        "dataset_id": features["dataset_id"],
        "ensembl_gene_id": features["ensembl_gene_id"],
        "gene_symbol": features["gene_symbol"],
        "score_name": "real_transcriptomics_effect_score",
        "score": round(score, 4),
        "components": {
            "effect_component": round(effect_component, 4),
            "standardized_component": round(standardized_component, 4),
            "count_component": round(count_component, 4),
        },
        "evidence_kind": features["evidence_kind"],
    }
