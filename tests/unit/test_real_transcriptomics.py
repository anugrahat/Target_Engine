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
    parse_gene_count_matrix_text,
    parse_gene_count_text,
    parse_geo_platform_gene_symbols,
    parse_geo_series_matrix_table,
    parse_geo_series_samples,
    parse_xlsx_expression_sheet,
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

    def test_parses_gene_count_matrix_text(self) -> None:
        text = "\n".join(
            [
                "s_1\ts_2",
                "GENEA.chr1\t10\t20",
                "GENEB.chr2\t5\t8",
            ]
        )
        sample_titles, matrix = parse_gene_count_matrix_text(text)
        self.assertEqual(["s_1", "s_2"], sample_titles)
        self.assertEqual([10, 20], matrix["GENEA.chr1"])

    def test_parses_gene_count_matrix_text_with_csv_header(self) -> None:
        text = "\n".join(
            [
                "symbol,s_1,s_2",
                "TNIK,11,12",
                "A2M,20,25",
            ]
        )
        sample_titles, matrix = parse_gene_count_matrix_text(
            text,
            delimiter=",",
            has_gene_header=True,
        )
        self.assertEqual(["s_1", "s_2"], sample_titles)
        self.assertEqual([11, 12], matrix["TNIK"])

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

    def test_series_matrix_parser_skips_rows_with_blank_values(self) -> None:
        series_text = "\n".join(
            [
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSMN1"\t"GSMT1"',
                '"1007_s_at"\t5.0\t8.0',
                '"117_at"\t3.0\t',
                "!series_matrix_table_end",
            ]
        )
        sample_ids, rows = parse_geo_series_matrix_table(series_text)
        self.assertEqual(["GSMN1", "GSMT1"], sample_ids)
        self.assertEqual([("1007_s_at", [5.0, 8.0])], rows)

    def test_parses_illumina_platform_mapping_from_supplement(self) -> None:
        platform_text = "\n".join(
            [
                "[Heading]",
                "Date\t15/4/2010",
                "[Probes]",
                "Species\tProbe_Id\tSymbol",
                "Homo sapiens\tILMN_00001\tGENEA",
                "Homo sapiens\tILMN_00002\t---",
                "Homo sapiens\tILMN_00003\tGENEB",
            ]
        )
        mapping = parse_geo_platform_gene_symbols(platform_text)
        self.assertEqual({"ILMN_00001": "GENEA", "ILMN_00003": "GENEB"}, mapping)

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
            case_label="hepatocellular carcinoma",
            control_label="adjacent non-tumorous liver",
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
            case_label="tumor",
            control_label="normal",
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
        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_map",
            return_value=hgnc_map,
        ):
            records = load_real_geo_gene_statistics("ipf_lung_core_gse52463")
        self.assertEqual(3, len(records))
        mapped = next(record for record in records if record["gene"]["ensembl_gene_id"] == "ENSG000001")
        self.assertEqual("TESTGENE1", mapped["gene"]["symbol"])
        load_real_geo_gene_statistics.cache_clear()

    def test_loads_real_ipf_microarray_gene_statistics_with_patched_downloads(self) -> None:
        matrix_text = "\n".join(
            [
                '!Sample_title\t"Healthy donor 1"\t"Healthy donor 2"\t"Early IPF 1"\t"Advanced IPF 1"',
                '!Sample_geo_accession\t"GSMN1"\t"GSMN2"\t"GSMI1"\t"GSMI2"',
                '!Sample_characteristics_ch1\t"phenotype: healthy"\t"phenotype: healthy"\t"phenotype: early idiopathic pulmonary fibrosis (IPF)"\t"phenotype: advanced idiopathic pulmonary fibrosis (IPF)"',
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSMN1"\t"GSMN2"\t"GSMI1"\t"GSMI2"',
                '"1007_s_at"\t4.0\t4.2\t8.1\t8.4',
                '"117_at"\t3.1\t3.3\t5.6\t5.8',
                "!series_matrix_table_end",
            ]
        )
        platform_text = "\n".join(
            [
                "^Annotation",
                "#ID = ID from Platform data table",
                "#Gene symbol = Entrez Gene symbol",
                "1007_s_at\tGENEA",
                "117_at\tGENEB",
            ]
        )
        reverse_map = {
            "GENEA": {"ensembl_gene_id": "ENSG000001", "hgnc_id": "HGNC:1", "symbol": "GENEA"},
            "GENEB": {"ensembl_gene_id": "ENSG000002", "hgnc_id": "HGNC:2", "symbol": "GENEB"},
        }

        def fake_load_text(url: str, namespace: str) -> str:
            if url.endswith("GSE24206_series_matrix.txt.gz"):
                return matrix_text
            if url.endswith("GPL570.annot.gz"):
                return platform_text
            raise AssertionError(url)

        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_reverse_map",
            return_value=reverse_map,
        ):
            records = load_real_geo_gene_statistics("ipf_lung_core_gse24206")

        self.assertEqual(2, len(records))
        self.assertTrue(all(record["dataset_id"] == "GSE24206" for record in records))
        self.assertTrue(all(record["sample_counts"] == {"case": 2, "control": 2} for record in records))
        self.assertTrue(all(record["gene"]["symbol"] in {"GENEA", "GENEB"} for record in records))
        self.assertTrue(all(not record["provenance"]["paired_design"] for record in records))

    def test_loads_real_ipf_rnaseq_matrix_gene_statistics_with_patched_downloads(self) -> None:
        matrix_text = "\n".join(
            [
                '!Sample_title\t"s_1"\t"s_2"\t"s_3"\t"s_4"',
                '!Sample_geo_accession\t"GSM1"\t"GSM2"\t"GSM3"\t"GSM4"',
                '!Sample_characteristics_ch1\t"tissue: lung"\t"tissue: lung"\t"tissue: lung"\t"tissue: lung"',
                '!Sample_characteristics_ch1\t"disease state: Idiopathic Pulmonary Fibrosis"\t"disease state: Idiopathic Pulmonary Fibrosis"\t"disease state: Control"\t"disease state: Control"',
            ]
        )
        counts_text = "\n".join(
            [
                "s_1\ts_2\ts_3\ts_4",
                "TNIK.chr3\t100\t90\t40\t35",
                "A2M.chr12\t500\t520\t100\t120",
            ]
        )
        reverse_map = {
            "TNIK": {"ensembl_gene_id": "ENSG00000154310", "hgnc_id": "HGNC:11576", "symbol": "TNIK"},
            "A2M": {"ensembl_gene_id": "ENSG00000175899", "hgnc_id": "HGNC:7", "symbol": "A2M"},
        }
        symbol_map = {
            "ENSG00000154310": {"symbol": "TNIK", "hgnc_id": "HGNC:11576"},
            "ENSG00000175899": {"symbol": "A2M", "hgnc_id": "HGNC:7"},
        }

        def fake_load_text(url: str, namespace: str) -> str:
            if url.endswith("GSE92592_series_matrix.txt.gz"):
                return matrix_text
            if url.endswith("GSE92592_gene.counts.txt.gz"):
                return counts_text
            raise AssertionError(url)

        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_reverse_map",
            return_value=reverse_map,
        ), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_map",
            return_value=symbol_map,
        ):
            records = load_real_geo_gene_statistics("ipf_lung_core_gse92592")

        self.assertEqual(2, len(records))
        tnik = next(record for record in records if record["gene"]["symbol"] == "TNIK")
        self.assertEqual({"case": 2, "control": 2}, tnik["sample_counts"])
        self.assertEqual("geo_series_supplement_counts_matrix", tnik["provenance"]["source_kind"])
        self.assertEqual("HGNC:11576", tnik["gene"]["hgnc_id"])

    def test_loads_real_hcc_xlsx_expression_statistics_with_patched_downloads(self) -> None:
        sample_ids = ["S1N", "S1T", "S2N", "S2T"]
        sheet_rows = [
            {"symbol": "CDK20", "values": [2.0, 4.0, 2.5, 4.5]},
            {"symbol": "TP53", "values": [8.0, 9.0, 8.5, 9.4]},
        ]
        reverse_map = {
            "CDK20": {"ensembl_gene_id": "ENSG00000156345", "hgnc_id": "HGNC:1778", "symbol": "CDK20"},
            "TP53": {"ensembl_gene_id": "ENSG00000141510", "hgnc_id": "HGNC:11998", "symbol": "TP53"},
        }

        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_bytes_with_cache", return_value=b"fixture"), patch(
            "prioritx_data.real_transcriptomics.parse_xlsx_expression_sheet",
            return_value=(sample_ids, sheet_rows),
        ), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_reverse_map",
            return_value=reverse_map,
        ):
            records = load_real_geo_gene_statistics("hcc_adult_core_gse77314")

        self.assertEqual(2, len(records))
        cdk20 = next(record for record in records if record["gene"]["symbol"] == "CDK20")
        self.assertEqual({"case": 2, "control": 2}, cdk20["sample_counts"])
        self.assertEqual("geo_expression_workbook", cdk20["provenance"]["source_kind"])
        self.assertTrue(cdk20["provenance"]["paired_design"])

    def test_loads_real_ipf_extended_matrix_statistics_with_patched_downloads(self) -> None:
        matrix_text = "\n".join(
            [
                '!Sample_title\t"ipf_1"\t"ipf_2"\t"control_1"\t"control_2"\t"chp_1"',
                '!Sample_geo_accession\t"GSM1"\t"GSM2"\t"GSM3"\t"GSM4"\t"GSM5"',
                '!Sample_characteristics_ch1\t"diagnosis: ipf"\t"diagnosis: ipf"\t"diagnosis: control"\t"diagnosis: control"\t"diagnosis: chp"',
            ]
        )
        counts_text = "\n".join(
            [
                "symbol,ipf_1,ipf_2,control_1,control_2,chp_1",
                "TNIK,100,90,40,35,20",
                "A2M,500,520,100,120,95",
            ]
        )
        reverse_map = {
            "TNIK": {"ensembl_gene_id": "ENSG00000154310", "hgnc_id": "HGNC:11576", "symbol": "TNIK"},
            "A2M": {"ensembl_gene_id": "ENSG00000175899", "hgnc_id": "HGNC:7", "symbol": "A2M"},
        }
        symbol_map = {
            "ENSG00000154310": {"symbol": "TNIK", "hgnc_id": "HGNC:11576"},
            "ENSG00000175899": {"symbol": "A2M", "hgnc_id": "HGNC:7"},
        }

        def fake_load_text(url: str, namespace: str) -> str:
            if url.endswith("GSE150910_series_matrix.txt.gz"):
                return matrix_text
            if url.endswith("GSE150910_gene-level_count_file.csv.gz"):
                return counts_text
            raise AssertionError(url)

        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_reverse_map",
            return_value=reverse_map,
        ), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_map",
            return_value=symbol_map,
        ):
            records = load_real_geo_gene_statistics("ipf_lung_extended_gse150910")

        self.assertEqual(2, len(records))
        tnik = next(record for record in records if record["gene"]["symbol"] == "TNIK")
        self.assertEqual({"case": 2, "control": 2}, tnik["sample_counts"])
        self.assertEqual("geo_series_supplement_counts_matrix", tnik["provenance"]["source_kind"])

    def test_loads_real_hcc_extended_microarray_statistics_with_patched_downloads(self) -> None:
        matrix_text = "\n".join(
            [
                '!Sample_title\t"5617835061_H"\t"5617835061_J"\t"5617835104_C"\t"5617835176_L"',
                '!Sample_geo_accession\t"GSMN1"\t"GSMN2"\t"GSMT1"\t"GSMT2"',
                '!Sample_characteristics_ch1\t"tissue: adjacent non-tumor liver"\t"tissue: adjacent non-tumor liver"\t"tissue: liver tumor"\t"tissue: liver tumor"',
                "!series_matrix_table_begin",
                '"ID_REF"\t"GSMN1"\t"GSMN2"\t"GSMT1"\t"GSMT2"',
                '"ILMN_00001"\t4.2\t4.4\t7.8\t8.0',
                '"ILMN_00002"\t6.5\t6.7\t6.6\t6.8',
                "!series_matrix_table_end",
            ]
        )
        platform_text = "\n".join(
            [
                "[Heading]",
                "Date\t15/4/2010",
                "[Probes]",
                "Species\tProbe_Id\tSymbol",
                "Homo sapiens\tILMN_00001\tCCRK",
                "Homo sapiens\tILMN_00002\tTP53",
            ]
        )
        reverse_map = {
            "CCRK": {
                "ensembl_gene_id": "ENSG00000156345",
                "hgnc_id": "HGNC:1778",
                "symbol": "CDK20",
                "match_type": "prev_symbol",
            },
            "TP53": {"ensembl_gene_id": "ENSG00000141510", "hgnc_id": "HGNC:11998", "symbol": "TP53"},
        }

        def fake_load_text(url: str, namespace: str) -> str:
            if url.endswith("GSE36376_series_matrix.txt.gz"):
                return matrix_text
            if url.endswith("GPL10558_HumanHT-12_V4_0_R2_15002873_B.txt.gz"):
                return platform_text
            raise AssertionError(url)

        load_real_geo_gene_statistics.cache_clear()
        with patch("prioritx_data.real_transcriptomics.load_text_with_cache", side_effect=fake_load_text), patch(
            "prioritx_data.real_transcriptomics.load_hgnc_symbol_reverse_map",
            return_value=reverse_map,
        ):
            records = load_real_geo_gene_statistics("hcc_adult_extended_gse36376")

        self.assertEqual(2, len(records))
        cdk20 = next(record for record in records if record["gene"]["symbol"] == "CDK20")
        self.assertEqual({"case": 2, "control": 2}, cdk20["sample_counts"])
        self.assertFalse(cdk20["provenance"]["paired_design"])
        self.assertEqual(["CCRK"], cdk20["provenance"]["source_gene_symbols"])
        self.assertEqual("GSE36376", cdk20["dataset_id"])


if __name__ == "__main__":
    unittest.main()
