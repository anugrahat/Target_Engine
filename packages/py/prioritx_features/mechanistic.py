"""Feature derivation for curated mechanistic support."""

from __future__ import annotations

import math
from typing import Any


def derive_mechanistic_support_features(
    *,
    benchmark_id: str,
    subset_id: str,
    gene: dict[str, Any],
    disease_edge_weights: dict[str, float],
    gene_edges: list[dict[str, Any]],
    max_leakage_risk: str,
) -> dict[str, Any]:
    """Summarize typed disease->mechanism->gene support for one candidate."""
    matched = []
    for edge in gene_edges:
        mechanism_ref = edge["target"]["ref"]
        disease_weight = disease_edge_weights.get(mechanism_ref)
        if disease_weight is None:
            continue
        path_strength = math.sqrt(float(disease_weight) * float(edge["weight"]))
        matched.append((path_strength, edge))

    matched.sort(key=lambda item: item[0], reverse=True)
    path_strengths = [item[0] for item in matched]
    mean_path_strength = sum(path_strengths) / len(path_strengths) if path_strengths else 0.0
    strongest_path_strength = max(path_strengths, default=0.0)

    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": gene["ensembl_gene_id"],
        "gene_symbol": gene["gene_symbol"],
        "mechanistic_support_count": len(matched),
        "mean_path_strength": round(mean_path_strength, 6),
        "strongest_path_strength": round(strongest_path_strength, 6),
        "mechanism_kinds": sorted({item[1]["target"].get("mechanism_kind", "unknown") for item in matched}),
        "top_mechanisms": [
            {
                "ref": edge["target"]["ref"],
                "label": edge["target"]["label"],
                "mechanism_kind": edge["target"].get("mechanism_kind", "unknown"),
                "path_strength": round(path_strength, 6),
                "sources": edge.get("sources", []),
                "leakage_risk": edge["leakage_risk"],
            }
            for path_strength, edge in matched[:5]
        ],
        "max_leakage_risk": max_leakage_risk,
        "evidence_kind": "curated_mechanistic_support",
    }
