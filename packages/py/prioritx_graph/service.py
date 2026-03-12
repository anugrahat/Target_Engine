"""Assemble provenance-first knowledge graphs and transparent graph features."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from prioritx_data.mechanistic import load_mechanistic_edges
from prioritx_data.proteophospho import load_benchmark_proteophospho_statistics, load_proteophospho_programs
from prioritx_data.reactome import load_reactome_gene_pathways, load_reactome_pathway_enrichment
from prioritx_data.service import fused_target_evidence, query_study_contrasts, transcriptomics_indication_evidence, transcriptomics_real_scores
from prioritx_data.cell_state import load_cell_state_programs
from prioritx_data.signaling import load_signaling_programs
from prioritx_eval.assertions import load_benchmark_assertion
from prioritx_eval.policy import benchmark_mode_config
from prioritx_features.mechanistic import derive_mechanistic_support_features
from prioritx_features.pathway import derive_reactome_pathway_features
from prioritx_features.proteophospho import (
    derive_gene_proteophospho_support_features,
    derive_proteophospho_program_activity_features,
)
from prioritx_features.cell_state import (
    derive_cell_state_program_activity_features,
    derive_gene_cell_state_support_features,
)
from prioritx_features.signaling import (
    derive_gene_signaling_support_features,
    derive_signaling_program_activity_features,
)
from prioritx_graph.cache import load_reactome_membership_cache, save_reactome_membership_cache
from prioritx_rank.baseline import (
    score_cell_state_program_activity,
    score_cell_state_support,
    score_mechanistic_support,
    score_proteophospho_program_activity,
    score_proteophospho_support,
    score_reactome_pathway_support,
    score_signaling_program_activity,
    score_signaling_support,
)


def _bounded_log_score(value: float, *, max_log: float = 10.0) -> float:
    return min(-math.log10(max(value, 1e-300)) / max_log, 1.0)


def _edge(
    source: str,
    target: str,
    edge_type: str,
    *,
    weight: float,
    evidence_family: str,
    provenance: dict[str, Any],
    leakage_risk: str = "low",
) -> dict[str, Any]:
    return {
        "source": source,
        "target": target,
        "type": edge_type,
        "weight": round(weight, 4),
        "evidence_family": evidence_family,
        "discovery_time_valid": leakage_risk == "low",
        "leakage_risk": leakage_risk,
        "provenance": provenance,
    }


def _max_leakage_risk_for_mode(mode: str) -> str:
    return "low" if mode == "strict" else "medium"


def _enrichment_gene_symbols(core_ranked: list[dict[str, Any]], *, limit: int) -> tuple[str, ...]:
    symbols: list[str] = []
    seen: set[str] = set()
    for item in core_ranked:
        gene_symbol = item.get("gene_symbol")
        if not gene_symbol or not item.get("transcriptomics_available") or gene_symbol in seen:
            continue
        seen.add(gene_symbol)
        symbols.append(gene_symbol)
        if len(symbols) >= max(limit, 0):
            break
    return tuple(symbols)


def _score_pathway_overlap(
    *,
    benchmark_id: str,
    subset_id: str,
    gene: dict[str, Any],
    enriched_pathways: list[dict[str, Any]],
    gene_pathways: list[dict[str, Any]],
    enrichment_gene_count: int,
    enrichment_fdr_max: float,
) -> dict[str, Any]:
    features = derive_reactome_pathway_features(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        gene=gene,
        enriched_pathways=enriched_pathways,
        gene_pathways=gene_pathways,
        enrichment_gene_count=enrichment_gene_count,
        enrichment_fdr_max=enrichment_fdr_max,
    )
    return score_reactome_pathway_support(features)


def _cache_aware_pathway_scores(
    *,
    benchmark_id: str,
    subset_id: str,
    core_ranked: list[dict[str, Any]],
    candidate_limit: int,
    enrichment_gene_limit: int = 300,
    enrichment_fdr_max: float = 0.05,
) -> list[dict[str, Any]]:
    enrichment_gene_symbols = _enrichment_gene_symbols(core_ranked, limit=enrichment_gene_limit)
    if not enrichment_gene_symbols:
        return []

    enriched_pathways = [
        item
        for item in load_reactome_pathway_enrichment(enrichment_gene_symbols)
        if item["pathway"].get("species_name") == "Homo sapiens"
        and float(item["statistics"]["fdr"]) <= enrichment_fdr_max
    ]
    if not enriched_pathways:
        return []

    cache = load_reactome_membership_cache()
    cache_dirty = False
    scored = []
    for item in core_ranked[: max(candidate_limit, 0)]:
        gene_symbol = item.get("gene_symbol")
        ensembl_gene_id = item.get("ensembl_gene_id")
        if not gene_symbol or not ensembl_gene_id:
            continue

        # Reuse local memberships first so live graph runs are mostly local after warmup.
        gene_pathways = cache.get(gene_symbol)
        cache_hit = gene_pathways is not None
        if gene_pathways is None:
            gene_pathways = load_reactome_gene_pathways(gene_symbol)
            cache[gene_symbol] = gene_pathways
            cache_dirty = True

        score = _score_pathway_overlap(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            enriched_pathways=enriched_pathways,
            gene_pathways=gene_pathways,
            enrichment_gene_count=len(enrichment_gene_symbols),
            enrichment_fdr_max=enrichment_fdr_max,
        )
        score["provenance"] = {
            "source_kind": "reactome_analysis_service",
            "api_url": "https://reactome.org/AnalysisService/identifiers/projection",
            "candidate_identifier": gene_symbol,
            "cache_hit": cache_hit,
        }
        scored.append(score)

    if cache_dirty:
        save_reactome_membership_cache(cache)

    scored.sort(key=lambda item: (item["score"], item["overlap_count"]), reverse=True)
    return scored


def mechanistic_support_scores(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    ranked_items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return typed mechanistic support over the current candidate slice."""
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    if ranked_items is None:
        core_ranked = fused_target_evidence(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            genetics_size=genetics_size,
            tractability_top_n=0,
            pathway_top_n=0,
            network_top_n=0,
        )[: max(candidate_limit, 0)]
    else:
        core_ranked = ranked_items[: max(candidate_limit, 0)]
    max_leakage_risk = _max_leakage_risk_for_mode(mode)
    edges = load_mechanistic_edges(benchmark_id, max_leakage_risk=max_leakage_risk)
    if not edges:
        return []

    disease_edge_weights = {
        edge["target"]["ref"]: float(edge["weight"])
        for edge in edges
        if edge["source"]["node_type"] == "disease"
    }
    gene_edges_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        if edge["source"]["node_type"] != "gene":
            continue
        gene_edges_by_symbol[edge["source"]["ref"]].append(edge)

    scored = []
    for item in core_ranked:
        gene_symbol = item.get("gene_symbol")
        ensembl_gene_id = item.get("ensembl_gene_id")
        if not gene_symbol or not ensembl_gene_id:
            continue
        gene_edges = gene_edges_by_symbol.get(gene_symbol, [])
        features = derive_mechanistic_support_features(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            disease_edge_weights=disease_edge_weights,
            gene_edges=gene_edges,
            max_leakage_risk=max_leakage_risk,
        )
        score = score_mechanistic_support(features)
        score["provenance"] = {
            "source_kind": "curated_mechanistic_edges",
            "max_leakage_risk": max_leakage_risk,
            "matched_mechanism_count": features["mechanistic_support_count"],
        }
        scored.append(score)

    scored.sort(key=lambda item: (item["score"], item["mechanistic_support_count"]), reverse=True)
    return scored


