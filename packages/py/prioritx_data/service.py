"""Query services for curated PrioriTx registry fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.open_targets import (
    list_open_targets_benchmark_ids,
    load_open_targets_genetics,
    load_open_targets_tractability,
)
from prioritx_data.pubmed import load_pubmed_gene_support
from prioritx_data.reactome import load_reactome_gene_pathways, load_reactome_pathway_enrichment
from prioritx_data.real_transcriptomics import list_real_contrast_ids, load_real_geo_gene_statistics
from prioritx_data.registry import RegistryArtifact, list_dataset_manifests, list_study_contrasts, repo_root
from prioritx_data.string_network import load_string_id_map, load_string_network_edges
from prioritx_data.transcriptomics import list_fixture_contrast_ids, load_transcriptomics_fixture
from prioritx_features.fusion import derive_fused_target_evidence_features
from prioritx_features.genetics import derive_open_targets_genetics_features
from prioritx_features.network import derive_string_network_features
from prioritx_features.pathway import derive_reactome_pathway_features
from prioritx_features.literature import derive_pubmed_literature_features
from prioritx_features.tractability import derive_open_targets_tractability_features
from prioritx_features.transcriptomics import (
    derive_contrast_quality_features,
    derive_gene_transcriptomics_features,
    derive_real_gene_evidence_features,
    derive_real_gene_transcriptomics_features,
)
from prioritx_rank.baseline import (
    score_fused_target_evidence,
    score_open_targets_genetics,
    score_open_targets_tractability,
    score_pubmed_literature_support,
    score_reactome_pathway_support,
    score_cross_contrast_transcriptomics_evidence,
    score_contrast_readiness,
    score_gene_transcriptomics,
    score_real_gene_transcriptomics,
    score_string_network_support,
)


def _subset_example_dir() -> Path:
    return repo_root() / "data_contracts" / "examples"


def list_benchmark_subsets() -> list[dict[str, Any]]:
    """Load curated benchmark subset example records."""
    subset_paths = sorted(_subset_example_dir().glob("benchmark_subset.*.json"))
    return [json.loads(path.read_text()) for path in subset_paths]


def _matches_filter(artifact: RegistryArtifact, subset_id: str | None, tissue: str | None, modality: str | None) -> bool:
    payload = artifact.payload
    if subset_id and not payload.get("dataset_id", payload.get("contrast_id", "")).startswith(f"{subset_id}_"):
        return False
    if tissue and payload.get("tissue") != tissue:
        return False
    if modality and payload.get("modality") != modality:
        return False
    return True


def query_dataset_manifests(
    *,
    benchmark_id: str | None = None,
    subset_id: str | None = None,
    tissue: str | None = None,
    modality: str | None = None,
) -> list[dict[str, Any]]:
    """Return dataset manifests filtered by benchmark, subset, tissue, or modality."""
    manifests = list_dataset_manifests()
    results = []
    for artifact in manifests:
        if benchmark_id and artifact.benchmark_id != benchmark_id:
            continue
        if not _matches_filter(artifact, subset_id, tissue, modality):
            continue
        results.append(artifact.payload)
    return results


def query_study_contrasts(
    *,
    benchmark_id: str | None = None,
    subset_id: str | None = None,
    tissue: str | None = None,
    modality: str | None = None,
) -> list[dict[str, Any]]:
    """Return study contrasts filtered by benchmark, subset, tissue, or modality."""
    contrasts = list_study_contrasts()
    results = []
    for artifact in contrasts:
        if benchmark_id and artifact.benchmark_id != benchmark_id:
            continue
        if not _matches_filter(artifact, subset_id, tissue, modality):
            continue
        results.append(artifact.payload)
    return results


def get_subset(subset_id: str) -> dict[str, Any] | None:
    """Return one curated subset definition by id."""
    for subset in list_benchmark_subsets():
        if subset["subset_id"] == subset_id:
            return subset
    return None


def benchmark_index() -> list[dict[str, Any]]:
    """Summarize available benchmarks, subsets, and generated registry fixtures."""
    subsets = list_benchmark_subsets()
    manifests = list_dataset_manifests()
    contrasts = list_study_contrasts()
    benchmark_ids = sorted({artifact.benchmark_id for artifact in manifests + contrasts})

    rows: list[dict[str, Any]] = []
    for benchmark_id in benchmark_ids:
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "dataset_manifest_count": len([artifact for artifact in manifests if artifact.benchmark_id == benchmark_id]),
                "study_contrast_count": len([artifact for artifact in contrasts if artifact.benchmark_id == benchmark_id]),
                "subset_ids": sorted([subset["subset_id"] for subset in subsets if subset["benchmark_id"] == benchmark_id]),
            }
        )
    return rows


def contrast_readiness_scores(
    *,
    benchmark_id: str | None = None,
    subset_id: str | None = None,
    tissue: str | None = None,
    modality: str | None = None,
) -> list[dict[str, Any]]:
    """Compute metadata-derived readiness scores for filtered study contrasts."""
    contrasts = query_study_contrasts(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        tissue=tissue,
        modality=modality,
    )
    scored = [
        score_contrast_readiness(derive_contrast_quality_features(contrast))
        for contrast in contrasts
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def transcriptomics_fixture_scores(contrast_id: str) -> list[dict[str, Any]]:
    """Compute illustrative gene-level scores for one fixture contrast."""
    if contrast_id not in set(list_fixture_contrast_ids()):
        return []

    records = load_transcriptomics_fixture(contrast_id)
    scored = [
        score_gene_transcriptomics(derive_gene_transcriptomics_features(record))
        for record in records
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def transcriptomics_real_scores(contrast_id: str) -> list[dict[str, Any]]:
    """Compute accession-backed gene-level scores for one supported contrast."""
    if contrast_id not in set(list_real_contrast_ids()):
        return []

    records = load_real_geo_gene_statistics(contrast_id)
    scored = [
        {
            **score_real_gene_transcriptomics(derive_real_gene_transcriptomics_features(record)),
            "statistics": record["statistics"],
            "sample_counts": record["sample_counts"],
            "provenance": record["provenance"],
        }
        for record in records
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def open_targets_genetics_scores(benchmark_id: str, *, size: int = 200) -> list[dict[str, Any]]:
    """Return scored Open Targets genetics evidence for one benchmark disease."""
    if benchmark_id not in set(list_open_targets_benchmark_ids()):
        return []

    records = load_open_targets_genetics(benchmark_id, size=size)
    scored = [
        {
            **score_open_targets_genetics(derive_open_targets_genetics_features(record)),
            "statistics": record["statistics"],
            "provenance": record["provenance"],
        }
        for record in records
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def open_targets_tractability_scores(ensembl_gene_ids: list[str]) -> list[dict[str, Any]]:
    """Return scored Open Targets tractability evidence for a set of genes."""
    records = load_open_targets_tractability(ensembl_gene_ids)
    scored = [
        {
            **score_open_targets_tractability(derive_open_targets_tractability_features(record)),
            "provenance": record["provenance"],
        }
        for record in records
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def string_network_scores(
    *,
    benchmark_id: str,
    subset_id: str | None = None,
    candidate_gene_map: dict[str, str],
    seed_symbols: list[str],
    partner_limit: int = 50,
) -> list[dict[str, Any]]:
    """Return STRING network support scores for a candidate symbol slice."""
    candidate_symbols = list(candidate_gene_map)
    symbol_map = load_string_id_map(candidate_symbols)
    string_id_to_symbol = {payload["string_id"]: symbol for symbol, payload in symbol_map.items()}
    edges = load_string_network_edges([payload["string_id"] for payload in symbol_map.values()], limit=partner_limit)

    filtered_edges: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbol_map}
    candidate_set = set(candidate_symbols)
    seed_set = set(seed_symbols)
    for edge in edges:
        source_symbol = string_id_to_symbol.get(edge.get("stringId_A"))
        partner_symbol = string_id_to_symbol.get(edge.get("stringId_B")) or edge.get("preferredName_B")
        if source_symbol is None or partner_symbol not in candidate_set:
            continue
        filtered_edges[source_symbol].append(
            {
                "partner_symbol": partner_symbol,
                "score": float(edge.get("score") or 0.0),
                "preferredName_A": source_symbol,
                "preferredName_B": partner_symbol,
            }
        )

    scored = []
    for symbol in candidate_symbols:
        if symbol not in symbol_map:
            continue
        features = derive_string_network_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            gene={
                "ensembl_gene_id": candidate_gene_map[symbol],
                "gene_symbol": symbol,
            },
            edges=filtered_edges.get(symbol, []),
            seed_gene_symbols=seed_set,
        )
        item = score_string_network_support(features)
        item["provenance"] = {
            "source_kind": "string_api_v12",
            "api_base": "https://version-12-0.string-db.org/api/json",
            "partner_limit": partner_limit,
        }
        scored.append(item)
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def _filtered_real_contrast_ids(
    *,
    benchmark_id: str | None = None,
    subset_id: str | None = None,
    tissue: str | None = None,
    modality: str | None = None,
) -> list[str]:
    real_contrast_ids = set(list_real_contrast_ids())
    filtered = query_study_contrasts(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        tissue=tissue,
        modality=modality,
    )
    return sorted(
        contrast["contrast_id"]
        for contrast in filtered
        if contrast["contrast_id"] in real_contrast_ids
    )


def transcriptomics_indication_evidence(
    *,
    benchmark_id: str | None = None,
    subset_id: str | None = None,
    tissue: str | None = None,
    modality: str | None = None,
    min_support: int = 1,
) -> list[dict[str, Any]]:
    """Aggregate real transcriptomics evidence across contrasts for one indication slice."""
    contrast_ids = _filtered_real_contrast_ids(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        tissue=tissue,
        modality=modality,
    )
    if not contrast_ids:
        return []

    resolved_benchmark_id = benchmark_id
    if resolved_benchmark_id is None:
        contrasts = query_study_contrasts(subset_id=subset_id, tissue=tissue, modality=modality)
        benchmark_ids = {contrast["benchmark_id"] for contrast in contrasts if contrast["contrast_id"] in set(contrast_ids)}
        resolved_benchmark_id = sorted(benchmark_ids)[0] if benchmark_ids else None

    grouped_records: dict[str, list[dict[str, Any]]] = {}
    for contrast_id in contrast_ids:
        for record in load_real_geo_gene_statistics(contrast_id):
            gene_id = record["gene"].get("ensembl_gene_id")
            if not gene_id:
                continue
            grouped_records.setdefault(gene_id, []).append(record)

    scored = []
    for records in grouped_records.values():
        features = derive_real_gene_evidence_features(
            benchmark_id=resolved_benchmark_id or records[0]["benchmark_id"],
            subset_id=subset_id,
            total_real_contrasts=len(contrast_ids),
            records=records,
        )
        if int(features["supporting_contrast_count"]) < max(min_support, 1):
            continue
        scored.append(score_cross_contrast_transcriptomics_evidence(features))

    scored.sort(
        key=lambda item: (
            item["score"],
            item["supporting_contrast_count"],
            -item["best_adjusted_p_value"],
        ),
        reverse=True,
    )
    return scored


def pubmed_literature_scores(
    *,
    benchmark_id: str,
    subset_id: str | None = None,
    candidate_top_n: int = 100,
) -> list[dict[str, Any]]:
    """Return PubMed disease-gene support for the current candidate slice."""
    transcriptomics_items = transcriptomics_indication_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        min_support=1,
    )
    genetics_items = open_targets_genetics_scores(benchmark_id, size=candidate_top_n)

    candidate_map: dict[str, str | None] = {}
    for item in transcriptomics_items[: max(candidate_top_n, 0)]:
        if item.get("gene_symbol"):
            candidate_map[item["gene_symbol"]] = item.get("ensembl_gene_id")
    for item in genetics_items[: max(candidate_top_n, 0)]:
        if item.get("gene_symbol"):
            candidate_map.setdefault(item["gene_symbol"], item.get("ensembl_gene_id"))

    scored = []
    for gene_symbol, ensembl_gene_id in sorted(candidate_map.items()):
        record = load_pubmed_gene_support(benchmark_id, gene_symbol, ensembl_gene_id)
        item = score_pubmed_literature_support(derive_pubmed_literature_features(record))
        item["provenance"] = record["provenance"]
        scored.append(item)

    scored.sort(key=lambda item: (item["score"], item["pubmed_count"]), reverse=True)
    return scored


def reactome_pathway_scores(
    *,
    benchmark_id: str,
    subset_id: str | None = None,
    min_support: int = 1,
    enrichment_gene_limit: int = 300,
    candidate_top_n: int = 200,
    enrichment_fdr_max: float = 0.05,
) -> list[dict[str, Any]]:
    """Return Reactome pathway-overlap support for the top candidate slice."""
    transcriptomics_items = transcriptomics_indication_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        min_support=min_support,
    )
    if not transcriptomics_items:
        return []

    enrichment_gene_symbols = tuple(
        item["gene_symbol"]
        for item in transcriptomics_items[: max(enrichment_gene_limit, 0)]
        if item.get("gene_symbol")
    )
    enriched_pathways = [
        item
        for item in load_reactome_pathway_enrichment(enrichment_gene_symbols)
        if item["pathway"].get("species_name") == "Homo sapiens"
        and float(item["statistics"]["fdr"]) <= enrichment_fdr_max
    ]
    if not enriched_pathways:
        return []

    genetics_items = open_targets_genetics_scores(benchmark_id, size=candidate_top_n)
    candidate_gene_map: dict[str, str] = {}
    for item in transcriptomics_items[: max(candidate_top_n, 0)]:
        if item.get("gene_symbol") and item.get("ensembl_gene_id"):
            candidate_gene_map[item["gene_symbol"]] = item["ensembl_gene_id"]
    for item in genetics_items[: max(candidate_top_n, 0)]:
        if item.get("gene_symbol") and item.get("ensembl_gene_id"):
            candidate_gene_map.setdefault(item["gene_symbol"], item["ensembl_gene_id"])

    scored = []
    for gene_symbol, ensembl_gene_id in sorted(candidate_gene_map.items()):
        gene_pathways = load_reactome_gene_pathways(gene_symbol)
        features = derive_reactome_pathway_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            gene={"ensembl_gene_id": ensembl_gene_id, "gene_symbol": gene_symbol},
            enriched_pathways=enriched_pathways,
            gene_pathways=gene_pathways,
            enrichment_gene_count=len(enrichment_gene_symbols),
            enrichment_fdr_max=enrichment_fdr_max,
        )
        item = score_reactome_pathway_support(features)
        item["provenance"] = {
            "source_kind": "reactome_analysis_service",
            "api_url": "https://reactome.org/AnalysisService/identifiers/projection",
            "candidate_identifier": gene_symbol,
        }
        scored.append(item)

    scored.sort(key=lambda item: (item["score"], item["overlap_count"]), reverse=True)
    return scored


def fused_target_evidence(
    *,
    benchmark_id: str,
    subset_id: str | None = None,
    min_transcriptomics_support: int = 1,
    genetics_size: int = 200,
    tractability_top_n: int = 500,
    pathway_top_n: int = 200,
    network_top_n: int = 100,
) -> list[dict[str, Any]]:
    """Fuse transcriptomics and Open Targets genetics evidence by Ensembl gene."""
    transcriptomics_items = transcriptomics_indication_evidence(
        benchmark_id=benchmark_id,
        subset_id=subset_id,
        min_support=min_transcriptomics_support,
    )
    genetics_items = open_targets_genetics_scores(benchmark_id, size=genetics_size)

    transcriptomics_by_gene = {item["ensembl_gene_id"]: item for item in transcriptomics_items}
    genetics_by_gene = {item["ensembl_gene_id"]: item for item in genetics_items}
    gene_ids = sorted(set(transcriptomics_by_gene) | set(genetics_by_gene))

    base_scored = []
    for gene_id in gene_ids:
        features = derive_fused_target_evidence_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            transcriptomics=transcriptomics_by_gene.get(gene_id),
            genetics=genetics_by_gene.get(gene_id),
            tractability=None,
            pathway=None,
            network=None,
        )
        base_scored.append(score_fused_target_evidence(features))

    base_scored.sort(
        key=lambda item: (
            item["score"],
            item["transcriptomics_supporting_contrasts"],
            item["genetics_available"],
        ),
        reverse=True,
    )
    tractability_gene_ids = [item["ensembl_gene_id"] for item in base_scored[: max(tractability_top_n, 0)]]
    tractability_by_gene = {item["ensembl_gene_id"]: item for item in open_targets_tractability_scores(tractability_gene_ids)}
    pathway_by_gene = {
        item["ensembl_gene_id"]: item
        for item in reactome_pathway_scores(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            min_support=min_transcriptomics_support,
            candidate_top_n=pathway_top_n,
        )
    }
    network_candidates = base_scored[: max(network_top_n, 0)]
    network_by_gene = {
        item["gene_symbol"]: item
        for item in string_network_scores(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            candidate_gene_map={
                item["gene_symbol"]: item["ensembl_gene_id"]
                for item in network_candidates
                if item.get("gene_symbol")
            },
            seed_symbols=[item["gene_symbol"] for item in base_scored[:20] if item.get("gene_symbol")],
        )
    }

    scored = []
    for gene_id in gene_ids:
        transcriptomics_item = transcriptomics_by_gene.get(gene_id)
        genetics_item = genetics_by_gene.get(gene_id)
        tractability_item = tractability_by_gene.get(gene_id)
        symbol = (transcriptomics_item or genetics_item or tractability_item or {}).get("gene_symbol")
        features = derive_fused_target_evidence_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            transcriptomics=transcriptomics_item,
            genetics=genetics_item,
            tractability=tractability_item,
            pathway=pathway_by_gene.get(gene_id),
            network=network_by_gene.get(symbol) if symbol else None,
        )
        scored.append(score_fused_target_evidence(features))

    scored.sort(
        key=lambda item: (
            item["score"],
            item["transcriptomics_supporting_contrasts"],
            item["genetics_available"],
        ),
        reverse=True,
    )
    return scored
