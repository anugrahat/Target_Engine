"""Access official GEO transcriptomics inputs for curated PrioriTx contrasts."""

from __future__ import annotations

import csv
import functools
import io
import math
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from statistics import fmean, stdev
from typing import Any

from prioritx_data.hgnc import load_hgnc_symbol_map, load_hgnc_symbol_reverse_map
from prioritx_data.remote_cache import load_bytes_with_cache, load_text_with_cache, normalize_geo_url

REAL_CONTRASTS: dict[str, dict[str, str]] = {
    "ipf_lung_core_gse52463": {
        "source_type": "geo_rnaseq_counts",
        "series_accession": "GSE52463",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE52463",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "normal",
    },
    "ipf_lung_extended_gse52463": {
        "source_type": "geo_rnaseq_counts",
        "series_accession": "GSE52463",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE52463",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "normal",
    },
    "ipf_lung_core_gse24206": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE24206",
        "platform_accession": "GPL570",
        "design": "unpaired",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE24206",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "healthy",
    },
    "ipf_lung_extended_gse24206": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE24206",
        "platform_accession": "GPL570",
        "design": "unpaired",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE24206",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "healthy",
    },
    "ipf_lung_core_gse92592": {
        "source_type": "geo_rnaseq_matrix_counts",
        "series_accession": "GSE92592",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE92592",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "control",
        "supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE92nnn/GSE92592/suppl/GSE92592_gene.counts.txt.gz",
    },
    "ipf_lung_extended_gse92592": {
        "source_type": "geo_rnaseq_matrix_counts",
        "series_accession": "GSE92592",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE92592",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "control",
        "supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE92nnn/GSE92592/suppl/GSE92592_gene.counts.txt.gz",
    },
    "ipf_lung_extended_gse150910": {
        "source_type": "geo_rnaseq_matrix_counts",
        "series_accession": "GSE150910",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE150910",
        "case_label": "ipf",
        "control_label": "control",
        "supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE150nnn/GSE150910/suppl/GSE150910_gene-level_count_file.csv.gz",
        "delimiter": ",",
        "has_gene_header": True,
    },
    "hcc_adult_core_gse60502": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE60502",
        "platform_accession": "GPL96",
        "design": "paired",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE60502",
        "case_label": "hepatocellular carcinoma",
        "control_label": "adjacent non-tumorous liver",
    },
    "hcc_adult_extended_gse60502": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE60502",
        "platform_accession": "GPL96",
        "design": "paired",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE60502",
        "case_label": "hepatocellular carcinoma",
        "control_label": "adjacent non-tumorous liver",
    },
    "hcc_adult_core_gse45267": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE45267",
        "platform_accession": "GPL570",
        "design": "unpaired",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE45267",
        "case_label": "tumor",
        "control_label": "normal",
    },
    "hcc_adult_extended_gse45267": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE45267",
        "platform_accession": "GPL570",
        "design": "unpaired",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE45267",
        "case_label": "tumor",
        "control_label": "normal",
    },
    "hcc_adult_core_gse77314": {
        "source_type": "geo_xlsx_expression_matrix",
        "series_accession": "GSE77314",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE77314",
        "case_label": "tumor",
        "control_label": "normal",
        "supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE77nnn/GSE77314/suppl/GSE77314_expression.xlsx",
        "sheet_path": "xl/worksheets/sheet5.xml",
    },
    "hcc_adult_extended_gse77314": {
        "source_type": "geo_xlsx_expression_matrix",
        "series_accession": "GSE77314",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE77314",
        "case_label": "tumor",
        "control_label": "normal",
        "supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE77nnn/GSE77314/suppl/GSE77314_expression.xlsx",
        "sheet_path": "xl/worksheets/sheet5.xml",
    },
    "hcc_adult_extended_gse36376": {
        "source_type": "geo_microarray_series",
        "series_accession": "GSE36376",
        "platform_accession": "GPL10558",
        "platform_supplementary_url": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL10nnn/GPL10558/suppl/GPL10558_HumanHT-12_V4_0_R2_15002873_B.txt.gz",
        "design": "unpaired",
        "benchmark_id": "hcc_cdk20",
        "dataset_id": "GSE36376",
        "case_label": "liver tumor",
        "control_label": "adjacent non-tumor liver",
    },
}


@dataclass(frozen=True)
class GeoSample:
    """One GEO sample with phenotype metadata and optional supplement URLs."""

    geo_accession: str
    title: str
    phenotype: str
    supplementary_gene_url: str


XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def list_real_contrast_ids() -> list[str]:
    """List contrast ids that have accession-backed transcriptomics loaders."""
    return sorted(REAL_CONTRASTS)


def _geo_series_bucket(accession: str) -> str:
    prefix = accession[:-3]
    return f"{prefix}nnn"


def _series_matrix_url(series_accession: str) -> str:
    bucket = _geo_series_bucket(series_accession)
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{series_accession}/matrix/{series_accession}_series_matrix.txt.gz"