def _select_graph_candidates(
    *,
    benchmark_id: str,
    mode: str,
    subset_id: str,
    candidate_limit: int,
    genetics_size: int,
    mechanistic_seed_top_n: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    ranked_full = fused_target_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        genetics_size=genetics_size,
        tractability_top_n=0,
        pathway_top_n=0,
        network_top_n=0,
    )
    ranked_by_gene_id = {item["ensembl_gene_id"]: item for item in ranked_full if item.get("ensembl_gene_id")}
    selected_ids: list[str] = [
        item["ensembl_gene_id"]
        for item in ranked_full[: max(candidate_limit, 0)]
        if item.get("ensembl_gene_id")
    ]
    mechanistic_ranked = mechanistic_support_scores(
        benchmark_id,
        mode=mode,
        subset_id=subset_id,
        candidate_limit=len(ranked_full),
        genetics_size=genetics_size,
        ranked_items=ranked_full,
    )
    for item in mechanistic_ranked[: max(mechanistic_seed_top_n, 0)]:
        gene_id = item.get("ensembl_gene_id")
        if gene_id and gene_id not in selected_ids:
            selected_ids.append(gene_id)
    return [ranked_by_gene_id[gene_id] for gene_id in selected_ids if gene_id in ranked_by_gene_id], {
        item["ensembl_gene_id"]: item for item in mechanistic_ranked if item.get("ensembl_gene_id")
    }


def signaling_program_activity_scores(
    benchmark_id: str,
    *,
    subset_id: str,
    min_support: int = 1,
) -> list[dict[str, Any]]:
    """Return disease-specific signaling program activity derived from transcriptomics."""
    programs = load_signaling_programs(benchmark_id)
    if not programs:
        return []
    transcriptomics_items = transcriptomics_indication_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        min_support=min_support,
    )
    transcriptomics_by_symbol = {
        item["gene_symbol"]: item
        for item in transcriptomics_items
        if item.get("gene_symbol")
    }
    scored = []
    for program in programs:
        marker_hits = [
            transcriptomics_by_symbol[marker]
            for marker in program.get("marker_genes") or []
            if marker in transcriptomics_by_symbol
        ]
        features = derive_signaling_program_activity_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            program=program,
            marker_hits=marker_hits,
        )
        scored.append(score_signaling_program_activity(features))
    scored.sort(key=lambda item: (item["score"], item["positive_marker_count"]), reverse=True)
    return scored


