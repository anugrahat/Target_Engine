"""Feature derivation for Open Targets tractability evidence."""

from __future__ import annotations

from typing import Any


_TRACTABILITY_WEIGHTS = {
    ("SM", "Approved Drug"): 1.0,
    ("SM", "Advanced Clinical"): 0.9,
    ("SM", "Phase 1 Clinical"): 0.8,
    ("SM", "High-Quality Ligand"): 0.65,
    ("SM", "Structure with Ligand"): 0.6,
    ("SM", "High-Quality Pocket"): 0.55,
    ("SM", "Med-Quality Pocket"): 0.45,
    ("SM", "Druggable Family"): 0.35,
    ("AB", "Approved Drug"): 1.0,
    ("AB", "Advanced Clinical"): 0.9,
    ("AB", "Phase 1 Clinical"): 0.8,
    ("AB", "UniProt loc high conf"): 0.55,
    ("AB", "GO CC high conf"): 0.5,
    ("AB", "UniProt loc med conf"): 0.4,
    ("AB", "UniProt SigP or TMHMM"): 0.4,
    ("AB", "GO CC med conf"): 0.3,
    ("AB", "Human Protein Atlas loc"): 0.25,
    ("PR", "Approved Drug"): 1.0,
    ("PR", "Advanced Clinical"): 0.9,
    ("PR", "Phase 1 Clinical"): 0.8,
    ("PR", "Small Molecule Binder"): 0.5,
    ("PR", "Literature"): 0.35,
    ("PR", "UniProt Ubiquitination"): 0.3,
    ("PR", "Database Ubiquitination"): 0.3,
    ("PR", "Half-life Data"): 0.25,
    ("OC", "Approved Drug"): 1.0,
    ("OC", "Advanced Clinical"): 0.9,
    ("OC", "Phase 1 Clinical"): 0.8,
}


def derive_open_targets_tractability_features(record: dict[str, Any]) -> dict[str, Any]:
    """Derive modality-aware tractability features from one Open Targets target record."""
    modality_scores: dict[str, float] = {}
    positive_buckets = []
    for bucket in record["tractability"]:
        modality = str(bucket.get("modality"))
        label = str(bucket.get("label"))
        if not bool(bucket.get("value")):
            continue
        weight = _TRACTABILITY_WEIGHTS.get((modality, label), 0.2)
        modality_scores[modality] = max(modality_scores.get(modality, 0.0), weight)
        positive_buckets.append({"modality": modality, "label": label, "weight": weight})

    return {
        "ensembl_gene_id": record["gene"]["ensembl_gene_id"],
        "gene_symbol": record["gene"]["symbol"],
        "approved_name": record["gene"]["approved_name"],
        "modality_scores": modality_scores,
        "positive_bucket_count": len(positive_buckets),
        "positive_modalities": sorted(modality_scores),
        "positive_buckets": positive_buckets,
        "evidence_kind": record["evidence_kind"],
    }
