"""Command-line summary for generated PrioriTx registry fixtures."""

from __future__ import annotations

from prioritx_data.registry import group_by_benchmark, list_dataset_manifests, list_study_contrasts
from prioritx_data.service import list_benchmark_subsets


def main() -> int:
    dataset_manifests = list_dataset_manifests()
    study_contrasts = list_study_contrasts()
    subsets = list_benchmark_subsets()

    print(f"Dataset manifests: {len(dataset_manifests)}")
    for benchmark_id, artifacts in sorted(group_by_benchmark(dataset_manifests).items()):
        print(f"- {benchmark_id}: {len(artifacts)}")

    print(f"Study contrasts: {len(study_contrasts)}")
    for benchmark_id, artifacts in sorted(group_by_benchmark(study_contrasts).items()):
        print(f"- {benchmark_id}: {len(artifacts)}")

    print(f"Curated subsets: {len(subsets)}")
    for subset in subsets:
        print(f"- {subset['subset_id']}: {subset['benchmark_id']} ({len(subset['included_datasets'])} included datasets)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