def _platform_quick_text_url(platform_accession: str) -> str:
    return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={platform_accession}&targ=self&form=text&view=quick"


def _platform_annotation_url(platform_accession: str) -> str:
    return f"https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/{platform_accession}/annot/{platform_accession}.annot.gz"


def _parse_tsv_row(line: str) -> list[str]:
    reader = csv.reader([line], delimiter="\t", quotechar='"')
    return next(reader)


def _empty_sample_columns(size: int) -> list[dict[str, str]]:
    return [{} for _ in range(size)]


def parse_geo_series_samples(series_matrix_text: str) -> list[GeoSample]:
    """Parse sample phenotype metadata and supplementary URLs from a GEO matrix."""
    row_map: dict[str, list[list[str]]] = {}
    for line in series_matrix_text.splitlines():
        if line.startswith("!series_matrix_table_begin"):
            break
        if not line.startswith("!Sample_"):
            continue
        cells = _parse_tsv_row(line)
        row_map.setdefault(cells[0], []).append(cells[1:])

    accessions = row_map["!Sample_geo_accession"][0]
    titles = row_map["!Sample_title"][0]
    supplementary = row_map.get("!Sample_supplementary_file_1", row_map.get("!Sample_supplementary_file"))
    supplementary_urls = supplementary[0] if supplementary else [""] * len(accessions)
    characteristics = _empty_sample_columns(len(accessions))

    for values in row_map.get("!Sample_characteristics_ch1", []):
        for index, raw_value in enumerate(values):
            if ": " not in raw_value:
                continue
            key, value = raw_value.split(": ", 1)
            characteristics[index][key.strip().lower()] = value.strip()

    samples: list[GeoSample] = []
    for index, accession in enumerate(accessions):
        phenotype = (
            characteristics[index].get("phenotype")
            or characteristics[index].get("disease")
            or characteristics[index].get("disease state")
            or characteristics[index].get("diagnosis")
            or characteristics[index].get("tissue type")
            or characteristics[index].get("tissue")
            or ""
        )
        samples.append(
            GeoSample(
                geo_accession=accession,
                title=titles[index],
                phenotype=phenotype,
                supplementary_gene_url=normalize_geo_url(supplementary_urls[index]),
            )
        )
    return samples


def parse_gene_count_text(gene_count_text: str) -> dict[str, int]:
    """Parse a per-sample GEO gene-count table keyed by Ensembl gene id."""
    counts: dict[str, int] = {}
    for line in gene_count_text.splitlines():
        if not line.strip():
            continue
        gene_id, raw_count = line.split("\t", 1)
        counts[gene_id] = int(raw_count)
    return counts


def parse_gene_count_matrix_text(
    gene_count_text: str,
    *,
    delimiter: str = "\t",
    has_gene_header: bool = False,
) -> tuple[list[str], dict[str, list[int]]]:
    """Parse a sample-by-gene count matrix keyed by gene label."""
    reader = csv.reader(
        [line for line in gene_count_text.splitlines() if line.strip()],
        delimiter=delimiter,
        quotechar='"',
    )
    rows = list(reader)
    if not rows:
        return [], {}

    header = rows[0]
    sample_titles = header[1:] if has_gene_header else header
    matrix: dict[str, list[int]] = {}
    for cells in rows[1:]:
        expected_length = len(sample_titles) + 1
        if len(cells) != expected_length:
            continue
        matrix[cells[0]] = [int(value) for value in cells[1:]]
    return sample_titles, matrix


def parse_geo_series_matrix_table(series_matrix_text: str) -> tuple[list[str], list[tuple[str, list[float]]]]:
    """Parse the expression table from a GEO series matrix."""
    lines = series_matrix_text.splitlines()
    in_table = False
    sample_ids: list[str] = []
    rows: list[tuple[str, list[float]]] = []

    for line in lines:
        if line.startswith("!series_matrix_table_begin"):
            in_table = True
            continue
        if line.startswith("!series_matrix_table_end"):
            break
        if not in_table:
            continue
        cells = _parse_tsv_row(line)
        if not sample_ids:
            sample_ids = cells[1:]
            continue
        try:
            values = [float(value) for value in cells[1:]]
        except ValueError:
            continue
        rows.append((cells[0], values))
    return sample_ids, rows


