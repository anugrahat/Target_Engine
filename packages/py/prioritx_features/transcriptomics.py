"""Metadata-derived transcriptomics baseline features.

These features do not represent biological target evidence yet. They are a
transparent readiness layer over curated study contrasts so that later
expression-derived signals have a stable, testable contract.
"""

from __future__ import annotations

import math
from typing import Any


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
