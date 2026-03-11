"""Feature derivation for STRING network evidence."""

from __future__ import annotations

from statistics import fmean
from typing import Any


def derive_string_network_features(
    *,
    benchmark_id: str,
    subset_id: str | None,
    gene: dict[str, Any],
    edges: list[dict[str, Any]],
    seed_gene_symbols: set[str],
) -> dict[str, Any]:
    """Derive network support features for one gene within a candidate slice."""
    partner_scores = [float(edge["score"]) for edge in edges]
    seed_scores = [
        float(edge["score"])
        for edge in edges
        if edge.get("preferredName_B") in seed_gene_symbols
        or edge.get("preferredName_A") in seed_gene_symbols
    ]
    weighted_degree = sum(partner_scores)
    mean_partner_score = fmean(partner_scores) if partner_scores else 0.0
    mean_seed_score = fmean(seed_scores) if seed_scores else 0.0

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": gene["ensembl_gene_id"],
        "gene_symbol": gene["gene_symbol"],
        "partner_count": len(edges),
        "seed_partner_count": len(seed_scores),
        "weighted_degree": round(weighted_degree, 6),
        "mean_partner_score": round(mean_partner_score, 6),
        "mean_seed_score": round(mean_seed_score, 6),
        "top_partners": sorted(
            (
                {
                    "partner_symbol": edge["partner_symbol"],
                    "score": edge["score"],
                }
                for edge in edges
            ),
            key=lambda item: item["score"],
            reverse=True,
        )[:10],
        "evidence_kind": "string_network_support",
    }