def parse_geo_platform_gene_symbols(platform_text: str) -> dict[str, str]:
    """Parse unambiguous probe-to-symbol mappings from a GEO platform text file."""
    lines = platform_text.splitlines()
    header: list[str] | None = None
    data_lines: list[str] = []
    probe_header: list[str] | None = None
    probe_rows: list[str] = []
    in_probe_table = False

    for line in lines:
        if line.startswith("#ID ="):
            header = ["ID"]
            continue
        if header is not None and line.startswith("#"):
            label = line[1:].split(" = ", 1)[0]
            header.append(label)
            continue
        if line.strip() == "[Probes]":
            in_probe_table = True
            probe_header = None
            continue
        if in_probe_table and probe_header is None:
            probe_header = line.split("\t")
            continue
        if in_probe_table:
            if line.strip():
                probe_rows.append(line)
            continue
        if line.startswith("^Annotation") or line.startswith("!"):
            continue
        if line.strip():
            data_lines.append(line)

    mapping: dict[str, str] = {}

    if header is not None:
        reader = csv.DictReader(data_lines, delimiter="\t", fieldnames=header)
        for row in reader:
            probe_id = (row.get("ID") or "").strip()
            gene_symbol = (row.get("Gene symbol") or "").strip()
            if not probe_id or not gene_symbol or gene_symbol == "---":
                continue
            if "///" in gene_symbol:
                continue
            mapping[probe_id] = gene_symbol

    if probe_header is None:
        return mapping

    reader = csv.DictReader(probe_rows, delimiter="\t", fieldnames=probe_header)
    for row in reader:
        probe_id = (row.get("Probe_Id") or "").strip()
        gene_symbol = (row.get("Symbol") or "").strip()
        if not probe_id or not gene_symbol or gene_symbol == "---":
            continue
        if "///" in gene_symbol or "," in gene_symbol or " " in gene_symbol:
            continue
        mapping[probe_id] = gene_symbol
    return mapping


def _select_samples(samples: list[GeoSample], label: str) -> list[GeoSample]:
    expected = label.lower()
    return [sample for sample in samples if expected in sample.phenotype.lower()]


def _library_sizes(sample_counts: dict[str, dict[str, int]]) -> dict[str, int]:
    return {
        accession: max(sum(counts.values()), 1)
        for accession, counts in sample_counts.items()
    }


def _log_cpm(count: int, library_size: int) -> float:
    return math.log2((count * 1_000_000.0 / library_size) + 1.0)


def _standardized_mean_difference(case_values: list[float], control_values: list[float]) -> float:
    case_sd = stdev(case_values) if len(case_values) > 1 else 0.0
    control_sd = stdev(control_values) if len(control_values) > 1 else 0.0
    pooled = math.sqrt(((case_sd ** 2) + (control_sd ** 2)) / 2.0)
    if pooled == 0.0:
        return 0.0
    return (fmean(case_values) - fmean(control_values)) / pooled


def _paired_standardized_effect(case_values: list[float], control_values: list[float]) -> float:
    differences = [case - control for case, control in zip(case_values, control_values)]
    if len(differences) < 2:
        return 0.0
    diff_sd = stdev(differences)
    if diff_sd == 0.0:
        return 0.0
    return fmean(differences) / diff_sd


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _betacf(a: float, b: float, x: float) -> float:
    max_iterations = 200
    epsilon = 3.0e-14
    tiny = 1.0e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - (qab * x / qap)
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    fraction = d

    for iteration in range(1, max_iterations + 1):
        even_index = 2 * iteration
        aa = iteration * (b - iteration) * x / ((qam + even_index) * (a + even_index))
        d = 1.0 + (aa * d)
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + (aa / c)
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        fraction *= d * c

        aa = -(a + iteration) * (qab + iteration) * x / ((a + even_index) * (qap + even_index))
        d = 1.0 + (aa * d)
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + (aa / c)
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        fraction *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return fraction


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp((a * math.log(x)) + (b * math.log1p(-x)) - _log_beta(a, b)) / a
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x)
    return 1.0 - (math.exp((b * math.log1p(-x)) + (a * math.log(x)) - _log_beta(b, a)) / b) * _betacf(b, a, 1.0 - x)


def _student_t_two_sided_p_value(statistic: float, degrees_of_freedom: float) -> float:
    if degrees_of_freedom <= 0.0:
        return 1.0
    x = degrees_of_freedom / (degrees_of_freedom + (statistic ** 2))
    return float(max(min(_regularized_incomplete_beta(degrees_of_freedom / 2.0, 0.5, x), 1.0), 0.0))


def _welch_satterthwaite_df(case_values: list[float], control_values: list[float]) -> float:
    case_var = stdev(case_values) ** 2
    control_var = stdev(control_values) ** 2
    case_term = case_var / len(case_values)
    control_term = control_var / len(control_values)
    numerator = (case_term + control_term) ** 2
    denominator = 0.0
    if len(case_values) > 1 and case_term > 0.0:
        denominator += (case_term ** 2) / (len(case_values) - 1)
    if len(control_values) > 1 and control_term > 0.0:
        denominator += (control_term ** 2) / (len(control_values) - 1)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _safe_ttest_ind(case_values: list[float], control_values: list[float]) -> tuple[float, float, float]:
    if len(case_values) < 2 or len(control_values) < 2:
        return 0.0, 1.0, 0.0
    case_mean = fmean(case_values)
    control_mean = fmean(control_values)
    case_var = stdev(case_values) ** 2
    control_var = stdev(control_values) ** 2
    denominator = math.sqrt((case_var / len(case_values)) + (control_var / len(control_values)))
    if denominator == 0.0:
        return 0.0, 1.0, 0.0
    statistic = (case_mean - control_mean) / denominator
    degrees_of_freedom = _welch_satterthwaite_df(case_values, control_values)
    p_value = _student_t_two_sided_p_value(statistic, degrees_of_freedom)
    return float(statistic), float(max(min(p_value, 1.0), 0.0)), float(degrees_of_freedom)


