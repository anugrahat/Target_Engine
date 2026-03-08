"""Query services for curated PrioriTx registry fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.registry import RegistryArtifact, list_dataset_manifests, list_study_contrasts, repo_root
from prioritx_features.transcriptomics import derive_contrast_quality_features
from prioritx_rank.baseline import score_contrast_readiness


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
