"""Feature derivation for disease-specific signaling-state support."""

from __future__ import annotations

import math
from typing import Any


def derive_signaling_program_activity_features(
    *,
    benchmark_id: str,
    subset_id: str,
    program: dict[str, Any],
    marker_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize transcriptomic support for one curated signaling program."""
    positive_hits = [
        item for item in marker_hits
        if float(item.get("weighted_mean_log2_fold_change") or 0.0) > 0.0
    ]
    marker_count = len(program.get("marker_genes") or [])
    coverage = len(positive_hits) / max(marker_count, 1)
    mean_marker_score = (
        sum(float(item["score"]) for item in positive_hits) / len(positive_hits)
        if positive_hits else 0.0
    )
    mean_effect = (
        sum(float(item.get("weighted_mean_log2_fold_change") or 0.0) for item in positive_hits) / len(positive_hits)
        if positive_hits else 0.0
    )
    effect_strength = min(abs(mean_effect) / 2.0, 1.0)
    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "program_ref": program["ref"],
        "program_label": program["label"],
        "marker_gene_count": marker_count,
        "observed_marker_count": len(marker_hits),
        "positive_marker_count": len(positive_hits),
        "coverage": round(coverage, 6),
        "mean_marker_score": round(mean_marker_score, 6),
        "mean_effect": round(mean_effect, 6),
        "effect_strength": round(effect_strength, 6),
        "top_markers": [
            {
                "gene_symbol": item["gene_symbol"],
                "score": item["score"],
                "weighted_mean_log2_fold_change": item["weighted_mean_log2_fold_change"],
                "supporting_contrast_count": item["supporting_contrast_count"],
            }
            for item in sorted(positive_hits, key=lambda entry: entry["score"], reverse=True)[:5]
        ],
        "sources": program.get("sources", []),
        "evidence_kind": "signaling_program_activity",
    }


def derive_gene_signaling_support_features(
    *,
    benchmark_id: str,
    subset_id: str,
    gene: dict[str, Any],
    gene_edges: list[dict[str, Any]],
    program_activity_by_ref: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Summarize signaling-state support for one gene from active programs."""
    matched = []
    for edge in gene_edges:
        program_ref = edge["target"]["ref"]
        program = program_activity_by_ref.get(program_ref)
        if program is None:
            continue
        path_strength = math.sqrt(float(edge["weight"]) * float(program["score"]))
        matched.append((path_strength, edge, program))

    matched.sort(key=lambda item: item[0], reverse=True)
    strengths = [item[0] for item in matched]
    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": gene["ensembl_gene_id"],
        "gene_symbol": gene["gene_symbol"],
        "program_support_count": len(matched),
        "mean_path_strength": round(sum(strengths) / len(strengths), 6) if strengths else 0.0,
        "strongest_path_strength": round(max(strengths, default=0.0), 6),
        "top_programs": [
            {
                "ref": edge["target"]["ref"],
                "label": edge["target"]["label"],
                "path_strength": round(path_strength, 6),
                "program_score": program["score"],
                "top_markers": program["top_markers"],
                "sources": edge.get("sources", []),
            }
            for path_strength, edge, program in matched[:5]
        ],
        "evidence_kind": "signaling_state_support",
    }