def _safe_ttest_rel(case_values: list[float], control_values: list[float]) -> tuple[float, float, float]:
    differences = [case - control for case, control in zip(case_values, control_values)]
    if len(differences) < 2:
        return 0.0, 1.0, 0.0
    diff_mean = fmean(differences)
    diff_sd = stdev(differences)
    if diff_sd == 0.0:
        return 0.0, 1.0, 0.0
    statistic = diff_mean / (diff_sd / math.sqrt(len(differences)))
    degrees_of_freedom = float(len(differences) - 1)
    p_value = _student_t_two_sided_p_value(statistic, degrees_of_freedom)
    return float(statistic), float(max(min(p_value, 1.0), 0.0)), degrees_of_freedom


def _bh_adjust(records: list[dict[str, Any]]) -> None:
    ranked = sorted(enumerate(records), key=lambda item: item[1]["statistics"]["p_value"])
    total = len(ranked)
    running_min = 1.0
    adjusted = [1.0] * total
    for reverse_rank, (index, record) in enumerate(reversed(ranked), start=1):
        rank = total - reverse_rank + 1
        p_value = float(record["statistics"]["p_value"])
        corrected = min(p_value * total / rank, 1.0)
        running_min = min(running_min, corrected)
        adjusted[index] = running_min
    for index, value in enumerate(adjusted):
        records[index]["statistics"]["adjusted_p_value"] = round(value, 12)


