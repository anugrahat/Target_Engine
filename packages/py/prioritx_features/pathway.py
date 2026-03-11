"""Feature derivation for Reactome pathway support evidence."""

from __future__ import annotations

import math
from typing import Any


def _pathway_strength(fdr: float) -> float:
    return min(max(-math.log10(max(fdr, 1e-300)) / 20.0, 0.0), 1.0)


def derive_reactome_pathway_features(
    *,
    benchmark_id: str,
    subset_id: str | None,
    gene: dict[str, Any],
    enriched_pathways: list[dict[str, Any]],
    gene_pathways: list[dict[str, Any]],
    enrichment_gene_count: int,
    enrichment_fdr_max: float,
) -> dict[str, Any]:
    """Derive pathway-overlap features for one candidate gene."""
    enriched_by_id = {
        item["pathway"]["st_id"]: item
        for item in enriched_pathways
        if item["pathway"].get("st_id")
    }
    overlap = [
        item
        for item in gene_pathways
        if item["pathway"].get("st_id") in enriched_by_id
    ]
    overlap.sort(key=lambda item: item["statistics"]["fdr"])
    overlap_strengths = [_pathway_strength(item["statistics"]["fdr"]) for item in overlap]
    weighted_overlap_strength = min(sum(overlap_strengths[:10]) / 3.0, 1.0)
    best_fdr = min((item["statistics"]["fdr"] for item in overlap), default=1.0)

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": gene["ensembl_gene_id"],
        "gene_symbol": gene.get("gene_symbol"),
        "overlap_count": len(overlap),
        "gene_pathway_count": len(gene_pathways),
        "enriched_pathway_count": len(enriched_pathways),
        "best_overlap_fdr": float(best_fdr),
        "best_overlap_strength": _pathway_strength(float(best_fdr)),
        "weighted_overlap_strength": round(weighted_overlap_strength, 6),
        "pathway_overlap_fraction": round(len(overlap) / max(len(gene_pathways), 1), 6),
        "enrichment_gene_count": enrichment_gene_count,
        "enrichment_fdr_max": enrichment_fdr_max,
        "top_overlap_pathways": [
            {
                "st_id": item["pathway"]["st_id"],
                "name": item["pathway"]["name"],
                "fdr": item["statistics"]["fdr"],
            }
            for item in overlap[:10]
        ],
        "evidence_kind": "reactome_pathway_support",
    }
