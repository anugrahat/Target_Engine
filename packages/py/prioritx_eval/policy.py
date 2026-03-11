"""Benchmark mode resolution and evidence-leakage review."""

from __future__ import annotations

from typing import Any

from prioritx_eval.assertions import load_benchmark_assertion

BENCHMARK_MODES = {"strict", "exploratory"}

EVIDENCE_FAMILY_REVIEW = {
    "transcriptomics": {
        "risk_level": "low",
        "fused": True,
        "notes": "Accession-backed disease-control evidence with explicit support rules.",
    },
    "genetics": {
        "risk_level": "low",
        "fused": True,
        "notes": "Disease-target associations from Open Targets without case-study-specific tuning.",
    },
    "tractability": {
        "risk_level": "moderate",
        "fused": True,
        "notes": "Target-level modality feasibility can bias toward known target classes.",
    },
    "reactome_pathway": {
        "risk_level": "moderate",
        "fused": True,
        "notes": "Disease-context pathway overlap is useful, but favors well-annotated biology.",
    },
    "string_network": {
        "risk_level": "moderate",
        "fused": True,
        "notes": "Connectivity can favor central, well-studied genes if not bounded carefully.",
    },
    "pubmed_literature": {
        "risk_level": "high",
        "fused": False,
        "notes": "Literature popularity can directly echo benchmark narratives and famous genes.",
    },
}


def benchmark_mode_config(benchmark_id: str, *, mode: str = "strict") -> dict[str, Any]:
    """Resolve subset and scoring defaults for one benchmark mode."""
    if mode not in BENCHMARK_MODES:
        raise ValueError(f"Unsupported benchmark mode: {mode}")
    assertion = load_benchmark_assertion(benchmark_id)
    if mode == "strict":
        return {
            "mode": "strict",
            "subset_id": assertion["default_subset_id"],
            "genetics_size": 0,
            "tractability_top_n": 100,
            "pathway_top_n": 40,
            "network_top_n": 50,
            "description": "Core benchmark subset with conservative fused-evidence limits.",
        }
    return {
        "mode": "exploratory",
        "subset_id": assertion.get("exploratory_subset_id") or assertion["default_subset_id"],
        "genetics_size": 0,
        "tractability_top_n": 200,
        "pathway_top_n": 80,
        "network_top_n": 100,
        "description": "Broader subset and wider candidate slices for exploratory evidence analysis.",
    }


def benchmark_integrity_review(benchmark_id: str, *, mode: str = "strict") -> dict[str, Any]:
    """Return an explicit evidence-family leakage review for one benchmark mode."""
    config = benchmark_mode_config(benchmark_id, mode=mode)
    families = []
    for family, metadata in EVIDENCE_FAMILY_REVIEW.items():
        families.append(
            {
                "family": family,
                "risk_level": metadata["risk_level"],
                "included_in_fused_ranking": metadata["fused"],
                "mode": mode,
                "notes": metadata["notes"],
            }
        )
    return {
        "benchmark_id": benchmark_id,
        "mode": mode,
        "subset_id": config["subset_id"],
        "description": config["description"],
        "families": families,
        "benchmark_specific_forbidden_leakage": [
            item
            for target in load_benchmark_assertion(benchmark_id)["target_assertions"]
            for item in target["forbidden_feature_leakage"]
        ],
    }
