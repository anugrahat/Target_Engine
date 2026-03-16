from __future__ import annotations

import unittest

from prioritx_data.registry import (
    group_by_benchmark,
    list_dataset_manifests,
    list_study_contrasts,
    repo_root,
)


class RegistryFixtureTests(unittest.TestCase):
    def test_repo_root_contains_contracts(self) -> None:
        self.assertTrue((repo_root() / "data_contracts" / "registries").exists())

    def test_dataset_manifests_are_generated(self) -> None:
        manifests = list_dataset_manifests()
        self.assertEqual(35, len(manifests))
        grouped = group_by_benchmark(manifests)
        self.assertEqual(18, len(grouped["als_pandaomics"]))
        self.assertEqual(9, len(grouped["ipf_tnik"]))
        self.assertEqual(8, len(grouped["hcc_cdk20"]))

    def test_study_contrasts_are_generated(self) -> None:
        contrasts = list_study_contrasts()
        self.assertEqual(35, len(contrasts))
        grouped = group_by_benchmark(contrasts)
        self.assertEqual(18, len(grouped["als_pandaomics"]))
        self.assertEqual(9, len(grouped["ipf_tnik"]))
        self.assertEqual(8, len(grouped["hcc_cdk20"]))

    def test_tcga_lihc_curated_public_arm_is_present(self) -> None:
        tcga = [
            artifact
            for artifact in list_study_contrasts()
            if artifact.payload["dataset_ids"] == ["TCGA-LIHC"]
        ]
        self.assertEqual(1, len(tcga))
        self.assertEqual(377, tcga[0].payload["sample_counts"]["case"])
        self.assertEqual(89, tcga[0].payload["sample_counts"]["control"])


if __name__ == "__main__":
    unittest.main()
