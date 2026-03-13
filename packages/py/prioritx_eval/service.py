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
from prioritx_eval.assertions import list_benchmark_assertion_ids, load_benchmark_assertion
from prioritx_eval.policy import benchmark_integrity_review, benchmark_mode_config
from prioritx_features.transcriptomics import REAL_SUPPORT_MAX_ADJUSTED_P, REAL_SUPPORT_MIN_ABS_LOG2_FC


def _ranked_target_item(
    benchmark_id: str,
    *,
    subset_id: str,
    gene_symbol: str,
    genetics_size: int,
    tractability_top_n: int,
    pathway_top_n: int,
    network_top_n: int,
) -> tuple[int | None, dict[str, Any] | None]:
    ranked = fused_target_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        genetics_size=genetics_size,
        tractability_top_n=tractability_top_n,
        pathway_top_n=pathway_top_n,
        network_top_n=network_top_n,
    )
    for index, item in enumerate(ranked, start=1):
        if item.get("gene_symbol") == gene_symbol:
            return index, item
    return None, None


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
        "recovery_tier": assertion.get("recovery_tier"),
        "recovery_tier_note": assertion.get("recovery_tier_note"),
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
    _, fused = _ranked_target_item(
        benchmark_id,
        subset_id=chosen_subset_id,
        gene_symbol=gene_symbol,
        genetics_size=resolved_genetics_size,
        tractability_top_n=resolved_tractability_top_n,
        pathway_top_n=resolved_pathway_top_n,
        network_top_n=resolved_network_top_n,
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
    fused_rank, fused = _ranked_target_item(
        benchmark_id,
        subset_id=chosen_subset_id,
        gene_symbol=gene_symbol,
        genetics_size=resolved_genetics_size,
        tractability_top_n=resolved_tractability_top_n,
        pathway_top_n=resolved_pathway_top_n,
        network_top_n=resolved_network_top_n,
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
                "fused_rank": fused_rank,
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
            "fused_rank": fused_rank,
            "fused_score": fused.get("score") if fused else None,
            "transcriptomics_found_in_contrasts": sum(1 for item in audit["transcriptomics"] if item["found"]),
            "transcriptomics_support_hits": sum(1 for item in audit["transcriptomics"] if item["passes_support_rule"]),
            "genetics_found": genetics is not None,
            "tractability_found": tractability is not None,
            "pathway_found": pathway is not None,
            "network_found": bool(fused and fused.get("network_provenance", {}).get("top_partners")),
        },
        "integrity_review": benchmark_integrity_review(benchmark_id, mode=mode),
    }


