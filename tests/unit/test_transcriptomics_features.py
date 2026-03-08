from __future__ import annotations

import unittest

from prioritx_data.transcriptomics import load_transcriptomics_fixture
from prioritx_data.service import query_study_contrasts
from prioritx_features.transcriptomics import derive_contrast_quality_features, derive_gene_transcriptomics_features
from prioritx_rank.baseline import score_contrast_readiness, score_gene_transcriptomics


class TranscriptomicsFeatureTests(unittest.TestCase):
    def test_derives_expected_features_for_ipf_controlled_contrast(self) -> None:
        contrast = query_study_contrasts(subset_id="ipf_lung_core")[0]
        features = derive_contrast_quality_features(contrast)
        self.assertGreater(features["total_samples"], 0)
        self.assertEqual(1, features["bulk_rna"])
        self.assertEqual("ipf_tnik", features["benchmark_id"])

    def test_adjacent_control_penalty_for_hcc(self) -> None:
        contrast = next(
            item
            for item in query_study_contrasts(subset_id="hcc_adult_core")
            if item["contrast_id"] == "hcc_adult_core_gse60502"
        )
        features = derive_contrast_quality_features(contrast)
        self.assertEqual(1, features["adjacent_control"])
        score = score_contrast_readiness(features)
        self.assertLess(score["components"]["adjacent_penalty"], 0)

    def test_tcga_curated_public_arm_gets_penalty(self) -> None:
        contrast = next(
            item
            for item in query_study_contrasts(subset_id="hcc_adult_core")
            if item["contrast_id"] == "hcc_adult_core_tcga_lihc"
        )
        features = derive_contrast_quality_features(contrast)
        self.assertEqual(1, features["curated_public_arm"])
        score = score_contrast_readiness(features)
        self.assertLess(score["components"]["curated_public_arm_penalty"], 0)

    def test_gene_level_fixture_features_and_scores(self) -> None:
        record = load_transcriptomics_fixture("hcc_adult_core_gse77314")[0]
        features = derive_gene_transcriptomics_features(record)
        self.assertEqual("CDK20", features["gene_symbol"])
        score = score_gene_transcriptomics(features)
        self.assertGreater(score["score"], 0)


if __name__ == "__main__":
    unittest.main()
