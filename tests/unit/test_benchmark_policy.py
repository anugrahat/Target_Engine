from __future__ import annotations

import unittest

from prioritx_eval.policy import benchmark_integrity_review, benchmark_mode_config


class BenchmarkPolicyTests(unittest.TestCase):
    def test_strict_mode_uses_default_subset(self) -> None:
        config = benchmark_mode_config("ipf_tnik", mode="strict")
        self.assertEqual("ipf_lung_core", config["subset_id"])
        self.assertEqual(40, config["pathway_top_n"])

    def test_exploratory_mode_uses_extended_subset_when_available(self) -> None:
        config = benchmark_mode_config("hcc_cdk20", mode="exploratory")
        self.assertEqual("hcc_adult_extended", config["subset_id"])
        self.assertEqual(80, config["pathway_top_n"])

    def test_integrity_review_lists_high_risk_literature_family(self) -> None:
        review = benchmark_integrity_review("ipf_tnik", mode="strict")
        families = {item["family"]: item for item in review["families"]}
        self.assertEqual("high", families["pubmed_literature"]["risk_level"])
        self.assertFalse(families["pubmed_literature"]["included_in_fused_ranking"])


if __name__ == "__main__":
    unittest.main()