def contrast_signaling_program_activity_scores(
    benchmark_id: str,
    *,
    subset_id: str,
) -> list[dict[str, Any]]:
    """Return per-contrast signaling program activity to preserve context-specific signal."""
    programs = load_signaling_programs(benchmark_id)
    if not programs:
        return []
    contrast_ids = sorted(
        contrast["contrast_id"]
        for contrast in query_study_contrasts(benchmark_id=benchmark_id, subset_id=subset_id)
        if contrast["contrast_id"].startswith(f"{subset_id}_")
    )
    scored = []
    for contrast_id in contrast_ids:
        by_symbol = {
            item["gene_symbol"]: {
                "gene_symbol": item["gene_symbol"],
                "score": item["score"],
                "weighted_mean_log2_fold_change": item["statistics"]["log2_fold_change"],
                "supporting_contrast_count": 1,
            }
            for item in transcriptomics_real_scores(contrast_id)
            if item.get("gene_symbol")
        }
        for program in programs:
            marker_hits = [
                by_symbol[marker]
                for marker in program.get("marker_genes") or []
                if marker in by_symbol
            ]
            features = derive_signaling_program_activity_features(
                benchmark_id=benchmark_id,
                subset_id=subset_id,
                program=program,
                marker_hits=marker_hits,
            )
            item = score_signaling_program_activity(features)
            item["contrast_id"] = contrast_id
            scored.append(item)
    scored.sort(key=lambda item: (item["score"], item["positive_marker_count"]), reverse=True)
    return scored


def cell_state_program_activity_scores(
    benchmark_id: str,
    *,
    subset_id: str,
    min_support: int = 1,
) -> list[dict[str, Any]]:
    """Return single-cell-derived cell-state activity from bulk transcriptomics."""
    programs = load_cell_state_programs(benchmark_id)
    if not programs:
        return []
    transcriptomics_items = transcriptomics_indication_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        min_support=min_support,
    )
    transcriptomics_by_symbol = {
        item["gene_symbol"]: item
        for item in transcriptomics_items
        if item.get("gene_symbol")
    }
    scored = []
    for program in programs:
        marker_hits = [
            transcriptomics_by_symbol[marker]
            for marker in program.get("marker_genes") or []
            if marker in transcriptomics_by_symbol
        ]
        features = derive_cell_state_program_activity_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            program=program,
            marker_hits=marker_hits,
        )
        scored.append(score_cell_state_program_activity(features))
    scored.sort(key=lambda item: (item["score"], len(item["linked_targets"])), reverse=True)
    return scored


def cell_state_support_scores(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    ranked_items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return gene support from active single-cell-derived cell-state programs."""
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    if ranked_items is None:
        ranked_items = fused_target_evidence(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            genetics_size=genetics_size,
            tractability_top_n=0,
            pathway_top_n=0,
            network_top_n=0,
        )
    ranked_slice = ranked_items[: max(candidate_limit, 0)]
    program_activity = cell_state_program_activity_scores(
        benchmark_id,
        subset_id=chosen_subset_id,
        min_support=1,
    )
    program_activity_by_ref = {item["program_ref"]: item for item in program_activity if item.get("program_ref")}
    if not program_activity_by_ref:
        return []

    scored = []
    for item in ranked_slice:
        gene_symbol = item.get("gene_symbol")
        ensembl_gene_id = item.get("ensembl_gene_id")
        if not gene_symbol or not ensembl_gene_id:
            continue
        features = derive_gene_cell_state_support_features(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            program_activity_by_ref=program_activity_by_ref,
        )
        if features["program_support_count"] <= 0:
            continue
        scored.append(score_cell_state_support(features))
    scored.sort(key=lambda item: (item["score"], item["program_support_count"]), reverse=True)
    return scored


def signaling_support_scores(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    ranked_items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return gene support from active signaling programs."""
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    if ranked_items is None:
        ranked_items = fused_target_evidence(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            genetics_size=genetics_size,
            tractability_top_n=0,
            pathway_top_n=0,
            network_top_n=0,
        )
    ranked_slice = ranked_items[: max(candidate_limit, 0)]
    program_activity = signaling_program_activity_scores(
        benchmark_id,
        subset_id=chosen_subset_id,
        min_support=1,
    )
    context_program_activity = contrast_signaling_program_activity_scores(
        benchmark_id,
        subset_id=chosen_subset_id,
    )
    program_activity_by_ref = {item["program_ref"]: item for item in program_activity if item.get("program_ref")}
    for item in context_program_activity:
        program_ref = item.get("program_ref")
        if not program_ref:
            continue
        current = program_activity_by_ref.get(program_ref)
        if current is None or float(item["score"]) > float(current["score"]):
            program_activity_by_ref[program_ref] = item
    if not program_activity_by_ref:
        return []

    gene_edges_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in load_mechanistic_edges(benchmark_id, max_leakage_risk=_max_leakage_risk_for_mode(mode)):
        if edge["source"]["node_type"] == "gene":
            gene_edges_by_symbol[edge["source"]["ref"]].append(edge)

    scored = []
    for item in ranked_slice:
        gene_symbol = item.get("gene_symbol")
        ensembl_gene_id = item.get("ensembl_gene_id")
        if not gene_symbol or not ensembl_gene_id:
            continue
        features = derive_gene_signaling_support_features(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            gene_edges=gene_edges_by_symbol.get(gene_symbol, []),
            program_activity_by_ref=program_activity_by_ref,
        )
        if features["program_support_count"] <= 0:
            continue
        scored.append(score_signaling_support(features))
    scored.sort(key=lambda item: (item["score"], item["program_support_count"]), reverse=True)
    return scored


def proteophospho_program_activity_scores(
    benchmark_id: str,
    *,
    subset_id: str,
) -> list[dict[str, Any]]:
    """Return curated proteomic and phosphosite program activity."""
    programs = load_proteophospho_programs(benchmark_id)
    if not programs:
        return []
    statistics = load_benchmark_proteophospho_statistics(benchmark_id)
    protein_markers = statistics.get("protein_markers") or {}
    phosphosite_markers = statistics.get("phosphosite_markers") or {}
    scored = []
    for program in programs:
        protein_hits = [
            protein_markers[marker["gene_symbol"]]
            for marker in program.get("protein_markers") or []
            if marker["gene_symbol"] in protein_markers
        ]
        phosphosite_hits = [
            phosphosite_markers[f"{marker['gene_symbol']}:{marker['site'].upper()}"]
            for marker in program.get("phosphosite_markers") or []
            if f"{marker['gene_symbol']}:{marker['site'].upper()}" in phosphosite_markers
        ]
        features = derive_proteophospho_program_activity_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            program=program,
            protein_hits=protein_hits,
            phosphosite_hits=phosphosite_hits,
        )
        scored.append(score_proteophospho_program_activity(features))
    scored.sort(
        key=lambda item: (
            item["score"],
            item["supported_phosphosite_count"],
            item["supported_protein_count"],
        ),
        reverse=True,
    )
    return scored


