"""Feature derivation for proteo-phospho program activity and target support."""

from __future__ import annotations

import math
from typing import Any


def derive_proteophospho_program_activity_features(
    *,
    benchmark_id: str,
    subset_id: str,
    program: dict[str, Any],
    protein_hits: list[dict[str, Any]],
    phosphosite_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize curated proteo-phospho support for one signaling program."""
    supported_proteins = [item for item in protein_hits if item.get("directionally_supported")]
    supported_phosphosites = [item for item in phosphosite_hits if item.get("directionally_supported")]
    all_supported = [
        *[(1.0, item) for item in supported_proteins],
        *[(1.35, item) for item in supported_phosphosites],
    ]
    total_marker_count = len(program.get("protein_markers") or []) + len(program.get("phosphosite_markers") or [])
    weighted_support = sum(weight for weight, _ in all_supported)
    max_weighted_support = len(program.get("protein_markers") or []) + 1.35 * len(program.get("phosphosite_markers") or [])
    coverage = weighted_support / max(max_weighted_support, 1.0)
    weighted_score_sum = sum(weight * float(item["score"]) for weight, item in all_supported)
    mean_marker_score = weighted_score_sum / weighted_support if weighted_support > 0.0 else 0.0
    context_scores = [
        min(max(float(item.get("outlier_shift") or 0.0), 0.0) / 1.0, 1.0)
        * min(float(item.get("outlier_fraction") or 0.0) / 0.15, 1.0)
        for _, item in all_supported
    ]
    context_strength = sum(context_scores) / len(context_scores) if context_scores else 0.0
    mean_effect = (
        sum(abs(float(item["mean_difference"])) for _, item in all_supported) / len(all_supported)
        if all_supported
        else 0.0
    )
    return {
        "benchmark_id": benchmark_id,
        "subset_id": subset_id,
        "program_ref": program["ref"],
        "program_label": program["label"],
        "linked_targets": program.get("linked_targets", []),
        "total_marker_count": total_marker_count,
        "supported_protein_count": len(supported_proteins),
        "supported_phosphosite_count": len(supported_phosphosites),
        "coverage": round(coverage, 6),
        "mean_marker_score": round(mean_marker_score, 6),
        "context_strength": round(context_strength, 6),
        "effect_strength": round(min(mean_effect / 1.0, 1.0), 6),
        "top_markers": [
            {
                "marker_kind": item["marker_kind"],
                "marker_ref": item["marker_ref"],
                "gene_symbol": item["gene_symbol"],
                "site": item.get("site"),
                "score": item["score"],
                "mean_difference": item["mean_difference"],
                "outlier_fraction": item.get("outlier_fraction"),
                "outlier_shift": item.get("outlier_shift"),
                "adjusted_p_value": item["statistics"]["adjusted_p_value"],
            }
            for _, item in sorted(all_supported, key=lambda entry: (entry[1]["score"], abs(float(entry[1]["mean_difference"]))), reverse=True)[:6]
        ],
        "sources": program.get("sources", []),
        "evidence_kind": "proteophospho_program_activity",
    }


def derive_gene_proteophospho_support_features(
    *,
    benchmark_id: str,
    subset_id: str,
    gene: dict[str, Any],
    gene_edges: list[dict[str, Any]],
    program_activity_by_ref: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Summarize target support from active proteo-phospho programs."""
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
        "evidence_kind": "proteophospho_target_support",
    }
