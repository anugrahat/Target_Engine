"""Metadata-derived transcriptomics baseline features.

These features do not represent biological target evidence yet. They are a
transparent readiness layer over curated study contrasts so that later
expression-derived signals have a stable, testable contract.
"""

from __future__ import annotations

import math
from collections import Counter
from statistics import fmean
from typing import Any


REAL_SUPPORT_MAX_ADJUSTED_P = 0.05
REAL_SUPPORT_MIN_ABS_LOG2_FC = 0.5


def _lower(value: str | None) -> str:
    return value.lower() if value else ""


def derive_contrast_quality_features(contrast: dict[str, Any]) -> dict[str, Any]:
    """Derive transparent metadata features for one study contrast."""
    sample_counts = contrast.get("sample_counts") or {}
    case_count = sample_counts.get("case") or 0
    control_count = sample_counts.get("control") or 0
    total_samples = case_count + control_count
    max_group = max(case_count, control_count, 1)
    min_group = min(case_count, control_count)
    balance_ratio = min_group / max_group if max_group else 0.0

    control_definition = _lower(contrast.get("control_definition"))
    inclusion_rule = _lower(contrast.get("inclusion_rule_summary"))
    leakage_risks = " ".join(_lower(risk) for risk in contrast.get("leakage_risks", []))
    notes = _lower((contrast.get("provenance") or {}).get("notes"))
    joined_text = " ".join([control_definition, inclusion_rule, leakage_risks, notes])

    healthy_like_control = int(
        "healthy" in joined_text
        or "age-matched control" in joined_text
        or "solid tissue normal" in joined_text
        or "paired normal" in joined_text
    )
    adjacent_control = int("adjacent" in joined_text or "non-tumorous" in joined_text)
    mixed_disease_risk = int("mixed" in joined_text or "pneumothorax" in joined_text)
    curated_public_arm = int("curated public project arm" in joined_text or "tcga-lihc" in joined_text)
    verified_status = int(contrast.get("status") == "verified")
    bulk_rna = int(contrast.get("analysis_unit") == "bulk_rna")

    return {
        "contrast_id": contrast["contrast_id"],
        "benchmark_id": contrast["benchmark_id"],
        "modality": contrast.get("modality"),
        "tissue": contrast.get("tissue"),
        "case_samples": case_count,
        "control_samples": control_count,
        "total_samples": total_samples,
        "sample_balance_ratio": round(balance_ratio, 4),
        "healthy_like_control": healthy_like_control,
        "adjacent_control": adjacent_control,
        "mixed_disease_risk": mixed_disease_risk,
        "curated_public_arm": curated_public_arm,
        "verified_status": verified_status,
        "bulk_rna": bulk_rna,
    }


def derive_gene_transcriptomics_features(record: dict[str, Any]) -> dict[str, Any]:
    """Derive transparent gene-level features from one transcriptomics record."""
    stats = record["statistics"]
    log2_fold_change = float(stats["log2_fold_change"])
    adjusted_p_value = max(float(stats["adjusted_p_value"]), 1e-300)
    significance = min(-math.log10(adjusted_p_value), 20.0)

    return {
        "contrast_id": record["contrast_id"],
        "benchmark_id": record["benchmark_id"],
        "dataset_id": record["dataset_id"],
        "gene_symbol": record["gene"]["symbol"],
        "effect_direction": 1 if log2_fold_change >= 0 else -1,
        "absolute_log2_fold_change": round(abs(log2_fold_change), 4),
        "significance_score": round(significance, 4),
        "fixture_status": record["fixture_status"],
    }


def derive_real_gene_transcriptomics_features(record: dict[str, Any]) -> dict[str, Any]:
    """Derive transparent features from accession-backed transcriptomics statistics."""
    stats = record["statistics"]
    log2_fold_change = float(stats["log2_fold_change"])
    standardized_mean_difference = float(stats["standardized_mean_difference"])
    adjusted_p_value = max(float(stats["adjusted_p_value"]), 1e-300)
    significance = min(-math.log10(adjusted_p_value), 20.0)
    abundance_value = float(stats.get("mean_raw_count", stats.get("mean_expression", 0.0)))
    abundance_kind = "raw_count" if "mean_raw_count" in stats else "expression"

    return {
        "contrast_id": record["contrast_id"],
        "benchmark_id": record["benchmark_id"],
        "dataset_id": record["dataset_id"],
        "ensembl_gene_id": record["gene"]["ensembl_gene_id"],
        "gene_symbol": record["gene"]["symbol"],
        "effect_direction": 1 if log2_fold_change >= 0 else -1,
        "absolute_log2_fold_change": round(abs(log2_fold_change), 4),
        "absolute_standardized_mean_difference": round(abs(standardized_mean_difference), 4),
        "significance_score": round(significance, 4),
        "abundance_value": round(max(abundance_value, 0.0), 4),
        "abundance_kind": abundance_kind,
        "evidence_kind": record["evidence_kind"],
    }


