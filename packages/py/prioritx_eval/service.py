"""Evaluate live PrioriTx rankings against source-backed positive targets."""

from __future__ import annotations

from typing import Any

from prioritx_data.service import fused_target_evidence
from prioritx_eval.assertions import load_benchmark_assertion


def evaluate_fused_benchmark(
    benchmark_id: str,
    *,
    subset_id: str | None = None,
    min_transcriptomics_support: int = 1,
    genetics_size: int = 50,
    tractability_top_n: int = 100,
    network_top_n: int = 50,
) -> dict[str, Any]:
    assertion = load_benchmark_assertion(benchmark_id)
    chosen_subset_id = subset_id or assertion["default_subset_id"]
    ranked = fused_target_evidence(
        benchmark_id=benchmark_id,
        subset_id=chosen_subset_id,
        min_transcriptomics_support=min_transcriptomics_support,
        genetics_size=genetics_size,
        tractability_top_n=tractability_top_n,
        network_top_n=network_top_n,
    )

    by_symbol = {
        item["gene_symbol"]: (index + 1, item)
        for index, item in enumerate(ranked)
        if item.get("gene_symbol")
    }
    by_ensembl = {
        item["ensembl_gene_id"]: (index + 1, item)
        for index, item in enumerate(ranked)
        if item.get("ensembl_gene_id")
    }

    evaluated_items = []
    found_ranks: list[int] = []
    for target in assertion["target_assertions"]:
        match = None
        matching_strategy = "none"
        if target.get("ensembl_gene_id"):
            match = by_ensembl.get(target["ensembl_gene_id"])
            if match is not None:
                matching_strategy = "ensembl_gene_id"
        if match is None:
            match = by_symbol.get(target["gene_symbol"])
            if match is not None:
                matching_strategy = "gene_symbol"

        if match is None:
            evaluated_items.append(
                {
                    "gene_symbol": target["gene_symbol"],
                    "ensembl_gene_id": target["ensembl_gene_id"],
                    "label_tier": target["label_tier"],
                    "assertion_kind": target["assertion_kind"],
                    "matching_strategy": matching_strategy,
                    "found": False,
                    "rank": None,
                    "rank_percentile": None,
                    "score": None,
                    "source": target["source"],
                    "forbidden_feature_leakage": target["forbidden_feature_leakage"],
                }
            )
            continue

        rank, item = match
        found_ranks.append(rank)
        total = len(ranked)
        evaluated_items.append(
            {
                "gene_symbol": target["gene_symbol"],
                "ensembl_gene_id": target["ensembl_gene_id"] or item.get("ensembl_gene_id"),
                "label_tier": target["label_tier"],
                "assertion_kind": target["assertion_kind"],
                "matching_strategy": matching_strategy,
                "found": True,
                "rank": rank,
                "rank_percentile": round(1.0 - ((rank - 1) / total), 4) if total else None,
                "score": item["score"],
                "components": item["components"],
                "source": target["source"],
                "forbidden_feature_leakage": target["forbidden_feature_leakage"],
            }
        )

    found_count = len(found_ranks)
    reciprocal_rank = round(sum(1.0 / rank for rank in found_ranks) / found_count, 4) if found_count else 0.0

    return {
        "benchmark_id": benchmark_id,
        "subset_id": chosen_subset_id,
        "indication_name": assertion["indication_name"],
        "target_universe_size": len(ranked),
        "positive_target_count": len(assertion["target_assertions"]),
        "positive_targets_found": found_count,
        "metrics": {
            "hit_at_10": any(rank <= 10 for rank in found_ranks),
            "hit_at_25": any(rank <= 25 for rank in found_ranks),
            "best_rank": min(found_ranks) if found_ranks else None,
            "mean_reciprocal_rank": reciprocal_rank,
        },
        "items": evaluated_items,
        "provenance": {
            "evidence_stack": "fused_target_evidence",
            "min_transcriptomics_support": min_transcriptomics_support,
            "genetics_size": genetics_size,
            "tractability_top_n": tractability_top_n,
            "network_top_n": network_top_n,
        },
        "notes": assertion["notes"],
    }
