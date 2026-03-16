"""Feature derivation for single-cell-derived cell-state program support."""

from __future__ import annotations

import math
from typing import Any


def derive_cell_state_program_activity_features(
    *,
    benchmark_id: str,
    subset_id: str,
    program: dict[str, Any],
    marker_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize bulk-cohort support for one single-cell-derived program."""
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
    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "program_ref": program["ref"],
        "program_label": program["label"],
        "cell_state_kind": program["cell_state_kind"],
        "linked_targets": program.get("linked_targets", []),
        "marker_gene_count": marker_count,
        "positive_marker_count": len(positive_hits),
        "coverage": round(coverage, 6),
        "mean_marker_score": round(mean_marker_score, 6),
        "effect_strength": round(min(abs(mean_effect) / 2.0, 1.0), 6),
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
        "evidence_kind": "single_cell_derived_cell_state_activity",
    }


def derive_gene_cell_state_support_features(
    *,
    benchmark_id: str,
    subset_id: str,
    gene: dict[str, Any],
    program_activity_by_ref: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Summarize whether one gene is linked to active cell-state programs."""
    matched = []
    for program in program_activity_by_ref.values():
        if gene["gene_symbol"] not in set(program.get("linked_targets") or []):
            continue
        matched.append(program)

    scores = [float(item["score"]) for item in matched]
    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "ensembl_gene_id": gene["ensembl_gene_id"],
        "gene_symbol": gene["gene_symbol"],
        "program_support_count": len(matched),
        "mean_program_score": round(sum(scores) / len(scores), 6) if scores else 0.0,
        "strongest_program_score": round(max(scores, default=0.0), 6),
        "top_programs": [
            {
                "ref": item["program_ref"],
                "label": item["program_label"],
                "cell_state_kind": item["cell_state_kind"],
                "score": item["score"],
                "top_markers": item["top_markers"],
                "sources": item["sources"],
            }
            for item in sorted(matched, key=lambda entry: entry["score"], reverse=True)[:5]
        ],
        "evidence_kind": "single_cell_derived_gene_cell_state_support",
    }
