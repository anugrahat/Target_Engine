"""Feature derivation for transparent multi-evidence target fusion."""

from __future__ import annotations

from typing import Any


def derive_fused_target_evidence_features(
    *,
    benchmark_id: str,
    subset_id: str | None,
    transcriptomics: dict[str, Any] | None,
    genetics: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge transcriptomics and genetics evidence into one target feature record."""
    reference = transcriptomics or genetics
    if reference is None:
        raise ValueError("at least one evidence record is required")

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": reference["ensembl_gene_id"],
        "gene_symbol": reference.get("gene_symbol"),
        "transcriptomics_score": float(transcriptomics["score"]) if transcriptomics else 0.0,
        "genetics_score": float(genetics["score"]) if genetics else 0.0,
        "transcriptomics_supporting_contrasts": int(transcriptomics["supporting_contrast_count"]) if transcriptomics else 0,
        "transcriptomics_direction_conflict": bool(transcriptomics["direction_conflict"]) if transcriptomics else False,
        "genetics_available": genetics is not None,
        "transcriptomics_available": transcriptomics is not None,
        "transcriptomics_evidence_kind": transcriptomics["evidence_kind"] if transcriptomics else None,
        "genetics_evidence_kind": genetics["evidence_kind"] if genetics else None,
        "transcriptomics_provenance": {
            "source_contrast_ids": transcriptomics["source_contrast_ids"],
            "support_rule": transcriptomics["support_rule"],
        } if transcriptomics else None,
        "genetics_provenance": {
            "disease_id": genetics["disease_id"],
            "statistics": genetics["statistics"],
        } if genetics else None,
    }
