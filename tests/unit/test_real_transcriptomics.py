from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from prioritx_data.real_transcriptomics import (
    GeoSample,
    _student_t_two_sided_p_value,
    build_microarray_gene_statistics,
    build_real_gene_statistics,
    load_real_geo_gene_statistics,
    parse_gene_count_text,
    parse_geo_platform_gene_symbols,
    parse_geo_series_matrix_table,
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

    def test_builds_inferential_rnaseq_gene_statistics(self) -> None:
        case_samples = [
            GeoSample("GSMI1", "IPF1", "Idiopathic pulmonary fibrosis", "fixture://ipf1"),
            GeoSample("GSMI2", "IPF2", "Idiopathic pulmonary fibrosis", "fixture://ipf2"),
        ]
        control_samples = [
            GeoSample("GSMN1", "Norm1", "normal", "fixture://norm1"),
            GeoSample("GSMN2", "Norm2", "normal", "fixture://norm2"),
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
        target = next(item for item in scored if item["ensembl_gene_id"] == "ENSG000001")
        self.assertGreater(target["score"], 0.0)
        self.assertEqual("real_transcriptomics_inferential_score", target["score_name"])
        source = next(record for record in records if record["gene"]["ensembl_gene_id"] == "ENSG000001")
        self.assertIn("adjusted_p_value", source["statistics"])
        self.assertIn("degrees_of_freedom", source["statistics"])
        self.assertGreater(source["statistics"]["degrees_of_freedom"], 0.0)

    def test_parses_platform_mapping_and_matrix_table(self) -> None:
        platform_text = "\n".join(
            [
                "^Annotation",
                "#ID = ID from Platform data table",
                "#Gene symbol = Entrez Gene symbol",
                "1007_s_at\tGENEA",
                "1053_at\tGENEB /// MIR0001",
                "117_at\tGENEC",
            ]
        )
        mapping = parse_geo_platform_gene_symbols(platform_text)
        self.assertEqual({"1007_s_at": "GENEA", "117_at": "GENEC"}, mapping)

        series_text = "\n".join(
            [
                '!Sample_title\t"HCC001N"\t"HCC001T"',
                '!Sample_geo_accession\t"GSMN1"\t"GSMT1"',
                '!Sample_characteristics_ch1\t"tissue type: adjacent non-tumorous liver"\t"tissue type: hepatocellular carcinoma"',
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSMN1"\t"GSMT1"',
                '"1007_s_at"\t5.0\t8.0',
                '"117_at"\t3.0\t4.0',
                "!series_matrix_table_end",
            ]
        )
        sample_ids, rows = parse_geo_series_matrix_table(series_text)
        self.assertEqual(["GSMN1", "GSMT1"], sample_ids)
        self.assertEqual("1007_s_at", rows[0][0])

    def test_builds_paired_microarray_gene_statistics(self) -> None:
        samples = [
            GeoSample("GSMN1", "HCC001N", "adjacent non-tumorous liver", ""),
            GeoSample("GSMT1", "HCC001T", "hepatocellular carcinoma", ""),
            GeoSample("GSMN2", "HCC002N", "adjacent non-tumorous liver", ""),
            GeoSample("GSMT2", "HCC002T", "hepatocellular carcinoma", ""),
        ]
        sample_ids = ["GSMN1", "GSMT1", "GSMN2", "GSMT2"]
        gene_rows = [
            {
                "ensembl_gene_id": "ENSG000001",
                "symbol": "GENEA",
                "hgnc_id": "HGNC:1",
                "probe_ids": ["1007_s_at"],
                "probe_count": 1,
                "values": [5.0, 8.0, 5.5, 8.2],
            }
        ]
        records = build_microarray_gene_statistics(
            contrast_id="hcc_adult_core_gse60502",
            benchmark_id="hcc_cdk20",
            dataset_id="GSE60502",
            samples=samples,
            sample_ids=sample_ids,
            gene_rows=gene_rows,
            paired_design=True,
        )
        self.assertEqual(1, len(records))
        self.assertGreater(records[0]["statistics"]["log2_fold_change"], 0.0)
        self.assertIn("adjusted_p_value", records[0]["statistics"])
        self.assertEqual(1.0, records[0]["statistics"]["degrees_of_freedom"])
        self.assertTrue(records[0]["provenance"]["paired_design"])

    def test_builds_unpaired_microarray_gene_statistics(self) -> None:
        samples = [
            GeoSample("GSMN1", "normal 1", "Normal", ""),
            GeoSample("GSMN2", "normal 2", "Normal", ""),
            GeoSample("GSMT1", "tumor 1", "Tumor", ""),
            GeoSample("GSMT2", "tumor 2", "Tumor", ""),
        ]
        sample_ids = ["GSMN1", "GSMN2", "GSMT1", "GSMT2"]
        gene_rows = [
            {
                "ensembl_gene_id": "ENSG000001",
                "symbol": "GENEA",
                "hgnc_id": "HGNC:1",
                "probe_ids": ["1007_s_at"],
                "probe_count": 1,
                "values": [4.8, 5.1, 8.0, 8.2],
            }
        ]
        records = build_microarray_gene_statistics(
            contrast_id="hcc_adult_core_gse45267",
            benchmark_id="hcc_cdk20",
            dataset_id="GSE45267",
            samples=samples,
            sample_ids=sample_ids,
            gene_rows=gene_rows,
            paired_design=False,
        )
        self.assertEqual(1, len(records))
        self.assertFalse(records[0]["provenance"]["paired_design"])
        self.assertGreater(records[0]["statistics"]["degrees_of_freedom"], 0.0)

    def test_student_t_two_sided_p_value_matches_known_reference(self) -> None:
        p_value = _student_t_two_sided_p_value(2.228, 10.0)
        self.assertAlmostEqual(0.05, p_value, delta=0.003)

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
        mapped = next(record for record in records if record["gene"]["ensembl_gene_id"] == "ENSG000001")
        self.assertEqual("TESTGENE1", mapped["gene"]["symbol"])


if __name__ == "__main__":
    unittest.main()