def build_real_gene_statistics(
    *,
    contrast_id: str,
    benchmark_id: str,
    dataset_id: str,
    case_samples: list[GeoSample],
    control_samples: list[GeoSample],
    sample_counts: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """Build inferential RNA-seq gene statistics from accession-level counts."""
    ordered_samples = case_samples + control_samples
    library_sizes = _library_sizes(sample_counts)
    all_genes = sorted({gene_id for counts in sample_counts.values() for gene_id in counts})
    records: list[dict[str, Any]] = []

    for gene_id in all_genes:
        case_values = [
            _log_cpm(sample_counts[sample.geo_accession].get(gene_id, 0), library_sizes[sample.geo_accession])
            for sample in case_samples
        ]
        control_values = [
            _log_cpm(sample_counts[sample.geo_accession].get(gene_id, 0), library_sizes[sample.geo_accession])
            for sample in control_samples
        ]
        mean_case = fmean(case_values)
        mean_control = fmean(control_values)
        raw_counts = [sample_counts[sample.geo_accession].get(gene_id, 0) for sample in ordered_samples]
        t_statistic, p_value, degrees_of_freedom = _safe_ttest_ind(case_values, control_values)
        records.append(
            {
                "schema_version": "0.1.0",
                "evidence_kind": "accession_backed_real",
                "contrast_id": contrast_id,
                "benchmark_id": benchmark_id,
                "dataset_id": dataset_id,
                "gene": {
                    "ensembl_gene_id": gene_id,
                    "symbol": None,
                },
                "statistics": {
                    "case_mean_log2_cpm": round(mean_case, 6),
                    "control_mean_log2_cpm": round(mean_control, 6),
                    "log2_fold_change": round(mean_case - mean_control, 6),
                    "t_statistic": round(t_statistic, 6),
                    "degrees_of_freedom": round(degrees_of_freedom, 6),
                    "p_value": round(p_value, 12),
                    "standardized_mean_difference": round(
                        _standardized_mean_difference(case_values, control_values),
                        6,
                    ),
                    "mean_raw_count": round(fmean(raw_counts), 6),
                },
                "sample_counts": {
                    "case": len(case_samples),
                    "control": len(control_samples),
                },
                "provenance": {
                    "source_kind": "geo_sample_supplement",
                    "series_accession": dataset_id,
                    "sample_geo_accessions": [sample.geo_accession for sample in ordered_samples],
                    "analysis_notes": "Computed from accession-level GEO gene count tables using log2(CPM+1) with Welch t-tests and BH FDR.",
                    "p_value_method": "Student t distribution with Welch-Satterthwaite degrees of freedom.",
                },
            }
        )
    _bh_adjust(records)
    return records


def _pair_id_from_title(title: str) -> str | None:
    workbook_match = re.search(r"S(\d+)[NT]$", title, re.IGNORECASE)
    if workbook_match:
        return workbook_match.group(1)
    hcc_match = re.search(r"HCC(\d+)", title, re.IGNORECASE)
    if hcc_match:
        return hcc_match.group(1)
    patient_match = re.search(r"Patient\s+(\d+)", title, re.IGNORECASE)
    if patient_match:
        return patient_match.group(1)
    return None


def _aggregate_probe_rows_by_gene(
    sample_ids: list[str],
    rows: list[tuple[str, list[float]]],
    probe_to_symbol: dict[str, str],
    symbol_to_gene: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for probe_id, values in rows:
        symbol = probe_to_symbol.get(probe_id)
        if symbol is None:
            continue
        gene = symbol_to_gene.get(symbol)
        if gene is None:
            continue
        bucket = grouped.setdefault(
            gene["ensembl_gene_id"],
            {
                "symbol": gene["symbol"],
                "hgnc_id": gene["hgnc_id"],
                "probes": [],
                "vectors": [],
                "source_symbols": set(),
            },
        )
        bucket["probes"].append(probe_id)
        bucket["vectors"].append(values)
        bucket["source_symbols"].add(symbol)

    aggregated: list[dict[str, Any]] = []
    for ensembl_gene_id, bucket in grouped.items():
        vectors = bucket["vectors"]
        averaged = [
            fmean(vector[column] for vector in vectors)
            for column in range(len(sample_ids))
        ]
        aggregated.append(
            {
                "ensembl_gene_id": ensembl_gene_id,
                "symbol": bucket["symbol"],
                "hgnc_id": bucket["hgnc_id"],
                "probe_ids": sorted(bucket["probes"]),
                "probe_count": len(bucket["probes"]),
                "source_symbols": sorted(bucket["source_symbols"]),
                "values": averaged,
            }
        )
    return aggregated


def build_microarray_gene_statistics(
    *,
    contrast_id: str,
    benchmark_id: str,
    dataset_id: str,
    case_label: str,
    control_label: str,
    samples: list[GeoSample],
    sample_ids: list[str],
    gene_rows: list[dict[str, Any]],
    paired_design: bool,
) -> list[dict[str, Any]]:
    """Build inferential microarray gene statistics from paired GEO matrix values."""
    sample_by_accession = {sample.geo_accession: sample for sample in samples}
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    selected_case_ids = {sample.geo_accession for sample in _select_samples(samples, case_label)}
    selected_control_ids = {sample.geo_accession for sample in _select_samples(samples, control_label)}
    case_ids = [sample_id for sample_id in sample_ids if sample_id in selected_case_ids]
    control_ids = [sample_id for sample_id in sample_ids if sample_id in selected_control_ids]
    if not case_ids or not control_ids:
        raise ValueError(f"Failed to recover case/control samples for {contrast_id}")
    records: list[dict[str, Any]] = []

    if paired_design:
        pairs: dict[str, dict[str, str]] = {}
        for sample_id in sample_ids:
            sample = sample_by_accession[sample_id]
            pair_id = _pair_id_from_title(sample.title)
            if pair_id is None:
                continue
            pair_bucket = pairs.setdefault(pair_id, {})
            if sample_id in selected_case_ids:
                pair_bucket["case"] = sample_id
            elif sample_id in selected_control_ids:
                pair_bucket["control"] = sample_id

        ordered_pairs = sorted(
            (pair_id, values["case"], values["control"])
            for pair_id, values in pairs.items()
            if "case" in values and "control" in values
        )
    else:
        ordered_pairs = []

    for gene_row in gene_rows:
        if paired_design:
            case_values = [gene_row["values"][sample_index[case_id]] for _, case_id, _ in ordered_pairs]
            control_values = [gene_row["values"][sample_index[control_id]] for _, _, control_id in ordered_pairs]
            t_statistic, p_value, degrees_of_freedom = _safe_ttest_rel(case_values, control_values)
            standardized_effect = _paired_standardized_effect(case_values, control_values)
            p_value_method = "Student t distribution with paired t degrees of freedom."
            analysis_notes = "Computed from GEO series-matrix log-intensity values using paired t-tests after averaging unambiguous platform probes per HGNC-mapped gene."
            paired_flag = True
        else:
            case_values = [gene_row["values"][sample_index[case_id]] for case_id in case_ids]
            control_values = [gene_row["values"][sample_index[control_id]] for control_id in control_ids]
            t_statistic, p_value, degrees_of_freedom = _safe_ttest_ind(case_values, control_values)
            standardized_effect = _standardized_mean_difference(case_values, control_values)
            p_value_method = "Student t distribution with Welch-Satterthwaite degrees of freedom."
            analysis_notes = "Computed from GEO series-matrix log-intensity values using Welch t-tests after averaging unambiguous platform probes per HGNC-mapped gene."
            paired_flag = False

        if not case_values or not control_values:
            continue
        mean_case = fmean(case_values)
        mean_control = fmean(control_values)
        records.append(
            {
                "schema_version": "0.1.0",
                "evidence_kind": "accession_backed_real",
                "contrast_id": contrast_id,
                "benchmark_id": benchmark_id,
                "dataset_id": dataset_id,
                "gene": {
                    "ensembl_gene_id": gene_row["ensembl_gene_id"],
                    "symbol": gene_row["symbol"],
                    "hgnc_id": gene_row["hgnc_id"],
                },
                "statistics": {
                    "case_mean_log2_intensity": round(mean_case, 6),
                    "control_mean_log2_intensity": round(mean_control, 6),
                    "log2_fold_change": round(mean_case - mean_control, 6),
                    "t_statistic": round(t_statistic, 6),
                    "degrees_of_freedom": round(degrees_of_freedom, 6),
                    "p_value": round(p_value, 12),
                    "standardized_mean_difference": round(standardized_effect, 6),
                    "mean_expression": round(fmean(case_values + control_values), 6),
                    "probe_count": gene_row["probe_count"],
                },
                "sample_counts": {
                    "case": len(case_values),
                    "control": len(control_values),
                },
                "provenance": {
                    "source_kind": "geo_series_matrix",
                    "series_accession": dataset_id,
                    "sample_geo_accessions": sample_ids,
                    "paired_design": paired_flag,
                    "source_probe_ids": gene_row["probe_ids"],
                    "source_gene_symbols": gene_row.get("source_symbols", [gene_row["symbol"]]),
                    "analysis_notes": analysis_notes,
                    "p_value_method": p_value_method,
                },
            }
        )
    _bh_adjust(records)
    return records


def build_expression_matrix_gene_statistics(
    *,
    contrast_id: str,
    benchmark_id: str,
    dataset_id: str,
    case_label: str,
    control_label: str,
    samples: list[GeoSample],
    sample_ids: list[str],
    gene_rows: list[dict[str, Any]],
    paired_design: bool,
    source_kind: str,
    analysis_notes: str,
) -> list[dict[str, Any]]:
    """Build inferential statistics from a sample-level expression matrix."""
    sample_by_accession = {sample.geo_accession: sample for sample in samples}
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    selected_case_ids = {sample.geo_accession for sample in _select_samples(samples, case_label)}
    selected_control_ids = {sample.geo_accession for sample in _select_samples(samples, control_label)}
    case_ids = [sample_id for sample_id in sample_ids if sample_id in selected_case_ids]
    control_ids = [sample_id for sample_id in sample_ids if sample_id in selected_control_ids]
    if not case_ids or not control_ids:
        raise ValueError(f"Failed to recover case/control samples for {contrast_id}")

    if paired_design:
        pairs: dict[str, dict[str, str]] = {}
        for sample_id in sample_ids:
            sample = sample_by_accession[sample_id]
            pair_id = _pair_id_from_title(sample.title)
            if pair_id is None:
                continue
            pair_bucket = pairs.setdefault(pair_id, {})
            if sample_id in selected_case_ids:
                pair_bucket["case"] = sample_id
            elif sample_id in selected_control_ids:
                pair_bucket["control"] = sample_id
        ordered_pairs = sorted(
            (pair_id, values["case"], values["control"])
            for pair_id, values in pairs.items()
            if "case" in values and "control" in values
        )
    else:
        ordered_pairs = []

    records: list[dict[str, Any]] = []
    for gene_row in gene_rows:
        if paired_design:
            case_values = [gene_row["values"][sample_index[case_id]] for _, case_id, _ in ordered_pairs]
            control_values = [gene_row["values"][sample_index[control_id]] for _, _, control_id in ordered_pairs]
            t_statistic, p_value, degrees_of_freedom = _safe_ttest_rel(case_values, control_values)
            standardized_effect = _paired_standardized_effect(case_values, control_values)
            p_value_method = "Student t distribution with paired t degrees of freedom."
        else:
            case_values = [gene_row["values"][sample_index[case_id]] for case_id in case_ids]
            control_values = [gene_row["values"][sample_index[control_id]] for control_id in control_ids]
            t_statistic, p_value, degrees_of_freedom = _safe_ttest_ind(case_values, control_values)
            standardized_effect = _standardized_mean_difference(case_values, control_values)
            p_value_method = "Student t distribution with Welch-Satterthwaite degrees of freedom."
        if not case_values or not control_values:
            continue

        mean_case = fmean(case_values)
        mean_control = fmean(control_values)
        records.append(
            {
                "schema_version": "0.1.0",
                "evidence_kind": "accession_backed_real",
                "contrast_id": contrast_id,
                "benchmark_id": benchmark_id,
                "dataset_id": dataset_id,
                "gene": {
                    "ensembl_gene_id": gene_row["ensembl_gene_id"],
                    "symbol": gene_row["symbol"],
                    "hgnc_id": gene_row["hgnc_id"],
                },
                "statistics": {
                    "case_mean_expression": round(mean_case, 6),
                    "control_mean_expression": round(mean_control, 6),
                    "log2_fold_change": round(mean_case - mean_control, 6),
                    "t_statistic": round(t_statistic, 6),
                    "degrees_of_freedom": round(degrees_of_freedom, 6),
                    "p_value": round(p_value, 12),
                    "standardized_mean_difference": round(standardized_effect, 6),
                    "mean_expression": round(fmean(case_values + control_values), 6),
                },
                "sample_counts": {
                    "case": len(case_values),
                    "control": len(control_values),
                },
                "provenance": {
                    "source_kind": source_kind,
                    "series_accession": dataset_id,
                    "sample_geo_accessions": sample_ids,
                    "paired_design": paired_design,
                    "source_gene_symbols": gene_row.get("source_symbols", [gene_row["symbol"]]),
                    "analysis_notes": analysis_notes,
                    "p_value_method": p_value_method,
                },
            }
        )
    _bh_adjust(records)
    return records


def _load_rnaseq_count_contrast(config: dict[str, str], contrast_id: str) -> list[dict[str, Any]]:
    series_text = load_text_with_cache(_series_matrix_url(config["series_accession"]), namespace="geo_cache")
    samples = parse_geo_series_samples(series_text)
    case_samples = _select_samples(samples, config["case_label"])
    control_samples = _select_samples(samples, config["control_label"])
    if not case_samples or not control_samples:
        raise ValueError(f"Failed to recover case/control samples for {contrast_id}")

    symbol_map = load_hgnc_symbol_map()
    sample_counts = {
        sample.geo_accession: parse_gene_count_text(
            load_text_with_cache(sample.supplementary_gene_url, namespace="geo_cache")
        )
        for sample in case_samples + control_samples
    }
    records = build_real_gene_statistics(
        contrast_id=contrast_id,
        benchmark_id=config["benchmark_id"],
        dataset_id=config["dataset_id"],
        case_samples=case_samples,
        control_samples=control_samples,
        sample_counts=sample_counts,
    )
    for record in records:
        mapping = symbol_map.get(record["gene"]["ensembl_gene_id"])
        if mapping is not None:
            record["gene"]["symbol"] = mapping["symbol"]
            record["gene"]["hgnc_id"] = mapping["hgnc_id"]
            record["provenance"]["identifier_mapping"] = {
                "source": "HGNC complete set",
                "hgnc_id": mapping["hgnc_id"],
            }
    return records


def _normalize_matrix_gene_symbol(raw_gene_label: str) -> str:
    base = raw_gene_label.rsplit(".chr", 1)[0]
    return base.split("|", 1)[0].strip()


def _load_xlsx_shared_strings(workbook_bytes: bytes) -> list[str]:
    with ZipFile(io.BytesIO(workbook_bytes)) as workbook:
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join((text_node.text or "") for text_node in item.iter(f"{XLSX_NS}t"))
        for item in root.findall(f"{XLSX_NS}si")
    ]


def _xlsx_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    raw_value = cell.find(f"{XLSX_NS}v")
    if raw_value is None:
        return ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(raw_value.text or "0")]
    return raw_value.text or ""