def explain_target_evidence(
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
    graph_result = target_evidence_graph(
        benchmark_id,
        gene_symbol=gene_symbol,
        mode=mode,
        subset_id=subset_id,
        genetics_size=genetics_size,
        tractability_top_n=tractability_top_n,
        pathway_top_n=pathway_top_n,
        network_top_n=network_top_n,
    )
    summary = graph_result["evidence_summary"]
    gene_node = next(
        (node for node in graph_result["graph"]["nodes"] if node["type"] == "gene" and node["label"] == gene_symbol),
        None,
    )
    fused_edge = next(
        (edge for edge in graph_result["graph"]["edges"] if edge["type"] == "fused_target_evidence"),
        None,
    )
    pathway_nodes = [node for node in graph_result["graph"]["nodes"] if node["type"] == "pathway"]
    network_partners = [
        node["label"]
        for node in graph_result["graph"]["nodes"]
        if node["type"] == "gene" and node["attributes"].get("is_network_partner")
    ]

    rationale = []
    if summary["transcriptomics_support_hits"] > 0:
        rationale.append(
            f"Transcriptomics support passed the PrioriTx rule in {summary['transcriptomics_support_hits']} accession-backed contrasts."
        )
    elif summary["transcriptomics_found_in_contrasts"] > 0:
        rationale.append(
            f"Transcriptomics signal was observed in {summary['transcriptomics_found_in_contrasts']} contrasts, but none passed the current support rule."
        )
    if summary["genetics_found"]:
        genetics_edge = next((edge for edge in graph_result["graph"]["edges"] if edge["type"] == "genetics_association"), None)
        association_rank = genetics_edge["attributes"].get("association_rank") if genetics_edge else None
        if association_rank is not None:
            rationale.append(f"Open Targets genetics evidence is present with association rank {association_rank}.")
        else:
            rationale.append("Open Targets genetics evidence is present for this indication.")
    if summary["tractability_found"]:
        tractability_node = next((node for node in graph_result["graph"]["nodes"] if node["type"] == "tractability_profile"), None)
        modalities = tractability_node["attributes"].get("positive_modalities") if tractability_node else []
        if modalities:
            rationale.append(f"Open Targets tractability shows positive modalities: {', '.join(modalities)}.")
    if summary["pathway_found"] and pathway_nodes:
        top_pathway = sorted(pathway_nodes, key=lambda node: node["attributes"].get("fdr", 1.0))[0]
        rationale.append(
            f"Reactome pathway overlap is present, led by {top_pathway['label']} (FDR {top_pathway['attributes']['fdr']:.3g})."
        )
    if summary["network_found"] and network_partners:
        rationale.append(f"STRING network support connects this gene to partners such as {', '.join(network_partners[:3])}.")

    caveats = []
    if not summary["fused_found"]:
        caveats.append("This gene is not currently recovered in the fused target ranking for the selected mode and subset.")
    elif summary["fused_rank"] and summary["fused_rank"] > 100:
        caveats.append(f"This gene is currently low-ranked in fused evidence at rank {summary['fused_rank']}.")
    if summary["transcriptomics_found_in_contrasts"] > 0 and summary["transcriptomics_support_hits"] == 0:
        caveats.append("Observed transcriptomics effects remain below the current significance-and-effect support threshold.")
    if any(item["risk_level"] == "high" for item in graph_result["integrity_review"]["families"]):
        caveats.append("High-risk literature-style evidence exists for this benchmark but is intentionally excluded from fused ranking.")

    components = (fused_edge or {}).get("attributes", {}).get("components") or {}
    overview = (
        f"{gene_symbol} is "
        + (
            f"ranked #{summary['fused_rank']} with fused score {summary['fused_score']:.4f}"
            if summary["fused_found"] and summary["fused_rank"] and summary["fused_score"] is not None
            else "not currently ranked by the fused evidence stack"
        )
        + f" for {graph_result['indication_name']} in {graph_result['mode']} mode."
    )

    return {
        "benchmark_id": benchmark_id,
        "indication_name": graph_result["indication_name"],
        "mode": graph_result["mode"],
        "subset_id": graph_result["subset_id"],
        "gene_symbol": gene_symbol,
        "ensembl_gene_id": graph_result["ensembl_gene_id"],
        "overview": overview,
        "rationale": rationale,
        "caveats": caveats,
        "fused_components": components,
        "evidence_summary": summary,
        "integrity_review": graph_result["integrity_review"],
        "graph": {
            "node_count": len(graph_result["graph"]["nodes"]),
            "edge_count": len(graph_result["graph"]["edges"]),
        },
        "provenance": {
            "explanation_kind": "deterministic_target_evidence_summary",
            "graph_gene_node": gene_node["id"] if gene_node else None,
        },
    }


def explain_target_shortlist(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    top_n: int = 10,
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
        genetics_size=resolved_genetics_size,
        tractability_top_n=resolved_tractability_top_n,
        pathway_top_n=resolved_pathway_top_n,
        network_top_n=resolved_network_top_n,
    )
    positive_targets = assertion["target_assertions"]
    positive_by_symbol = {item["gene_symbol"]: item for item in positive_targets}
    positive_ranks = {
        item["gene_symbol"]: index
        for index, item in enumerate(ranked, start=1)
        if item.get("gene_symbol") in positive_by_symbol
    }

    items = []
    for ranked_item in ranked[: max(top_n, 0)]:
        explanation = explain_target_evidence(
            benchmark_id,
            gene_symbol=ranked_item["gene_symbol"],
            mode=mode,
            subset_id=chosen_subset_id,
            genetics_size=resolved_genetics_size,
            tractability_top_n=resolved_tractability_top_n,
            pathway_top_n=resolved_pathway_top_n,
            network_top_n=resolved_network_top_n,
        )
        items.append(
            {
                "rank": explanation["evidence_summary"]["fused_rank"],
                "gene_symbol": ranked_item["gene_symbol"],
                "ensembl_gene_id": ranked_item.get("ensembl_gene_id"),
                "score": ranked_item["score"],
                "benchmark_positive_overlay": (
                    {
                        "is_source_backed_positive": True,
                        "label_tier": positive_by_symbol[ranked_item["gene_symbol"]]["label_tier"],
                        "assertion_kind": positive_by_symbol[ranked_item["gene_symbol"]]["assertion_kind"],
                        "source": positive_by_symbol[ranked_item["gene_symbol"]]["source"],
                    }
                    if ranked_item["gene_symbol"] in positive_by_symbol
                    else {
                        "is_source_backed_positive": False,
                    }
                ),
                "overview": explanation["overview"],
                "rationale": explanation["rationale"],
                "caveats": explanation["caveats"],
                "fused_components": explanation["fused_components"],
                "evidence_summary": explanation["evidence_summary"],
            }
        )

    return {
        "benchmark_id": benchmark_id,
        "indication_name": assertion["indication_name"],
        "mode": mode,
        "subset_id": chosen_subset_id,
        "top_n": top_n,
        "items": items,
        "benchmark_positive_overlay": {
            "positive_target_count": len(positive_targets),
            "recovered_in_top_n_count": sum(
                1 for gene_symbol, rank in positive_ranks.items() if rank <= max(top_n, 0)
            ),
            "items": [
                {
                    "gene_symbol": target["gene_symbol"],
                    "ensembl_gene_id": target["ensembl_gene_id"],
                    "label_tier": target["label_tier"],
                    "assertion_kind": target["assertion_kind"],
                    "recovered_in_ranking": target["gene_symbol"] in positive_ranks,
                    "recovered_in_top_n": positive_ranks.get(target["gene_symbol"], top_n + 1) <= max(top_n, 0),
                    "rank": positive_ranks.get(target["gene_symbol"]),
                    "source": target["source"],
                }
                for target in positive_targets
            ],
        },
        "integrity_review": benchmark_integrity_review(benchmark_id, mode=mode),
        "provenance": {
            "explanation_kind": "deterministic_target_shortlist_summary",
            "source_ranking": "fused_target_evidence",
        },
    }


def compare_benchmark_modes(
    benchmark_id: str,
    *,
    top_n: int = 10,
) -> dict[str, Any]:
    assertion = load_benchmark_assertion(benchmark_id)
    strict = explain_target_shortlist(benchmark_id, mode="strict", top_n=top_n)
    exploratory = explain_target_shortlist(benchmark_id, mode="exploratory", top_n=top_n)

    def _overlay_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {item["gene_symbol"]: item for item in payload["benchmark_positive_overlay"]["items"]}

    strict_overlay = _overlay_map(strict)
    exploratory_overlay = _overlay_map(exploratory)
    comparison_items = []
    for gene_symbol in sorted(set(strict_overlay) | set(exploratory_overlay)):
        strict_item = strict_overlay.get(gene_symbol)
        exploratory_item = exploratory_overlay.get(gene_symbol)
        strict_rank = strict_item["rank"] if strict_item else None
        exploratory_rank = exploratory_item["rank"] if exploratory_item else None
        if strict_rank is None and exploratory_rank is None:
            movement = "not_recovered"
            rank_delta = None
        elif strict_rank is None:
            movement = "recovered_only_in_exploratory"
            rank_delta = None
        elif exploratory_rank is None:
            movement = "recovered_only_in_strict"
            rank_delta = None
        else:
            rank_delta = strict_rank - exploratory_rank
            if rank_delta > 0:
                movement = "improved_in_exploratory"
            elif rank_delta < 0:
                movement = "worsened_in_exploratory"
            else:
                movement = "unchanged"
        comparison_items.append(
            {
                "gene_symbol": gene_symbol,
                "label_tier": (strict_item or exploratory_item)["label_tier"],
                "strict_rank": strict_rank,
                "exploratory_rank": exploratory_rank,
                "rank_delta": rank_delta,
                "strict_recovered_in_top_n": strict_item["recovered_in_top_n"] if strict_item else False,
                "exploratory_recovered_in_top_n": exploratory_item["recovered_in_top_n"] if exploratory_item else False,
                "movement": movement,
                "source": (strict_item or exploratory_item)["source"],
            }
        )

    return {
        "benchmark_id": benchmark_id,
        "indication_name": strict["indication_name"],
        "recovery_tier": assertion.get("recovery_tier"),
        "recovery_tier_note": assertion.get("recovery_tier_note"),
        "top_n": top_n,
        "strict": {
            "subset_id": strict["subset_id"],
            "top_targets": [
                {
                    "rank": item["rank"],
                    "gene_symbol": item["gene_symbol"],
                    "score": item["score"],
                }
                for item in strict["items"]
            ],
        },
        "exploratory": {
            "subset_id": exploratory["subset_id"],
            "top_targets": [
                {
                    "rank": item["rank"],
                    "gene_symbol": item["gene_symbol"],
                    "score": item["score"],
                }
                for item in exploratory["items"]
            ],
        },
        "benchmark_positive_comparison": comparison_items,
        "integrity_review": {
            "strict": strict["integrity_review"],
            "exploratory": exploratory["integrity_review"],
        },
        "provenance": {
            "comparison_kind": "strict_vs_exploratory_benchmark_overlay",
        },
    }


def summarize_benchmark_dashboard(*, top_n: int = 5) -> dict[str, Any]:
    items = []
    for benchmark_id in list_benchmark_assertion_ids():
        comparison = compare_benchmark_modes(benchmark_id, top_n=top_n)
        items.append(
            {
                "benchmark_id": benchmark_id,
                "indication_name": comparison["indication_name"],
                "recovery_tier": comparison.get("recovery_tier"),
                "recovery_tier_note": comparison.get("recovery_tier_note"),
                "strict_subset_id": comparison["strict"]["subset_id"],
                "exploratory_subset_id": comparison["exploratory"]["subset_id"],
                "strict_top_targets": comparison["strict"]["top_targets"],
                "exploratory_top_targets": comparison["exploratory"]["top_targets"],
                "benchmark_positive_comparison": comparison["benchmark_positive_comparison"],
            }
        )

    return {
        "benchmark_count": len(items),
        "top_n": top_n,
        "items": items,
        "provenance": {
            "summary_kind": "benchmark_dashboard_summary",
        },
    }


def summarize_benchmark_health(*, top_n: int = 10) -> dict[str, Any]:
    dashboard = summarize_benchmark_dashboard(top_n=top_n)
    items = []
    improved_count = 0
    worsened_count = 0
    recovered_in_strict_top_n = 0
    recovered_in_exploratory_top_n = 0

    for item in dashboard["items"]:
        positives = item["benchmark_positive_comparison"]
        positive_count = len(positives)
        strict_hits = sum(1 for positive in positives if positive["strict_recovered_in_top_n"])
        exploratory_hits = sum(1 for positive in positives if positive["exploratory_recovered_in_top_n"])
        improved = sum(1 for positive in positives if positive["movement"] == "improved_in_exploratory")
        worsened = sum(1 for positive in positives if positive["movement"] == "worsened_in_exploratory")
        unchanged = sum(1 for positive in positives if positive["movement"] == "unchanged")
        recovered_any = sum(
            1
            for positive in positives
            if positive["strict_rank"] is not None or positive["exploratory_rank"] is not None
        )

        improved_count += improved
        worsened_count += worsened
        recovered_in_strict_top_n += strict_hits
        recovered_in_exploratory_top_n += exploratory_hits

        if exploratory_hits > 0:
            readiness = "exploratory_positive_in_top_n"
        elif strict_hits > 0:
            readiness = "strict_positive_in_top_n"
        elif recovered_any > 0:
            readiness = "positive_recovered_outside_top_n"
        else:
            readiness = "positive_not_recovered"

        items.append(
            {
                "benchmark_id": item["benchmark_id"],
                "indication_name": item["indication_name"],
                "recovery_tier": item.get("recovery_tier"),
                "recovery_tier_note": item.get("recovery_tier_note"),
                "positive_target_count": positive_count,
                "strict_recovered_in_top_n_count": strict_hits,
                "exploratory_recovered_in_top_n_count": exploratory_hits,
                "recovered_anywhere_count": recovered_any,
                "improved_in_exploratory_count": improved,
                "worsened_in_exploratory_count": worsened,
                "unchanged_count": unchanged,
                "readiness_flag": readiness,
                "strict_leader": item["strict_top_targets"][0] if item["strict_top_targets"] else None,
                "exploratory_leader": item["exploratory_top_targets"][0] if item["exploratory_top_targets"] else None,
            }
        )

    return {
        "benchmark_count": dashboard["benchmark_count"],
        "top_n": top_n,
        "totals": {
            "positive_target_count": sum(item["positive_target_count"] for item in items),
            "strict_recovered_in_top_n_count": recovered_in_strict_top_n,
            "exploratory_recovered_in_top_n_count": recovered_in_exploratory_top_n,
            "improved_in_exploratory_count": improved_count,
            "worsened_in_exploratory_count": worsened_count,
        },
        "items": items,
        "provenance": {
            "summary_kind": "benchmark_health_summary",
            "source_summary": "benchmark_dashboard_summary",
        },
    }


def export_benchmark_health_rows(*, top_n: int = 10) -> dict[str, Any]:
    health = summarize_benchmark_health(top_n=top_n)
    dashboard = summarize_benchmark_dashboard(top_n=top_n)
    dashboard_by_benchmark = {item["benchmark_id"]: item for item in dashboard["items"]}

    rows = []
    for item in health["items"]:
        dashboard_item = dashboard_by_benchmark[item["benchmark_id"]]
        positive_items = dashboard_item["benchmark_positive_comparison"]
        if not positive_items:
            rows.append(
                {
                    "benchmark_id": item["benchmark_id"],
                    "indication_name": item["indication_name"],
                    "top_n": top_n,
                    "readiness_flag": item["readiness_flag"],
                    "strict_subset_id": dashboard_item["strict_subset_id"],
                    "exploratory_subset_id": dashboard_item["exploratory_subset_id"],
                    "strict_leader_gene_symbol": (item["strict_leader"] or {}).get("gene_symbol"),
                    "strict_leader_rank": (item["strict_leader"] or {}).get("rank"),
                    "strict_leader_score": (item["strict_leader"] or {}).get("score"),
                    "exploratory_leader_gene_symbol": (item["exploratory_leader"] or {}).get("gene_symbol"),
                    "exploratory_leader_rank": (item["exploratory_leader"] or {}).get("rank"),
                    "exploratory_leader_score": (item["exploratory_leader"] or {}).get("score"),
                    "positive_gene_symbol": None,
                    "label_tier": None,
                    "strict_rank": None,
                    "exploratory_rank": None,
                    "rank_delta": None,
                    "movement": None,
                    "strict_recovered_in_top_n": False,
                    "exploratory_recovered_in_top_n": False,
                    "positive_target_count": item["positive_target_count"],
                    "strict_recovered_in_top_n_count": item["strict_recovered_in_top_n_count"],
                    "exploratory_recovered_in_top_n_count": item["exploratory_recovered_in_top_n_count"],
                    "recovered_anywhere_count": item["recovered_anywhere_count"],
                    "improved_in_exploratory_count": item["improved_in_exploratory_count"],
                    "worsened_in_exploratory_count": item["worsened_in_exploratory_count"],
                    "unchanged_count": item["unchanged_count"],
                }
            )
            continue

        for positive in positive_items:
            rows.append(
                {
                    "benchmark_id": item["benchmark_id"],
                    "indication_name": item["indication_name"],
                    "top_n": top_n,
                    "readiness_flag": item["readiness_flag"],
                    "strict_subset_id": dashboard_item["strict_subset_id"],
                    "exploratory_subset_id": dashboard_item["exploratory_subset_id"],
                    "strict_leader_gene_symbol": (item["strict_leader"] or {}).get("gene_symbol"),
                    "strict_leader_rank": (item["strict_leader"] or {}).get("rank"),
                    "strict_leader_score": (item["strict_leader"] or {}).get("score"),
                    "exploratory_leader_gene_symbol": (item["exploratory_leader"] or {}).get("gene_symbol"),
                    "exploratory_leader_rank": (item["exploratory_leader"] or {}).get("rank"),
                    "exploratory_leader_score": (item["exploratory_leader"] or {}).get("score"),
                    "positive_gene_symbol": positive["gene_symbol"],
                    "label_tier": positive["label_tier"],
                    "strict_rank": positive["strict_rank"],
                    "exploratory_rank": positive["exploratory_rank"],
                    "rank_delta": positive["rank_delta"],
                    "movement": positive["movement"],
                    "strict_recovered_in_top_n": positive["strict_recovered_in_top_n"],
                    "exploratory_recovered_in_top_n": positive["exploratory_recovered_in_top_n"],
                    "positive_target_count": item["positive_target_count"],
                    "strict_recovered_in_top_n_count": item["strict_recovered_in_top_n_count"],
                    "exploratory_recovered_in_top_n_count": item["exploratory_recovered_in_top_n_count"],
                    "recovered_anywhere_count": item["recovered_anywhere_count"],
                    "improved_in_exploratory_count": item["improved_in_exploratory_count"],
                    "worsened_in_exploratory_count": item["worsened_in_exploratory_count"],
                    "unchanged_count": item["unchanged_count"],
                }
            )

    return {
        "top_n": top_n,
        "row_count": len(rows),
        "rows": rows,
        "provenance": {
            "export_kind": "benchmark_health_rows",
            "source_summary": "benchmark_health_summary",
        },
    }