def _real_supports_signal(record: dict[str, Any]) -> bool:
    stats = record["statistics"]
    return (
        float(stats["adjusted_p_value"]) <= REAL_SUPPORT_MAX_ADJUSTED_P
        and abs(float(stats["log2_fold_change"])) >= REAL_SUPPORT_MIN_ABS_LOG2_FC
    )


def _pick_majority(values: list[str | None]) -> str | None:
    observed = [value for value in values if value]
    if not observed:
        return None
    return Counter(observed).most_common(1)[0][0]


def derive_real_gene_evidence_features(
    *,
    benchmark_id: str,
    subset_id: str | None,
    total_real_contrasts: int,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate accession-backed transcriptomics evidence across contrasts."""
    if not records:
        raise ValueError("records must not be empty")

    observed_contrasts = sorted({record["contrast_id"] for record in records})
    supported_records = [record for record in records if _real_supports_signal(record)]
    support_count = len(supported_records)
    positive_support = sum(1 for record in supported_records if float(record["statistics"]["log2_fold_change"]) > 0.0)
    negative_support = sum(1 for record in supported_records if float(record["statistics"]["log2_fold_change"]) < 0.0)
    support_fraction = support_count / max(total_real_contrasts, 1)
    direction_consistency = abs(positive_support - negative_support) / max(support_count, 1)

    weighted_effects: list[float] = []
    weights: list[float] = []
    per_contrast = []
    for record in records:
        stats = record["statistics"]
        sample_counts = record["sample_counts"]
        total_samples = int(sample_counts["case"]) + int(sample_counts["control"])
        weight = math.sqrt(max(total_samples, 1))
        weights.append(weight)
        weighted_effects.append(weight * float(stats["log2_fold_change"]))
        per_contrast.append(
            {
                "contrast_id": record["contrast_id"],
                "dataset_id": record["dataset_id"],
                "adjusted_p_value": float(stats["adjusted_p_value"]),
                "log2_fold_change": float(stats["log2_fold_change"]),
                "direction": "up" if float(stats["log2_fold_change"]) >= 0.0 else "down",
                "supports_signal": _real_supports_signal(record),
                "sample_counts": sample_counts,
            }
        )

    combined_weights = sum(weight ** 2 for weight in weights)
    weighted_mean_log2_fc = sum(weighted_effects) / max(sum(weights), 1e-9)
    mean_abs_standardized = fmean(abs(float(record["statistics"]["standardized_mean_difference"])) for record in records)
    supported_p_values = [float(record["statistics"]["adjusted_p_value"]) for record in supported_records]
    best_adjusted_p = min(float(record["statistics"]["adjusted_p_value"]) for record in records)
    geometric_supported_p = (
        math.exp(fmean(math.log(max(value, 1e-300)) for value in supported_p_values))
        if supported_p_values
        else 1.0
    )

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": records[0]["gene"]["ensembl_gene_id"],
        "gene_symbol": _pick_majority([record["gene"].get("symbol") for record in records]),
        "hgnc_id": _pick_majority([record["gene"].get("hgnc_id") for record in records]),
        "total_real_contrasts": total_real_contrasts,
        "observed_contrast_count": len(observed_contrasts),
        "supporting_contrast_count": support_count,
        "support_fraction": round(support_fraction, 4),
        "positive_support_count": positive_support,
        "negative_support_count": negative_support,
        "direction_consistency": round(direction_consistency, 4),
        "direction_conflict": positive_support > 0 and negative_support > 0,
        "weighted_mean_log2_fold_change": round(weighted_mean_log2_fc, 6),
        "mean_absolute_standardized_mean_difference": round(mean_abs_standardized, 6),
        "best_adjusted_p_value": round(best_adjusted_p, 12),
        "geometric_supported_adjusted_p_value": round(geometric_supported_p, 12),
        "total_sample_weight": round(math.sqrt(combined_weights), 6),
        "evidence_kind": "cross_contrast_real_transcriptomics",
        "support_rule": {
            "max_adjusted_p_value": REAL_SUPPORT_MAX_ADJUSTED_P,
            "min_absolute_log2_fold_change": REAL_SUPPORT_MIN_ABS_LOG2_FC,
        },
        "source_contrast_ids": observed_contrasts,
        "source_dataset_ids": sorted({record["dataset_id"] for record in records}),
        "per_contrast_evidence": per_contrast,
    }
