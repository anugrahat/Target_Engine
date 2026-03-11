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
from prioritx_data.real_transcriptomics import list_real_contrast_ids, load_real_geo_gene_statistics
from prioritx_data.registry import RegistryArtifact, list_dataset_manifests, list_study_contrasts, repo_root
from prioritx_data.transcriptomics import list_fixture_contrast_ids, load_transcriptomics_fixture
from prioritx_features.fusion import derive_fused_target_evidence_features
from prioritx_features.genetics import derive_open_targets_genetics_features
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
    score_cross_contrast_transcriptomics_evidence,
    score_contrast_readiness,
    score_gene_transcriptomics,
    score_real_gene_transcriptomics,
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


def fused_target_evidence(
    *,
    benchmark_id: str,
    subset_id: str | None = None,
    min_transcriptomics_support: int = 1,
    genetics_size: int = 200,
    tractability_top_n: int = 500,
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

    scored = []
    for gene_id in gene_ids:
        features = derive_fused_target_evidence_features(
            benchmark_id=benchmark_id,
            subset_id=subset_id,
            transcriptomics=transcriptomics_by_gene.get(gene_id),
            genetics=genetics_by_gene.get(gene_id),
            tractability=tractability_by_gene.get(gene_id),
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