def proteophospho_support_scores(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    ranked_items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return target support from active proteo-phospho programs."""
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    if ranked_items is None:
        ranked_items = fused_target_evidence(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            genetics_size=genetics_size,
            tractability_top_n=0,
            pathway_top_n=0,
            network_top_n=0,
        )
    ranked_slice = ranked_items[: max(candidate_limit, 0)]
    program_activity_by_ref = {
        item["program_ref"]: item
        for item in proteophospho_program_activity_scores(
            benchmark_id,
            subset_id=chosen_subset_id,
        )
        if item.get("program_ref")
    }
    if not program_activity_by_ref:
        return []

    gene_edges_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in load_mechanistic_edges(benchmark_id, max_leakage_risk=_max_leakage_risk_for_mode(mode)):
        if edge["source"]["node_type"] == "gene":
            gene_edges_by_symbol[edge["source"]["ref"]].append(edge)

    scored = []
    for item in ranked_slice:
        gene_symbol = item.get("gene_symbol")
        ensembl_gene_id = item.get("ensembl_gene_id")
        if not gene_symbol or not ensembl_gene_id:
            continue
        features = derive_gene_proteophospho_support_features(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            gene_edges=gene_edges_by_symbol.get(gene_symbol, []),
            program_activity_by_ref=program_activity_by_ref,
        )
        if features["program_support_count"] <= 0:
            continue
        scored.append(score_proteophospho_support(features))
    scored.sort(key=lambda item: (item["score"], item["program_support_count"]), reverse=True)
    return scored


def build_benchmark_knowledge_graph(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    mechanistic_seed_top_n: int = 10,
    include_signaling: bool = True,
) -> dict[str, Any]:
    """Build a provenance-first benchmark slice knowledge graph."""
    assertion = load_benchmark_assertion(benchmark_id)
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]

    core_ranked, mechanistic_scores = _select_graph_candidates(
        benchmark_id=benchmark_id,
        mode=mode,
        subset_id=chosen_subset_id,
        candidate_limit=candidate_limit,
        genetics_size=genetics_size,
        mechanistic_seed_top_n=mechanistic_seed_top_n,
    )
    pathway_scores = [
        item
        for item in _cache_aware_pathway_scores(
            benchmark_id=benchmark_id,
            subset_id=chosen_subset_id,
            core_ranked=core_ranked,
            candidate_limit=candidate_limit,
        )
        if item.get("ensembl_gene_id")
    ]
    mechanistic_edges = load_mechanistic_edges(benchmark_id, max_leakage_risk=_max_leakage_risk_for_mode(mode))

    disease_node_id = f"disease:{benchmark_id}"
    nodes = {
        disease_node_id: {
            "id": disease_node_id,
            "type": "disease",
            "label": assertion["indication_name"],
            "attributes": {
                "benchmark_id": benchmark_id,
                "mode": mode,
                "subset_id": chosen_subset_id,
            },
        }
    }
    edges: list[dict[str, Any]] = []
    graph_gene_ids: set[str] = set()
    pathway_gene_weights: dict[str, dict[str, float]] = defaultdict(dict)
    disease_pathway_weights: dict[str, float] = {}
    gene_ids_by_symbol: dict[str, str] = {}

    for index, item in enumerate(core_ranked, start=1):
        gene_id = item["ensembl_gene_id"]
        if not gene_id or not item.get("gene_symbol"):
            continue
        graph_gene_ids.add(gene_id)
        gene_ids_by_symbol[item["gene_symbol"]] = gene_id
        gene_node_id = f"gene:{gene_id}"
        nodes[gene_node_id] = {
            "id": gene_node_id,
            "type": "gene",
            "label": item["gene_symbol"],
            "attributes": {
                "ensembl_gene_id": gene_id,
                "core_rank": index,
                "core_score": item["score"],
                "transcriptomics_available": item["transcriptomics_available"],
                "genetics_available": item["genetics_available"],
            },
        }
        if item["transcriptomics_available"]:
            edges.append(
                _edge(
                    disease_node_id,
                    gene_node_id,
                    "disease_gene_transcriptomics",
                    weight=float(item["components"]["transcriptomics_component"]),
                    evidence_family="transcriptomics",
                    provenance=item["transcriptomics_provenance"] or {},
                )
            )
        if item["genetics_available"]:
            edges.append(
                _edge(
                    disease_node_id,
                    gene_node_id,
                    "disease_gene_genetics",
                    weight=float(item["components"]["genetics_component"]),
                    evidence_family="genetics",
                    provenance=item["genetics_provenance"] or {},
                )
            )

    for edge in mechanistic_edges:
        source_meta = edge["source"]
        target_meta = edge["target"]
        mechanism_node_id = f"mechanism:{target_meta['ref']}"
        nodes[mechanism_node_id] = {
            "id": mechanism_node_id,
            "type": "mechanism",
            "label": target_meta["label"],
            "attributes": {
                "mechanism_ref": target_meta["ref"],
                "mechanism_kind": target_meta.get("mechanism_kind", "unknown"),
            },
        }
        if source_meta["node_type"] == "disease":
            edges.append(
                _edge(
                    disease_node_id,
                    mechanism_node_id,
                    edge["edge_type"],
                    weight=float(edge["weight"]),
                    evidence_family="mechanistic_graph",
                    provenance={"sources": edge.get("sources", [])},
                    leakage_risk=edge["leakage_risk"],
                )
            )
        elif source_meta["node_type"] == "gene":
            gene_id = gene_ids_by_symbol.get(source_meta["ref"])
            if not gene_id:
                continue
            edges.append(
                _edge(
                    f"gene:{gene_id}",
                    mechanism_node_id,
                    edge["edge_type"],
                    weight=float(edge["weight"]),
                    evidence_family="mechanistic_graph",
                    provenance={"sources": edge.get("sources", [])},
                    leakage_risk=edge["leakage_risk"],
                )
            )

    for item in pathway_scores:
        gene_id = item["ensembl_gene_id"]
        if gene_id not in graph_gene_ids:
            continue
        gene_node_id = f"gene:{gene_id}"
        for pathway in item["top_overlap_pathways"]:
            pathway_id = pathway["st_id"]
            pathway_node_id = f"pathway:{pathway_id}"
            pathway_weight = _bounded_log_score(float(pathway["fdr"]))
            nodes[pathway_node_id] = {
                "id": pathway_node_id,
                "type": "pathway",
                "label": pathway["name"],
                "attributes": {
                    "pathway_id": pathway_id,
                    "fdr": pathway["fdr"],
                },
            }
            disease_pathway_weights[pathway_node_id] = max(disease_pathway_weights.get(pathway_node_id, 0.0), pathway_weight)
            pathway_gene_weights[pathway_node_id][gene_id] = max(
                pathway_gene_weights[pathway_node_id].get(gene_id, 0.0),
                float(item["score"]),
            )
            edges.append(
                _edge(
                    pathway_node_id,
                    gene_node_id,
                    "pathway_gene_membership",
                    weight=float(item["score"]),
                    evidence_family="reactome_pathway",
                    provenance={
                        **(item.get("provenance") or {}),
                        "pathway_id": pathway_id,
                    },
                )
            )

    for pathway_node_id, weight in disease_pathway_weights.items():
        edges.append(
            _edge(
                disease_node_id,
                pathway_node_id,
                "disease_pathway_enrichment",
                weight=weight,
                evidence_family="reactome_pathway",
                provenance={
                    "source_kind": "reactome_analysis_service",
                },
            )
        )

    for pathway_node_id, gene_weights in pathway_gene_weights.items():
        genes = sorted(gene_weights)
        for left_index, left_gene_id in enumerate(genes):
            for right_gene_id in genes[left_index + 1 :]:
                left_node_id = f"gene:{left_gene_id}"
                right_node_id = f"gene:{right_gene_id}"
                shared_weight = min(gene_weights[left_gene_id], gene_weights[right_gene_id])
                edges.append(
                    _edge(
                        left_node_id,
                        right_node_id,
                        "shared_pathway_neighbor",
                        weight=shared_weight,
                        evidence_family="reactome_pathway",
                        provenance={
                            "pathway_node_id": pathway_node_id,
                        },
                    )
                )

    return {
        "benchmark_id": benchmark_id,
        "indication_name": assertion["indication_name"],
        "mode": mode,
        "subset_id": chosen_subset_id,
        "candidate_limit": candidate_limit,
        "graph": {
            "nodes": list(nodes.values()),
            "edges": edges,
        },
        "provenance": {
            "graph_kind": "benchmark_slice_knowledge_graph",
            "genetics_size": genetics_size,
            "mechanistic_seed_top_n": mechanistic_seed_top_n,
            "include_signaling": include_signaling,
            "candidate_source": "core_fused_target_evidence_without_graph_rerank",
        },
    }


def _adjacency(graph: dict[str, Any]) -> dict[str, list[tuple[str, float]]]:
    adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for edge in graph["edges"]:
        source = edge["source"]
        target = edge["target"]
        weight = float(edge["weight"])
        adjacency[source].append((target, weight))
        adjacency[target].append((source, weight))
    return adjacency


def _propagation_scores(graph: dict[str, Any], *, seed_node_id: str, restart: float = 0.25, steps: int = 20) -> dict[str, float]:
    adjacency = _adjacency(graph)
    nodes = [node["id"] for node in graph["nodes"]]
    scores = {node_id: 0.0 for node_id in nodes}
    scores[seed_node_id] = 1.0
    for _ in range(max(steps, 1)):
        updated = {node_id: 0.0 for node_id in nodes}
        updated[seed_node_id] += restart
        for node_id in nodes:
            neighbors = adjacency.get(node_id, [])
            total = sum(weight for _, weight in neighbors)
            if total <= 0.0:
                continue
            retained = (1.0 - restart) * scores[node_id]
            for neighbor_id, weight in neighbors:
                updated[neighbor_id] += retained * (weight / total)
        scores = updated
    return scores


def graph_feature_scores(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    mechanistic_seed_top_n: int = 10,
) -> list[dict[str, Any]]:
    """Compute transparent graph features for genes in one benchmark slice."""
    kg = build_benchmark_knowledge_graph(
        benchmark_id,
        mode=mode,
        subset_id=subset_id,
        candidate_limit=candidate_limit,
        genetics_size=genetics_size,
        mechanistic_seed_top_n=mechanistic_seed_top_n,
    )
    graph = kg["graph"]
    disease_node_id = f"disease:{benchmark_id}"
    propagation = _propagation_scores(graph, seed_node_id=disease_node_id)
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    adjacency = _adjacency(graph)
    mechanistic_scores = {
        item["ensembl_gene_id"]: item
        for item in mechanistic_support_scores(
            benchmark_id,
            mode=mode,
            subset_id=kg["subset_id"],
            candidate_limit=candidate_limit,
            genetics_size=genetics_size,
            ranked_items=[
                {
                    "ensembl_gene_id": node["attributes"]["ensembl_gene_id"],
                    "gene_symbol": node["label"],
                    "score": node["attributes"]["core_score"],
                    "transcriptomics_available": node["attributes"]["transcriptomics_available"],
                    "genetics_available": node["attributes"]["genetics_available"],
                }
                for node in graph["nodes"]
                if node["type"] == "gene"
            ],
        )
        if item.get("ensembl_gene_id")
    }
    signaling_scores = {
        item["ensembl_gene_id"]: item
        for item in signaling_support_scores(
            benchmark_id,
            mode=mode,
            subset_id=kg["subset_id"],
            candidate_limit=len(
                [node for node in graph["nodes"] if node["type"] == "gene"]
            ),
            genetics_size=genetics_size,
            ranked_items=[
                {
                    "ensembl_gene_id": node["attributes"]["ensembl_gene_id"],
                    "gene_symbol": node["label"],
                    "score": node["attributes"]["core_score"],
                    "transcriptomics_available": node["attributes"]["transcriptomics_available"],
                    "genetics_available": node["attributes"]["genetics_available"],
                }
                for node in graph["nodes"]
                if node["type"] == "gene"
            ],
        )
        if item.get("ensembl_gene_id")
    }
    cell_state_scores = {
        item["ensembl_gene_id"]: item
        for item in cell_state_support_scores(
            benchmark_id,
            mode=mode,
            subset_id=kg["subset_id"],
            candidate_limit=len(
                [node for node in graph["nodes"] if node["type"] == "gene"]
            ),
            genetics_size=genetics_size,
            ranked_items=[
                {
                    "ensembl_gene_id": node["attributes"]["ensembl_gene_id"],
                    "gene_symbol": node["label"],
                    "score": node["attributes"]["core_score"],
                    "transcriptomics_available": node["attributes"]["transcriptomics_available"],
                    "genetics_available": node["attributes"]["genetics_available"],
                }
                for node in graph["nodes"]
                if node["type"] == "gene"
            ],
        )
        if item.get("ensembl_gene_id")
    }
    proteophospho_scores = {
        item["ensembl_gene_id"]: item
        for item in proteophospho_support_scores(
            benchmark_id,
            mode=mode,
            subset_id=kg["subset_id"],
            candidate_limit=len([node for node in graph["nodes"] if node["type"] == "gene"]),
            genetics_size=genetics_size,
            ranked_items=[
                {
                    "ensembl_gene_id": node["attributes"]["ensembl_gene_id"],
                    "gene_symbol": node["label"],
                    "score": node["attributes"]["core_score"],
                    "transcriptomics_available": node["attributes"]["transcriptomics_available"],
                    "genetics_available": node["attributes"]["genetics_available"],
                }
                for node in graph["nodes"]
                if node["type"] == "gene"
            ],
        )
        if item.get("ensembl_gene_id")
    }

    disease_pathway_weights = {
        edge["target"]: float(edge["weight"])
        for edge in graph["edges"]
        if edge["type"] == "disease_pathway_enrichment"
    }
    disease_mechanism_weights = {
        edge["target"]: float(edge["weight"])
        for edge in graph["edges"]
        if edge["type"] == "disease_mechanism_support"
    }
    gene_base_scores = {
        node["id"]: float(node["attributes"]["core_score"])
        for node in graph["nodes"]
        if node["type"] == "gene"
    }

    scores = []
    for node in graph["nodes"]:
        if node["type"] != "gene":
            continue
        gene_node_id = node["id"]
        neighbors = adjacency.get(gene_node_id, [])
        pathway_neighbors = [neighbor_id for neighbor_id, _ in neighbors if nodes_by_id[neighbor_id]["type"] == "pathway"]
        mechanism_neighbors = [neighbor_id for neighbor_id, _ in neighbors if nodes_by_id[neighbor_id]["type"] == "mechanism"]
        gene_neighbors = [neighbor_id for neighbor_id, _ in neighbors if nodes_by_id[neighbor_id]["type"] == "gene"]

        disease_pathway_connectivity = sum(disease_pathway_weights.get(pathway_id, 0.0) for pathway_id in pathway_neighbors)
        disease_mechanism_connectivity = sum(disease_mechanism_weights.get(mechanism_id, 0.0) for mechanism_id in mechanism_neighbors)
        path_count = len(pathway_neighbors)
        mechanism_count = len(mechanism_neighbors)
        neighborhood_support = (
            sum(gene_base_scores.get(neighbor_id, 0.0) for neighbor_id in gene_neighbors) / len(gene_neighbors)
            if gene_neighbors
            else 0.0
        )
        propagation_score = propagation.get(gene_node_id, 0.0)
        mechanistic_score = mechanistic_scores.get(node["attributes"]["ensembl_gene_id"], {}).get("score", 0.0)
        signaling_score = signaling_scores.get(node["attributes"]["ensembl_gene_id"], {}).get("score", 0.0)
        cell_state_score = cell_state_scores.get(node["attributes"]["ensembl_gene_id"], {}).get("score", 0.0)
        proteophospho_score = proteophospho_scores.get(node["attributes"]["ensembl_gene_id"], {}).get("score", 0.0)
        graph_score = (
            0.15 * min(propagation_score * 10.0, 1.0)
            + 0.18 * min(disease_pathway_connectivity / 3.0, 1.0)
            + 0.05 * min(path_count / 5.0, 1.0)
            + 0.12 * min(neighborhood_support, 1.0)
            + 0.15 * min(disease_mechanism_connectivity / 3.0, 1.0)
            + 0.12 * min(float(mechanistic_score), 1.0)
            + 0.08 * min(float(signaling_score), 1.0)
            + 0.03 * min(float(cell_state_score), 1.0)
            + 0.12 * min(float(proteophospho_score), 1.0)
        )
        scores.append(
            {
                "benchmark_id": benchmark_id,
                "mode": mode,
                "subset_id": kg["subset_id"],
                "ensembl_gene_id": node["attributes"]["ensembl_gene_id"],
                "gene_symbol": node["label"],
                "score_name": "knowledge_graph_support_score",
                "score": round(graph_score, 4),
                "components": {
                    "propagation_component": round(0.15 * min(propagation_score * 10.0, 1.0), 4),
                    "disease_pathway_component": round(0.18 * min(disease_pathway_connectivity / 3.0, 1.0), 4),
                    "path_count_component": round(0.05 * min(path_count / 5.0, 1.0), 4),
                    "neighborhood_component": round(0.12 * min(neighborhood_support, 1.0), 4),
                    "disease_mechanism_component": round(0.15 * min(disease_mechanism_connectivity / 3.0, 1.0), 4),
                    "mechanistic_component": round(0.12 * min(float(mechanistic_score), 1.0), 4),
                    "signaling_component": round(0.08 * min(float(signaling_score), 1.0), 4),
                    "cell_state_component": round(0.03 * min(float(cell_state_score), 1.0), 4),
                    "proteophospho_component": round(0.12 * min(float(proteophospho_score), 1.0), 4),
                },
                "pathway_neighbor_count": path_count,
                "mechanism_neighbor_count": mechanism_count,
                "gene_neighbor_count": len(gene_neighbors),
                "disease_pathway_connectivity": round(disease_pathway_connectivity, 4),
                "disease_mechanism_connectivity": round(disease_mechanism_connectivity, 4),
                "signaling_score": round(float(signaling_score), 4),
                "cell_state_score": round(float(cell_state_score), 4),
                "proteophospho_score": round(float(proteophospho_score), 4),
                "propagation_score": round(propagation_score, 6),
                "provenance": kg["provenance"],
            }
        )

    scores.sort(key=lambda item: (item["score"], item["propagation_score"]), reverse=True)
    return scores


def graph_augmented_target_evidence(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    mechanistic_seed_top_n: int = 10,
) -> list[dict[str, Any]]:
    """Combine core fused evidence with transparent graph support."""
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    core_ranked, _ = _select_graph_candidates(
        benchmark_id=benchmark_id,
        mode=mode,
        subset_id=chosen_subset_id,
        candidate_limit=candidate_limit,
        genetics_size=genetics_size,
        mechanistic_seed_top_n=mechanistic_seed_top_n,
    )
    graph_scores = {
        item["ensembl_gene_id"]: item
        for item in graph_feature_scores(
            benchmark_id,
            mode=mode,
            subset_id=chosen_subset_id,
            candidate_limit=candidate_limit,
            genetics_size=genetics_size,
            mechanistic_seed_top_n=mechanistic_seed_top_n,
        )
    }
    ranked = []
    for item in core_ranked:
        graph_item = graph_scores.get(item["ensembl_gene_id"])
        graph_score = graph_item["score"] if graph_item else 0.0
        combined = (0.75 * float(item["score"])) + (0.25 * float(graph_score))
        ranked.append(
            {
                **item,
                "score_name": "graph_augmented_target_evidence_score",
                "score": round(combined, 4),
                "graph_score": graph_score,
                "components": {
                    **item["components"],
                    "graph_component": round(0.25 * float(graph_score), 4),
                },
            }
        )
    ranked.sort(key=lambda item: (item["score"], item["graph_score"]), reverse=True)
    return ranked


def evaluate_graph_augmented_benchmark(
    benchmark_id: str,
    *,
    mode: str = "strict",
    subset_id: str | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 200,
    mechanistic_seed_top_n: int = 10,
) -> dict[str, Any]:
    """Evaluate graph-augmented ranking against source-backed positives."""
    assertion = load_benchmark_assertion(benchmark_id)
    mode_config = benchmark_mode_config(benchmark_id, mode=mode)
    chosen_subset_id = subset_id or mode_config["subset_id"]
    ranked = graph_augmented_target_evidence(
        benchmark_id,
        mode=mode,
        subset_id=chosen_subset_id,
        candidate_limit=candidate_limit,
        genetics_size=genetics_size,
        mechanistic_seed_top_n=mechanistic_seed_top_n,
    )
    by_symbol = {item["gene_symbol"]: (index + 1, item) for index, item in enumerate(ranked) if item.get("gene_symbol")}
    items = []
    found_ranks = []
    for target in assertion["target_assertions"]:
        match = by_symbol.get(target["gene_symbol"])
        if match is None:
            items.append(
                {
                    "gene_symbol": target["gene_symbol"],
                    "found": False,
                    "rank": None,
                    "score": None,
                    "source": target["source"],
                }
            )
            continue
        rank, item = match
        found_ranks.append(rank)
        items.append(
            {
                "gene_symbol": target["gene_symbol"],
                "found": True,
                "rank": rank,
                "score": item["score"],
                "graph_score": item["graph_score"],
                "source": target["source"],
            }
        )
    return {
        "benchmark_id": benchmark_id,
        "mode": mode,
        "subset_id": chosen_subset_id,
        "candidate_limit": candidate_limit,
        "target_universe_size": len(ranked),
        "metrics": {
            "best_rank": min(found_ranks) if found_ranks else None,
            "hit_at_25": any(rank <= 25 for rank in found_ranks),
            "mean_reciprocal_rank": round(sum(1.0 / rank for rank in found_ranks) / len(found_ranks), 4) if found_ranks else 0.0,
        },
        "items": items,
        "provenance": {
            "ranking_kind": "graph_augmented_target_evidence",
            "candidate_limit": candidate_limit,
            "genetics_size": genetics_size,
            "mechanistic_seed_top_n": mechanistic_seed_top_n,
        },
    }
