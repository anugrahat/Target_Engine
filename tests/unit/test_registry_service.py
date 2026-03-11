from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.service import (
    benchmark_index,
    contrast_readiness_scores,
    get_subset,
    fused_target_evidence,
    list_benchmark_subsets,
    query_dataset_manifests,
    query_study_contrasts,
    open_targets_genetics_scores,
    open_targets_tractability_scores,
    transcriptomics_indication_evidence,
    transcriptomics_fixture_scores,
    transcriptomics_real_scores,
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

    def test_returns_gene_scores_for_fixture_contrast(self) -> None:
        items = transcriptomics_fixture_scores("ipf_lung_core_gse92592")
        self.assertEqual(5, len(items))
        self.assertEqual("fixture_transcriptomics_gene_score", items[0]["score_name"])

    def test_returns_real_scores_for_supported_contrast(self) -> None:
        mocked_records = [
            {
                "contrast_id": "ipf_lung_core_gse52463",
                "benchmark_id": "ipf_tnik",
                "dataset_id": "GSE52463",
                "gene": {"ensembl_gene_id": "ENSG000001", "symbol": None},
                "evidence_kind": "accession_backed_real",
                "statistics": {
                    "log2_fold_change": 1.8,
                    "standardized_mean_difference": 2.1,
                    "adjusted_p_value": 0.001,
                    "mean_raw_count": 120.0,
                },
                "sample_counts": {"case": 8, "control": 7},
                "provenance": {"series_accession": "GSE52463"},
            }
        ]
        with patch("prioritx_data.service.load_real_geo_gene_statistics", return_value=mocked_records):
            items = transcriptomics_real_scores("ipf_lung_core_gse52463")
        self.assertEqual(1, len(items))
        self.assertEqual("real_transcriptomics_inferential_score", items[0]["score_name"])

    def test_aggregates_cross_contrast_evidence(self) -> None:
        contrast_records = {
            "hcc_adult_core_gse60502": [
                {
                    "contrast_id": "hcc_adult_core_gse60502",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE60502",
                    "gene": {"ensembl_gene_id": "ENSG000001", "symbol": "GENE1", "hgnc_id": "HGNC:1"},
                    "statistics": {
                        "log2_fold_change": 1.2,
                        "adjusted_p_value": 0.001,
                        "standardized_mean_difference": 1.5,
                    },
                    "sample_counts": {"case": 18, "control": 18},
                },
                {
                    "contrast_id": "hcc_adult_core_gse60502",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE60502",
                    "gene": {"ensembl_gene_id": "ENSG000002", "symbol": "GENE2", "hgnc_id": "HGNC:2"},
                    "statistics": {
                        "log2_fold_change": 0.9,
                        "adjusted_p_value": 0.01,
                        "standardized_mean_difference": 1.2,
                    },
                    "sample_counts": {"case": 18, "control": 18},
                },
            ],
            "hcc_adult_core_gse45267": [
                {
                    "contrast_id": "hcc_adult_core_gse45267",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE45267",
                    "gene": {"ensembl_gene_id": "ENSG000001", "symbol": "GENE1", "hgnc_id": "HGNC:1"},
                    "statistics": {
                        "log2_fold_change": 1.0,
                        "adjusted_p_value": 0.003,
                        "standardized_mean_difference": 1.3,
                    },
                    "sample_counts": {"case": 48, "control": 39},
                },
                {
                    "contrast_id": "hcc_adult_core_gse45267",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE45267",
                    "gene": {"ensembl_gene_id": "ENSG000002", "symbol": "GENE2", "hgnc_id": "HGNC:2"},
                    "statistics": {
                        "log2_fold_change": -0.8,
                        "adjusted_p_value": 0.02,
                        "standardized_mean_difference": 1.1,
                    },
                    "sample_counts": {"case": 48, "control": 39},
                },
                {
                    "contrast_id": "hcc_adult_core_gse45267",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE45267",
                    "gene": {"ensembl_gene_id": "ENSG000003", "symbol": "GENE3", "hgnc_id": "HGNC:3"},
                    "statistics": {
                        "log2_fold_change": 0.3,
                        "adjusted_p_value": 0.2,
                        "standardized_mean_difference": 0.2,
                    },
                    "sample_counts": {"case": 48, "control": 39},
                },
            ],
        }

        def fake_load(contrast_id: str) -> list[dict[str, object]]:
            return contrast_records.get(contrast_id, [])

        with patch("prioritx_data.service.load_real_geo_gene_statistics", side_effect=fake_load):
            items = transcriptomics_indication_evidence(subset_id="hcc_adult_core")

        self.assertEqual(2, len(items))
        self.assertEqual("cross_contrast_transcriptomics_evidence_score", items[0]["score_name"])
        self.assertEqual("ENSG000001", items[0]["ensembl_gene_id"])
        self.assertEqual(2, items[0]["supporting_contrast_count"])
        self.assertFalse(items[0]["direction_conflict"])
        self.assertTrue(items[1]["direction_conflict"])

    def test_cross_contrast_evidence_respects_min_support(self) -> None:
        contrast_records = {
            "hcc_adult_core_gse60502": [
                {
                    "contrast_id": "hcc_adult_core_gse60502",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE60502",
                    "gene": {"ensembl_gene_id": "ENSG000001", "symbol": "GENE1", "hgnc_id": "HGNC:1"},
                    "statistics": {
                        "log2_fold_change": 1.2,
                        "adjusted_p_value": 0.001,
                        "standardized_mean_difference": 1.5,
                    },
                    "sample_counts": {"case": 18, "control": 18},
                }
            ],
            "hcc_adult_core_gse45267": [
                {
                    "contrast_id": "hcc_adult_core_gse45267",
                    "benchmark_id": "hcc_cdk20",
                    "dataset_id": "GSE45267",
                    "gene": {"ensembl_gene_id": "ENSG000001", "symbol": "GENE1", "hgnc_id": "HGNC:1"},
                    "statistics": {
                        "log2_fold_change": 1.0,
                        "adjusted_p_value": 0.003,
                        "standardized_mean_difference": 1.3,
                    },
                    "sample_counts": {"case": 48, "control": 39},
                }
            ],
        }

        def fake_load(contrast_id: str) -> list[dict[str, object]]:
            return contrast_records.get(contrast_id, [])

        with patch("prioritx_data.service.load_real_geo_gene_statistics", side_effect=fake_load):
            items = transcriptomics_indication_evidence(subset_id="hcc_adult_core", min_support=2)

        self.assertEqual(1, len(items))
        self.assertEqual(2, items[0]["supporting_contrast_count"])

    def test_returns_open_targets_genetics_scores(self) -> None:
        mocked_records = [
            {
                "benchmark_id": "ipf_tnik",
                "disease": {"id": "EFO_0000768", "name": "idiopathic pulmonary fibrosis"},
                "gene": {
                    "ensembl_gene_id": "ENSG000001",
                    "symbol": "GENE1",
                    "approved_name": "Gene one",
                },
                "statistics": {
                    "association_score": 0.82,
                    "genetic_association_score": 0.91,
                    "genetic_literature_score": 0.4,
                    "literature_score": 0.1,
                },
                "provenance": {"source_kind": "open_targets_graphql"},
                "evidence_kind": "open_targets_genetics",
            }
        ]
        with patch("prioritx_data.service.load_open_targets_genetics", return_value=mocked_records):
            items = open_targets_genetics_scores("ipf_tnik", size=25)

        self.assertEqual(1, len(items))
        self.assertEqual("open_targets_genetics_evidence_score", items[0]["score_name"])

    def test_returns_open_targets_tractability_scores(self) -> None:
        mocked_records = [
            {
                "gene": {"ensembl_gene_id": "ENSG000001", "symbol": "GENE1", "approved_name": "Gene one"},
                "tractability": [{"label": "High-Quality Ligand", "modality": "SM", "value": True}],
                "provenance": {"source_kind": "open_targets_graphql"},
                "evidence_kind": "open_targets_tractability",
            }
        ]
        with patch("prioritx_data.service.load_open_targets_tractability", return_value=mocked_records):
            items = open_targets_tractability_scores(["ENSG000001"])

        self.assertEqual(1, len(items))
        self.assertEqual("open_targets_tractability_score", items[0]["score_name"])

    def test_fuses_transcriptomics_and_genetics(self) -> None:
        transcriptomics_items = [
            {
                "benchmark_id": "ipf_tnik",
                "subset_id": "ipf_lung_core",
                "ensembl_gene_id": "ENSG000001",
                "gene_symbol": "GENE1",
                "score": 0.8,
                "supporting_contrast_count": 2,
                "direction_conflict": False,
                "evidence_kind": "cross_contrast_real_transcriptomics",
                "source_contrast_ids": ["ipf_lung_core_gse52463", "ipf_lung_core_gse24206"],
                "support_rule": {"max_adjusted_p_value": 0.05, "min_absolute_log2_fold_change": 0.5},
            }
        ]
        genetics_items = [
            {
                "benchmark_id": "ipf_tnik",
                "disease_id": "EFO_0000768",
                "ensembl_gene_id": "ENSG000001",
                "gene_symbol": "GENE1",
                "score": 0.9,
                "evidence_kind": "open_targets_genetics",
                "statistics": {"genetic_association_score": 0.95},
            }
        ]
        tractability_items = [
            {
                "ensembl_gene_id": "ENSG000001",
                "gene_symbol": "GENE1",
                "score": 0.6,
                "positive_modalities": ["SM"],
                "positive_bucket_count": 1,
                "positive_buckets": [{"modality": "SM", "label": "High-Quality Ligand", "weight": 0.65}],
                "evidence_kind": "open_targets_tractability",
            }
        ]
        with patch("prioritx_data.service.transcriptomics_indication_evidence", return_value=transcriptomics_items), patch(
            "prioritx_data.service.open_targets_genetics_scores",
            return_value=genetics_items,
        ), patch(
            "prioritx_data.service.open_targets_tractability_scores",
            return_value=tractability_items,
        ):
            items = fused_target_evidence(benchmark_id="ipf_tnik", subset_id="ipf_lung_core", genetics_size=25)

        self.assertEqual(1, len(items))
        self.assertEqual("fused_target_evidence_score", items[0]["score_name"])
        self.assertTrue(items[0]["transcriptomics_available"])
        self.assertTrue(items[0]["genetics_available"])
        self.assertTrue(items[0]["tractability_available"])


if __name__ == "__main__":
    unittest.main()