def parse_xlsx_expression_sheet(workbook_bytes: bytes, sheet_path: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Parse one xlsx worksheet into sample ids and gene-value rows."""
    shared_strings = _load_xlsx_shared_strings(workbook_bytes)
    with ZipFile(io.BytesIO(workbook_bytes)) as workbook:
        root = ET.fromstring(workbook.read(sheet_path))
    rows = root.find(f"{XLSX_NS}sheetData").findall(f"{XLSX_NS}row")
    header_cells = rows[0].findall(f"{XLSX_NS}c")
    sample_ids = [_xlsx_cell_value(cell, shared_strings) for cell in header_cells[1:]]
    gene_rows: list[dict[str, Any]] = []
    for row in rows[1:]:
        cells = row.findall(f"{XLSX_NS}c")
        if len(cells) < len(sample_ids) + 1:
            continue
        symbol = _xlsx_cell_value(cells[0], shared_strings)
        if not symbol:
            continue
        values = [float(_xlsx_cell_value(cell, shared_strings)) for cell in cells[1 : len(sample_ids) + 1]]
        gene_rows.append({"symbol": symbol, "values": values})
    return sample_ids, gene_rows


def _load_rnaseq_matrix_count_contrast(config: dict[str, str], contrast_id: str) -> list[dict[str, Any]]:
    series_text = load_text_with_cache(_series_matrix_url(config["series_accession"]), namespace="geo_cache")
    samples = parse_geo_series_samples(series_text)
    title_to_sample = {sample.title: sample for sample in samples}
    case_samples = _select_samples(samples, config["case_label"])
    control_samples = _select_samples(samples, config["control_label"])
    if not case_samples or not control_samples:
        raise ValueError(f"Failed to recover case/control samples for {contrast_id}")

    matrix_text = load_text_with_cache(config["supplementary_url"], namespace="geo_cache")
    sample_titles, matrix = parse_gene_count_matrix_text(
        matrix_text,
        delimiter=config.get("delimiter", "\t"),
        has_gene_header=config.get("has_gene_header") == True,
    )
    symbol_to_gene = load_hgnc_symbol_reverse_map()

    sample_counts = {sample.geo_accession: {} for sample in case_samples + control_samples}
    for raw_gene_label, values in matrix.items():
        symbol = _normalize_matrix_gene_symbol(raw_gene_label)
        gene = symbol_to_gene.get(symbol)
        if gene is None:
            continue
        for title, value in zip(sample_titles, values):
            sample = title_to_sample.get(title)
            if sample is None or sample.geo_accession not in sample_counts:
                continue
            sample_counts[sample.geo_accession][gene["ensembl_gene_id"]] = (
                sample_counts[sample.geo_accession].get(gene["ensembl_gene_id"], 0) + value
            )

    records = build_real_gene_statistics(
        contrast_id=contrast_id,
        benchmark_id=config["benchmark_id"],
        dataset_id=config["dataset_id"],
        case_samples=case_samples,
        control_samples=control_samples,
        sample_counts=sample_counts,
    )
    symbol_map = load_hgnc_symbol_map()
    for record in records:
        mapping = symbol_map.get(record["gene"]["ensembl_gene_id"])
        if mapping is None:
            continue
        record["gene"]["symbol"] = mapping["symbol"]
        record["gene"]["hgnc_id"] = mapping["hgnc_id"]
        record["provenance"]["identifier_mapping"] = {
            "source": "HGNC complete set",
            "hgnc_id": mapping["hgnc_id"],
        }
        record["provenance"]["source_kind"] = "geo_series_supplement_counts_matrix"
        record["provenance"]["supplementary_url"] = config["supplementary_url"]
        record["provenance"]["analysis_notes"] = (
            "Computed from GEO series-level gene count matrix values mapped from sample titles and HGNC-backed gene symbols using log2(CPM+1) with Welch t-tests and BH FDR."
        )
    return records


def _load_xlsx_expression_matrix_contrast(config: dict[str, str], contrast_id: str) -> list[dict[str, Any]]:
    workbook_bytes = load_bytes_with_cache(config["supplementary_url"], namespace="geo_cache")
    sample_ids, raw_gene_rows = parse_xlsx_expression_sheet(workbook_bytes, config["sheet_path"])
    samples = [
        GeoSample(
            geo_accession=sample_id,
            title=sample_id,
            phenotype="tumor" if sample_id.endswith("T") else "normal",
            supplementary_gene_url=config["supplementary_url"],
        )
        for sample_id in sample_ids
    ]
    symbol_to_gene = load_hgnc_symbol_reverse_map()
    gene_rows = []
    for row in raw_gene_rows:
        gene = symbol_to_gene.get(row["symbol"])
        if gene is None:
            continue
        gene_rows.append(
            {
                "ensembl_gene_id": gene["ensembl_gene_id"],
                "symbol": gene["symbol"],
                "hgnc_id": gene["hgnc_id"],
                "source_symbols": [row["symbol"]],
                "values": row["values"],
            }
        )
    return build_expression_matrix_gene_statistics(
        contrast_id=contrast_id,
        benchmark_id=config["benchmark_id"],
        dataset_id=config["dataset_id"],
        case_label=config["case_label"],
        control_label=config["control_label"],
        samples=samples,
        sample_ids=sample_ids,
        gene_rows=gene_rows,
        paired_design=True,
        source_kind="geo_expression_workbook",
        analysis_notes="Computed from the official GEO supplementary expression workbook using paired t-tests over the sample-level expression matrix on sheet5.",
    )


def _load_microarray_series_contrast(config: dict[str, str], contrast_id: str) -> list[dict[str, Any]]:
    series_text = load_text_with_cache(_series_matrix_url(config["series_accession"]), namespace="geo_cache")
    samples = parse_geo_series_samples(series_text)
    sample_ids, rows = parse_geo_series_matrix_table(series_text)
    platform_url = config.get("platform_supplementary_url") or _platform_annotation_url(config["platform_accession"])
    platform_text = load_text_with_cache(platform_url, namespace="geo_platform_cache")
    probe_to_symbol = parse_geo_platform_gene_symbols(platform_text)
    symbol_to_gene = load_hgnc_symbol_reverse_map()
    gene_rows = _aggregate_probe_rows_by_gene(sample_ids, rows, probe_to_symbol, symbol_to_gene)
    return build_microarray_gene_statistics(
        contrast_id=contrast_id,
        benchmark_id=config["benchmark_id"],
        dataset_id=config["dataset_id"],
        case_label=config["case_label"],
        control_label=config["control_label"],
        samples=samples,
        sample_ids=sample_ids,
        gene_rows=gene_rows,
        paired_design=config.get("design") == "paired",
    )


@functools.lru_cache(maxsize=16)
def load_real_geo_gene_statistics(contrast_id: str) -> list[dict[str, Any]]:
    """Load real accession-backed gene statistics for a supported contrast."""
    config = REAL_CONTRASTS.get(contrast_id)
    if config is None:
        return []

    source_type = config["source_type"]
    if source_type == "geo_rnaseq_counts":
        return _load_rnaseq_count_contrast(config, contrast_id)
    if source_type == "geo_rnaseq_matrix_counts":
        return _load_rnaseq_matrix_count_contrast(config, contrast_id)
    if source_type == "geo_xlsx_expression_matrix":
        return _load_xlsx_expression_matrix_contrast(config, contrast_id)
    if source_type == "geo_microarray_series":
        return _load_microarray_series_contrast(config, contrast_id)
    raise ValueError(f"Unsupported real contrast source type: {source_type}")
