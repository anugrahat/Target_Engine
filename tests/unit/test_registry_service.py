from __future__ import annotations

import unittest

from prioritx_data.service import (
    benchmark_index,
    contrast_readiness_scores,
    get_subset,
    list_benchmark_subsets,
    query_dataset_manifests,
    query_study_contrasts,
)


class RegistryServiceTests(unittest.TestCase):
    def test_lists_curated_subsets(self) -> None:
        subsets = list_benchmark_subsets()
        subset_ids = {subset["subset_id"] for subset in subsets}
        self.assertEqual({"ipf_lung_core", "hcc_adult_core"}, subset_ids)

    def test_filters_dataset_manifests_by_subset(self) -> None:
        items = query_dataset_manifests(subset_id="ipf_lung_core")
        self.assertEqual(5, len(items))
        self.assertTrue(all(item["dataset_id"].startswith("ipf_lung_core_") for item in items))

    def test_filters_study_contrasts_by_benchmark_and_tissue(self) -> None:
        items = query_study_contrasts(benchmark_id="hcc_cdk20", tissue="liver")
        self.assertEqual(4, len(items))

    def test_returns_subset_definition(self) -> None:
        subset = get_subset("hcc_adult_core")
        self.assertIsNotNone(subset)
        self.assertEqual("hcc_cdk20", subset["benchmark_id"])

    def test_builds_benchmark_index(self) -> None:
        rows = {row["benchmark_id"]: row for row in benchmark_index()}
        self.assertEqual(["hcc_adult_core"], rows["hcc_cdk20"]["subset_ids"])
        self.assertEqual(["ipf_lung_core"], rows["ipf_tnik"]["subset_ids"])

    def test_returns_sorted_contrast_readiness_scores(self) -> None:
        items = contrast_readiness_scores(subset_id="hcc_adult_core")
        self.assertEqual(4, len(items))
        self.assertGreaterEqual(items[0]["score"], items[-1]["score"])


if __name__ == "__main__":
    unittest.main()
