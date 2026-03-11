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
    """Score accession-backed transcriptomics evidence with inferential support."""
    effect_component = 0.35 * min(float(features["absolute_log2_fold_change"]) / 3.0, 1.0)
    significance_component = 0.35 * min(float(features["significance_score"]) / 10.0, 1.0)
    standardized_component = 0.2 * min(float(features["absolute_standardized_mean_difference"]) / 3.0, 1.0)

    if features["abundance_kind"] == "raw_count":
        abundance_component = 0.1 * min(math.log10(float(features["abundance_value"]) + 1.0) / 4.0, 1.0)
    else:
        abundance_component = 0.1 * min(float(features["abundance_value"]) / 15.0, 1.0)

    score = effect_component + significance_component + standardized_component + abundance_component
    return {
        "contrast_id": features["contrast_id"],
        "benchmark_id": features["benchmark_id"],
        "dataset_id": features["dataset_id"],
        "ensembl_gene_id": features["ensembl_gene_id"],
        "gene_symbol": features["gene_symbol"],
        "score_name": "real_transcriptomics_inferential_score",
        "score": round(score, 4),
        "components": {
            "effect_component": round(effect_component, 4),
            "significance_component": round(significance_component, 4),
            "standardized_component": round(standardized_component, 4),
            "abundance_component": round(abundance_component, 4),
        },
        "evidence_kind": features["evidence_kind"],
    }


def score_cross_contrast_transcriptomics_evidence(features: dict[str, Any]) -> dict[str, Any]:
    """Score aggregated transcriptomics evidence across real contrasts."""
    support_component = 0.3 * min(float(features["support_fraction"]), 1.0)
    significance = min(-math.log10(max(float(features["geometric_supported_adjusted_p_value"]), 1e-300)), 20.0)
    significance_component = 0.3 * min(significance / 10.0, 1.0)
    effect_component = 0.2 * min(abs(float(features["weighted_mean_log2_fold_change"])) / 3.0, 1.0)
    standardized_component = 0.1 * min(float(features["mean_absolute_standardized_mean_difference"]) / 3.0, 1.0)
    consistency_component = 0.1 * float(features["direction_consistency"])

    score = (
        support_component
        + significance_component
        + effect_component
        + standardized_component
        + consistency_component
    )
    return {
        "benchmark_id": features["benchmark_id"],
        "subset_id": features["subset_id"],
        "ensembl_gene_id": features["ensembl_gene_id"],
        "gene_symbol": features["gene_symbol"],
        "hgnc_id": features["hgnc_id"],
        "score_name": "cross_contrast_transcriptomics_evidence_score",
        "score": round(score, 4),
        "components": {
            "support_component": round(support_component, 4),
            "significance_component": round(significance_component, 4),
            "effect_component": round(effect_component, 4),
            "standardized_component": round(standardized_component, 4),
            "consistency_component": round(consistency_component, 4),
        },
        "supporting_contrast_count": features["supporting_contrast_count"],
        "observed_contrast_count": features["observed_contrast_count"],
        "total_real_contrasts": features["total_real_contrasts"],
        "support_fraction": features["support_fraction"],
        "direction_conflict": features["direction_conflict"],
        "weighted_mean_log2_fold_change": features["weighted_mean_log2_fold_change"],
        "mean_absolute_standardized_mean_difference": features["mean_absolute_standardized_mean_difference"],
        "best_adjusted_p_value": features["best_adjusted_p_value"],
        "geometric_supported_adjusted_p_value": features["geometric_supported_adjusted_p_value"],
        "evidence_kind": features["evidence_kind"],
        "support_rule": features["support_rule"],
        "source_contrast_ids": features["source_contrast_ids"],
        "source_dataset_ids": features["source_dataset_ids"],
        "per_contrast_evidence": features["per_contrast_evidence"],
    }


def score_open_targets_genetics(features: dict[str, Any]) -> dict[str, Any]:
    """Score source-backed Open Targets genetics evidence."""
    genetic_component = 0.7 * min(float(features["genetic_association_score"]), 1.0)
    association_component = 0.2 * min(float(features["association_score"]), 1.0)
    literature_component = 0.1 * min(
        max(float(features["genetic_literature_score"]), float(features["literature_score"])),
        1.0,
    )

    score = genetic_component + association_component + literature_component
    return {
        "benchmark_id": features["benchmark_id"],
        "disease_id": features["disease_id"],
        "ensembl_gene_id": features["ensembl_gene_id"],
        "gene_symbol": features["gene_symbol"],
        "approved_name": features["approved_name"],
        "score_name": "open_targets_genetics_evidence_score",
        "score": round(score, 4),
        "components": {
            "genetic_component": round(genetic_component, 4),
            "association_component": round(association_component, 4),
            "literature_component": round(literature_component, 4),
        },
        "evidence_kind": features["evidence_kind"],
    }
