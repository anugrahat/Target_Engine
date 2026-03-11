"""Feature derivation for transparent multi-evidence target fusion."""

from __future__ import annotations

from typing import Any


def derive_fused_target_evidence_features(
    *,
    benchmark_id: str,
    subset_id: str | None,
    transcriptomics: dict[str, Any] | None,
    genetics: dict[str, Any] | None,
    tractability: dict[str, Any] | None,
    pathway: dict[str, Any] | None,
    network: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge transcriptomics, genetics, tractability, and network evidence into one target feature record."""
    reference = transcriptomics or genetics or tractability or pathway or network
    if reference is None:
        raise ValueError("at least one evidence record is required")

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": reference["ensembl_gene_id"],
        "gene_symbol": reference.get("gene_symbol"),
        "transcriptomics_score": float(transcriptomics["score"]) if transcriptomics else 0.0,
        "genetics_score": float(genetics["score"]) if genetics else 0.0,
        "tractability_score": float(tractability["score"]) if tractability else 0.0,
        "pathway_score": float(pathway["score"]) if pathway else 0.0,
        "network_score": float(network["score"]) if network else 0.0,
        "transcriptomics_supporting_contrasts": int(transcriptomics["supporting_contrast_count"]) if transcriptomics else 0,
        "transcriptomics_direction_conflict": bool(transcriptomics["direction_conflict"]) if transcriptomics else False,
        "genetics_available": genetics is not None,
        "transcriptomics_available": transcriptomics is not None,
        "tractability_available": tractability is not None,
        "pathway_available": pathway is not None,
        "network_available": network is not None,
        "transcriptomics_evidence_kind": transcriptomics["evidence_kind"] if transcriptomics else None,
        "genetics_evidence_kind": genetics["evidence_kind"] if genetics else None,
        "tractability_evidence_kind": tractability["evidence_kind"] if tractability else None,
        "pathway_evidence_kind": pathway["evidence_kind"] if pathway else None,
        "network_evidence_kind": network["evidence_kind"] if network else None,
        "transcriptomics_provenance": {
            "source_contrast_ids": transcriptomics["source_contrast_ids"],
            "support_rule": transcriptomics["support_rule"],
        } if transcriptomics else None,
        "genetics_provenance": {
            "disease_id": genetics["disease_id"],
            "statistics": genetics["statistics"],
        } if genetics else None,
        "tractability_provenance": {
            "positive_modalities": tractability["positive_modalities"],
            "positive_bucket_count": tractability["positive_bucket_count"],
            "positive_buckets": tractability["positive_buckets"],
        } if tractability else None,
        "pathway_provenance": {
            "overlap_count": pathway["overlap_count"],
            "top_overlap_pathways": pathway["top_overlap_pathways"],
            "enrichment_gene_count": pathway["enrichment_gene_count"],
            "enrichment_fdr_max": pathway["enrichment_fdr_max"],
        } if pathway else None,
        "network_provenance": {
            "partner_count": network["partner_count"],
            "seed_partner_count": network["seed_partner_count"],
            "top_partners": network["top_partners"],
        } if network else None,
    }
