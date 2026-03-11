"""Evaluate live PrioriTx rankings against source-backed positive targets."""

from __future__ import annotations

from typing import Any

from prioritx_data.service import (
    fused_target_evidence,
    open_targets_genetics_scores,
    open_targets_tractability_scores,
    query_study_contrasts,
    reactome_pathway_scores,
    transcriptomics_real_scores,
)
from prioritx_eval.assertions import load_benchmark_assertion
from prioritx_eval.policy import benchmark_integrity_review, benchmark_mode_config
from prioritx_features.transcriptomics import REAL_SUPPORT_MAX_ADJUSTED_P, REAL_SUPPORT_MIN_ABS_LOG2_FC


def evaluate_fused_benchmark(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    min_transcriptomics_support: int = 1,
    genetics_size: int | None = None,
    tractability_top_n: int | None = None,
    pathway_top_n: int | None = None,
    network_top_n: int | None = None,
) -> dict[str, Any]:
    assertion = load_benchmark_assertion(benchmark_id)
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    resolved_genetics_size = mode_config["genetics_size"] if genetics_size is None else genetics_size
    resolved_tractability_top_n = mode_config["tractability_top_n"] if tractability_top_n is None else tractability_top_n
    resolved_pathway_top_n = mode_config["pathway_top_n"] if pathway_top_n is None else pathway_top_n
    resolved_network_top_n = mode_config["network_top_n"] if network_top_n is None else network_top_n
    ranked = fused_target_evidence(
        benchmark_id=benchmark_id,
        subset_id=chosen_subset_id,
        min_transcriptomics_support=min_transcriptomics_support,
        genetics_size=resolved_genetics_size,
        tractability_top_n=resolved_tractability_top_n,
        pathway_top_n=resolved_pathway_top_n,
        network_top_n=resolved_network_top_n,
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
        "mode": mode,
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
            "genetics_size": resolved_genetics_size,
            "tractability_top_n": resolved_tractability_top_n,
            "pathway_top_n": resolved_pathway_top_n,
            "network_top_n": resolved_network_top_n,
        },
        "integrity_review": benchmark_integrity_review(benchmark_id, mode=mode),
        "notes": assertion["notes"],
    }


def audit_target_evidence(
    benchmark_id: str,
    *,
    gene_symbol: str,
    mode: str = "strict",
    subset_id: str | None = None,
    genetics_size: int | None = None,
    tractability_top_n: int | None = None,
    pathway_top_n: int | None = None,
    network_top_n: int | None = None,
) -> dict[str, Any]:
    assertion = load_benchmark_assertion(benchmark_id)
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    resolved_genetics_size = mode_config["genetics_size"] if genetics_size is None else genetics_size
    resolved_tractability_top_n = mode_config["tractability_top_n"] if tractability_top_n is None else tractability_top_n
    resolved_pathway_top_n = mode_config["pathway_top_n"] if pathway_top_n is None else pathway_top_n
    resolved_network_top_n = mode_config["network_top_n"] if network_top_n is None else network_top_n
    real_contrast_ids = sorted(
        contrast["contrast_id"]
        for contrast in query_study_contrasts(benchmark_id=benchmark_id, subset_id=chosen_subset_id)
        if contrast["contrast_id"].startswith(f"{chosen_subset_id}_")
    )

    transcriptomics_hits = []
    for contrast_id in real_contrast_ids:
        match = next(
            (item for item in transcriptomics_real_scores(contrast_id) if item.get("gene_symbol") == gene_symbol),
            None,
        )
        if match is None:
            transcriptomics_hits.append(
                {
                    "contrast_id": contrast_id,
                    "found": False,
                    "passes_support_rule": False,
                }
            )
            continue
        stats = match["statistics"]
        passes_support_rule = (
            float(stats["adjusted_p_value"]) <= REAL_SUPPORT_MAX_ADJUSTED_P
            and abs(float(stats["log2_fold_change"])) >= REAL_SUPPORT_MIN_ABS_LOG2_FC
        )
        transcriptomics_hits.append(
            {
                "contrast_id": contrast_id,
                "found": True,
                "ensembl_gene_id": match.get("ensembl_gene_id"),
                "score": match["score"],
                "log2_fold_change": stats["log2_fold_change"],
                "adjusted_p_value": stats["adjusted_p_value"],
                "passes_support_rule": passes_support_rule,
            }
        )

    genetics = next(
        (item for item in open_targets_genetics_scores(benchmark_id, size=resolved_genetics_size) if item.get("gene_symbol") == gene_symbol),
        None,
    )
    fused = next(
        (
            item
            for item in fused_target_evidence(
                benchmark_id=benchmark_id,
                subset_id=chosen_subset_id,
                genetics_size=resolved_genetics_size,
                tractability_top_n=resolved_tractability_top_n,
                pathway_top_n=resolved_pathway_top_n,
                network_top_n=resolved_network_top_n,
            )
            if item.get("gene_symbol") == gene_symbol
        ),
        None,
    )

    return {
        "benchmark_id": benchmark_id,
        "mode": mode,
        "subset_id": chosen_subset_id,
        "gene_symbol": gene_symbol,
        "transcriptomics_support_rule": {
            "max_adjusted_p_value": REAL_SUPPORT_MAX_ADJUSTED_P,
            "min_absolute_log2_fold_change": REAL_SUPPORT_MIN_ABS_LOG2_FC,
        },
        "transcriptomics": transcriptomics_hits,
        "open_targets_genetics": {
            "found": genetics is not None,
            "score": genetics.get("score") if genetics else None,
            "ensembl_gene_id": genetics.get("ensembl_gene_id") if genetics else None,
            "association_rank": ((genetics.get("provenance") or {}).get("association_rank")) if genetics else None,
            "provenance": genetics.get("provenance") if genetics else None,
        },
        "fused_target_evidence": {
            "found": fused is not None,
            "score": fused.get("score") if fused else None,
            "ensembl_gene_id": fused.get("ensembl_gene_id") if fused else None,
            "components": fused.get("components") if fused else None,
        },
        "integrity_review": benchmark_integrity_review(benchmark_id, mode=mode),
    }


