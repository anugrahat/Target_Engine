"""Access official GEO transcriptomics inputs for curated PrioriTx contrasts."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from statistics import fmean, stdev
from typing import Any

from prioritx_data.hgnc import load_hgnc_symbol_map
from prioritx_data.remote_cache import load_text_with_cache, normalize_geo_url

REAL_COUNT_CONTRASTS: dict[str, dict[str, str]] = {
    "ipf_lung_core_gse52463": {
        "series_accession": "GSE52463",
        "benchmark_id": "ipf_tnik",
        "dataset_id": "GSE52463",
        "case_label": "idiopathic pulmonary fibrosis",
        "control_label": "normal",
    }
}


@dataclass(frozen=True)
class GeoCountSample:
    """One GEO sample with phenotype metadata and a count-table URL."""

    geo_accession: str
    title: str
    phenotype: str
    supplementary_gene_url: str


def list_real_contrast_ids() -> list[str]:
    """List contrast ids that have accession-backed transcriptomics loaders."""
    return sorted(REAL_COUNT_CONTRASTS)


def _geo_series_bucket(accession: str) -> str:
    prefix = accession[:-3]
    return f"{prefix}nnn"


def _series_matrix_url(series_accession: str) -> str:
    bucket = _geo_series_bucket(series_accession)
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{series_accession}/matrix/{series_accession}_series_matrix.txt.gz"


def _parse_tsv_row(line: str) -> list[str]:
    reader = csv.reader([line], delimiter="\t", quotechar='"')
    return next(reader)


def _empty_sample_columns(size: int) -> list[dict[str, str]]:
    return [{} for _ in range(size)]


def parse_geo_series_samples(series_matrix_text: str) -> list[GeoCountSample]:
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

    samples: list[GeoCountSample] = []
    for index, accession in enumerate(accessions):
        phenotype = characteristics[index].get("phenotype", characteristics[index].get("disease", ""))
        samples.append(
            GeoCountSample(
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


def _select_samples(samples: list[GeoCountSample], label: str) -> list[GeoCountSample]:
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


def build_real_gene_statistics(
    *,
    contrast_id: str,
    benchmark_id: str,
    dataset_id: str,
    case_samples: list[GeoCountSample],
    control_samples: list[GeoCountSample],
    sample_counts: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """Build real gene-level transcriptomics statistics from accession-level counts."""
    ordered_samples = case_samples + control_samples
    library_sizes = _library_sizes(sample_counts)
    all_genes = sorted({gene_id for counts in sample_counts.values() for gene_id in counts})
    stats: list[dict[str, Any]] = []

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
        stats.append(
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
                    "analysis_notes": "Computed from accession-level GEO gene count tables using log2(CPM+1) group means.",
                },
            }
        )
    return stats


def load_real_geo_gene_statistics(contrast_id: str) -> list[dict[str, Any]]:
    """Load real accession-backed gene statistics for a supported contrast."""
    config = REAL_COUNT_CONTRASTS.get(contrast_id)
    if config is None:
        return []

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
