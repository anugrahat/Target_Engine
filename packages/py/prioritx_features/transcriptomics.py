"""Metadata-derived transcriptomics baseline features.

These features do not represent biological target evidence yet. They are a
transparent readiness layer over curated study contrasts so that later
expression-derived signals have a stable, testable contract.
"""

from __future__ import annotations

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