def target_evidence_graph(
    benchmark_id: str,
    *,
    gene_symbol: str,
    mode: str = "strict",
    subset_id: str | None = None,
    genetics_size: int | None = None,
    tractability_top_n: int | None = None,
    pathway_top_n: int | None = None,
    network_top_n: int | None = None,
) -> dict[str, Any]:
    assertion = load_benchmark_assertion(benchmark_id)
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    resolved_genetics_size = mode_config["genetics_size"] if genetics_size is None else genetics_size
    resolved_tractability_top_n = mode_config["tractability_top_n"] if tractability_top_n is None else tractability_top_n
    resolved_pathway_top_n = mode_config["pathway_top_n"] if pathway_top_n is None else pathway_top_n
    resolved_network_top_n = mode_config["network_top_n"] if network_top_n is None else network_top_n

    audit = audit_target_evidence(
        benchmark_id,
        gene_symbol=gene_symbol,
        mode=mode,
        subset_id=chosen_subset_id,
        genetics_size=resolved_genetics_size,
        tractability_top_n=resolved_tractability_top_n,
        pathway_top_n=resolved_pathway_top_n,
        network_top_n=resolved_network_top_n,
    )
    fused = next(
        (
            item
            for item in fused_target_evidence(
                benchmark_id=benchmark_id,
                subset_id=chosen_subset_id,
                genetics_size=resolved_genetics_size,
                tractability_top_n=resolved_tractability_top_n,
                pathway_top_n=resolved_pathway_top_n,
                network_top_n=resolved_network_top_n,
            )
            if item.get("gene_symbol") == gene_symbol
        ),
        None,
    )
    pathway = next(
        (
            item
            for item in reactome_pathway_scores(
                benchmark_id=benchmark_id,
                subset_id=chosen_subset_id,
                candidate_top_n=resolved_pathway_top_n,
            )
            if item.get("gene_symbol") == gene_symbol
        ),
        None,
    )
    genetics = next(
        (
            item
            for item in open_targets_genetics_scores(benchmark_id, size=resolved_genetics_size)
            if item.get("gene_symbol") == gene_symbol
        ),
        None,
    )

    ensembl_gene_id = (
        audit["fused_target_evidence"].get("ensembl_gene_id")
        or audit["open_targets_genetics"].get("ensembl_gene_id")
        or next((item.get("ensembl_gene_id") for item in audit["transcriptomics"] if item.get("ensembl_gene_id")), None)
    )
    tractability = None
    if ensembl_gene_id:
        tractability = next(
            (
                item
                for item in open_targets_tractability_scores([ensembl_gene_id])
                if item.get("ensembl_gene_id") == ensembl_gene_id
            ),
            None,
        )

    gene_node_id = f"gene:{ensembl_gene_id or gene_symbol}"
    nodes = [
        {
            "id": f"disease:{benchmark_id}",
            "type": "disease",
            "label": assertion["indication_name"],
            "attributes": {
                "benchmark_id": benchmark_id,
                "subset_id": chosen_subset_id,
                "mode": mode,
            },
        },
        {
            "id": gene_node_id,
            "type": "gene",
            "label": gene_symbol,
            "attributes": {
                "ensembl_gene_id": ensembl_gene_id,
                "fused_score": fused.get("score") if fused else None,
                "found_in_fused_ranking": fused is not None,
            },
        },
    ]
    edges = []

    edges.append(
        {
            "source": f"disease:{benchmark_id}",
            "target": gene_node_id,
            "type": "fused_target_evidence",
            "attributes": {
                "found": fused is not None,
                "score": fused.get("score") if fused else None,
                "components": fused.get("components") if fused else None,
            },
        }
    )

    for transcriptomics_hit in audit["transcriptomics"]:
        contrast_id = transcriptomics_hit["contrast_id"]
        contrast_node_id = f"contrast:{contrast_id}"
        nodes.append(
            {
                "id": contrast_node_id,
                "type": "study_contrast",
                "label": contrast_id,
                "attributes": {
                    "found": transcriptomics_hit["found"],
                    "passes_support_rule": transcriptomics_hit["passes_support_rule"],
                    "log2_fold_change": transcriptomics_hit.get("log2_fold_change"),
                    "adjusted_p_value": transcriptomics_hit.get("adjusted_p_value"),
                    "score": transcriptomics_hit.get("score"),
                },
            }
        )
        edges.append(
            {
                "source": f"disease:{benchmark_id}",
                "target": contrast_node_id,
                "type": "has_contrast",
                "attributes": {"subset_id": chosen_subset_id},
            }
        )
        edges.append(
            {
                "source": contrast_node_id,
                "target": gene_node_id,
                "type": "transcriptomics_support",
                "attributes": {
                    "found": transcriptomics_hit["found"],
                    "passes_support_rule": transcriptomics_hit["passes_support_rule"],
                    "log2_fold_change": transcriptomics_hit.get("log2_fold_change"),
                    "adjusted_p_value": transcriptomics_hit.get("adjusted_p_value"),
                },
            }
        )

    if genetics:
        edges.append(
            {
                "source": f"disease:{benchmark_id}",
                "target": gene_node_id,
                "type": "genetics_association",
                "attributes": {
                    "score": genetics["score"],
                    "association_rank": (genetics.get("provenance") or {}).get("association_rank"),
                    "disease_id": (genetics.get("provenance") or {}).get("disease_id"),
                },
            }
        )

    if tractability:
        tractability_node_id = f"tractability:{ensembl_gene_id}"
        nodes.append(
            {
                "id": tractability_node_id,
                "type": "tractability_profile",
                "label": f"{gene_symbol} tractability",
                "attributes": {
                    "score": tractability["score"],
                    "positive_bucket_count": tractability["positive_bucket_count"],
                    "positive_modalities": tractability["positive_modalities"],
                },
            }
        )
        edges.append(
            {
                "source": gene_node_id,
                "target": tractability_node_id,
                "type": "tractability_support",
                "attributes": {
                    "positive_buckets": tractability["positive_buckets"],
                },
            }
        )

    if pathway:
        for pathway_item in pathway["top_overlap_pathways"]:
            pathway_id = pathway_item["st_id"]
            nodes.append(
                {
                    "id": f"pathway:{pathway_id}",
                    "type": "pathway",
                    "label": pathway_item["name"],
                    "attributes": {
                        "pathway_id": pathway_id,
                        "fdr": pathway_item["fdr"],
                    },
                }
            )
            edges.append(
                {
                    "source": gene_node_id,
                    "target": f"pathway:{pathway_id}",
                    "type": "pathway_overlap",
                    "attributes": {
                        "support_score": pathway["score"],
                        "overlap_count": pathway["overlap_count"],
                    },
                }
            )

    if fused and fused.get("network_provenance"):
        for partner in fused["network_provenance"]["top_partners"]:
            partner_symbol = partner["partner_symbol"]
            partner_node_id = f"gene:{partner_symbol}"
            nodes.append(
                {
                    "id": partner_node_id,
                    "type": "gene",
                    "label": partner_symbol,
                    "attributes": {
                        "is_network_partner": True,
                    },
                }
            )
            edges.append(
                {
                    "source": gene_node_id,
                    "target": partner_node_id,
                    "type": "string_interaction",
                    "attributes": {
                        "score": partner["score"],
                    },
                }
            )

    deduped_nodes = list({node["id"]: node for node in nodes}.values())
    return {
        "benchmark_id": benchmark_id,
        "indication_name": assertion["indication_name"],
        "mode": mode,
        "subset_id": chosen_subset_id,
        "gene_symbol": gene_symbol,
        "ensembl_gene_id": ensembl_gene_id,
        "graph": {
            "nodes": deduped_nodes,
            "edges": edges,
        },
        "evidence_summary": {
            "fused_found": fused is not None,
            "transcriptomics_found_in_contrasts": sum(1 for item in audit["transcriptomics"] if item["found"]),
            "transcriptomics_support_hits": sum(1 for item in audit["transcriptomics"] if item["passes_support_rule"]),
            "genetics_found": genetics is not None,
            "tractability_found": tractability is not None,
            "pathway_found": pathway is not None,
            "network_found": bool(fused and fused.get("network_provenance", {}).get("top_partners")),
        },
        "integrity_review": benchmark_integrity_review(benchmark_id, mode=mode),
    }
