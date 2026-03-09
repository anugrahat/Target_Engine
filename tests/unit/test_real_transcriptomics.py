from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from prioritx_data.real_transcriptomics import (
    GeoCountSample,
    build_real_gene_statistics,
    load_real_geo_gene_statistics,
    parse_gene_count_text,
    parse_geo_series_samples,
)
from prioritx_features.transcriptomics import derive_real_gene_transcriptomics_features
from prioritx_rank.baseline import score_real_gene_transcriptomics


class RealTranscriptomicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "geo"

    def test_parses_geo_series_samples(self) -> None:
        text = (self.fixture_dir / "gse52463_series_matrix_minimal.txt").read_text()
        samples = parse_geo_series_samples(text)
        self.assertEqual(4, len(samples))
        self.assertEqual("GSMN1", samples[0].geo_accession)
        self.assertEqual("normal", samples[0].phenotype)
        self.assertTrue(samples[0].supplementary_gene_url.startswith("https://ftp.ncbi.nlm.nih.gov"))

    def test_parses_gene_count_text(self) -> None:
        text = (self.fixture_dir / "gsm_norm1.genes.txt").read_text()
        counts = parse_gene_count_text(text)
        self.assertEqual(100, counts["ENSG000001"])
        self.assertEqual(3, len(counts))

    def test_builds_scored_real_gene_statistics(self) -> None:
        case_samples = [
            GeoCountSample("GSMI1", "IPF1", "Idiopathic pulmonary fibrosis", "fixture://ipf1"),
            GeoCountSample("GSMI2", "IPF2", "Idiopathic pulmonary fibrosis", "fixture://ipf2"),
        ]
        control_samples = [
            GeoCountSample("GSMN1", "Norm1", "normal", "fixture://norm1"),
            GeoCountSample("GSMN2", "Norm2", "normal", "fixture://norm2"),
        ]
        sample_counts = {
            "GSMN1": parse_gene_count_text((self.fixture_dir / "gsm_norm1.genes.txt").read_text()),
            "GSMN2": parse_gene_count_text((self.fixture_dir / "gsm_norm2.genes.txt").read_text()),
            "GSMI1": parse_gene_count_text((self.fixture_dir / "gsm_ipf1.genes.txt").read_text()),
            "GSMI2": parse_gene_count_text((self.fixture_dir / "gsm_ipf2.genes.txt").read_text()),
        }
        records = build_real_gene_statistics(
            contrast_id="ipf_lung_core_gse52463",
            benchmark_id="ipf_tnik",
            dataset_id="GSE52463",
            case_samples=case_samples,
            control_samples=control_samples,
            sample_counts=sample_counts,
        )
        scored = [
            score_real_gene_transcriptomics(derive_real_gene_transcriptomics_features(record))
            for record in records
        ]
        target = next(
            item for item in scored if item["ensembl_gene_id"] == "ENSG000001"
        )
        self.assertGreater(target["score"], 0.0)
        self.assertEqual("real_transcriptomics_effect_score", target["score_name"])

    def test_loads_real_geo_gene_statistics_with_patched_downloads(self) -> None:
        matrix_text = (self.fixture_dir / "gse52463_series_matrix_minimal.txt").read_text()
        gene_texts = {
            "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSMNnnn/GSMN1/suppl/GSMN1_Norm1.genes.txt.gz": (self.fixture_dir / "gsm_norm1.genes.txt").read_text(),
            "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSMNnnn/GSMN2/suppl/GSMN2_Norm2.genes.txt.gz": (self.fixture_dir / "gsm_norm2.genes.txt").read_text(),
            "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSMInnn/GSMI1/suppl/GSMI1_IPF1.genes.txt.gz": (self.fixture_dir / "gsm_ipf1.genes.txt").read_text(),
            "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSMInnn/GSMI2/suppl/GSMI2_IPF2.genes.txt.gz": (self.fixture_dir / "gsm_ipf2.genes.txt").read_text(),
        }

        def fake_load_text(url: str, namespace: str) -> str:
            if url.endswith("GSE52463_series_matrix.txt.gz"):
                return matrix_text
            return gene_texts[url]

        hgnc_map = {"ENSG000001": {"symbol": "TESTGENE1", "hgnc_id": "HGNC:1000"}}
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_map",
            return_value=hgnc_map,
        ):
            records = load_real_geo_gene_statistics("ipf_lung_core_gse52463")
        self.assertEqual(3, len(records))
        self.assertTrue(all(record["evidence_kind"] == "accession_backed_real" for record in records))
        mapped = next(record for record in records if record["gene"]["ensembl_gene_id"] == "ENSG000001")
        self.assertEqual("TESTGENE1", mapped["gene"]["symbol"])


if __name__ == "__main__":
    unittest.main()
