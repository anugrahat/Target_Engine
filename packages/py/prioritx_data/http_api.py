"""Dependency-free read-only HTTP surface for registry fixtures."""

from __future__ import annotations

from typing import Any

from prioritx_data.service import (
    benchmark_index,
    get_subset,
    list_benchmark_subsets,
    query_dataset_manifests,
    query_study_contrasts,
)


def _single(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def handle_get(path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, Any]]:
    """Return status code plus JSON payload for a read-only GET route."""
    if path == "/":
        return 200, {
            "service": "prioritx-registry-api",
            "routes": [
                "/health",
                "/benchmarks",
                "/subsets",
                "/subsets/{subset_id}",
                "/dataset-manifests",
                "/study-contrasts",
            ],
        }

    if path == "/health":
        return 200, {"status": "ok"}

    if path == "/benchmarks":
        return 200, {"items": benchmark_index()}

    if path == "/subsets":
        benchmark_id = _single(query, "benchmark_id")
        subsets = list_benchmark_subsets()
        if benchmark_id:
            subsets = [subset for subset in subsets if subset["benchmark_id"] == benchmark_id]
        return 200, {"items": subsets}

    if path.startswith("/subsets/"):
        subset_id = path.split("/", 2)[2]
        subset = get_subset(subset_id)
        if subset is None:
            return 404, {"error": f"Unknown subset: {subset_id}"}
        return 200, subset

    if path == "/dataset-manifests":
        return 200, {
            "items": query_dataset_manifests(
                benchmark_id=_single(query, "benchmark_id"),
                subset_id=_single(query, "subset_id"),
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
            )
        }

    if path == "/study-contrasts":
        return 200, {
            "items": query_study_contrasts(
                benchmark_id=_single(query, "benchmark_id"),
                subset_id=_single(query, "subset_id"),
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
            )
        }

    return 404, {"error": f"Unknown route: {path}"}
