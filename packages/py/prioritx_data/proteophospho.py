"""Load curated proteo-phospho programs and public HCC proteogenomic markers."""

from __future__ import annotations

import csv
import functools
import io
import json
import math
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import pstdev
from typing import Any, Callable

from prioritx_data.hgnc import load_hgnc_symbol_reverse_map
from prioritx_data.real_transcriptomics import _bh_adjust, _safe_ttest_ind
from prioritx_data.registry import repo_root
from prioritx_data.remote_cache import load_bytes_with_cache

PROTEOPHOSPHO_PROGRAM_DIR = repo_root() / "data_contracts" / "curated" / "proteophospho_programs"
HCC_ARCHIVE_URL = "https://zenodo.org/records/14553766/files/copheemap_hcc.tar.gz"
HCC_ARCHIVE_NAMESPACE = "proteophospho_cache"
HCC_PROTEIN_TUMOR = "copheemap_hcc/HCC_proteomics_gene_abundance_log2_reference_intensity_normalized_Tumor.txt"
HCC_PROTEIN_NORMAL = "copheemap_hcc/HCC_proteomics_gene_abundance_log2_reference_intensity_normalized_Normal.txt"
HCC_PHOSPHO_TUMOR = "copheemap_hcc/HCC_phospho_site_abundance_log2_reference_intensity_normalized_Tumor.txt"
HCC_PHOSPHO_NORMAL = "copheemap_hcc/HCC_phospho_site_abundance_log2_reference_intensity_normalized_Normal.txt"


def _program_path(benchmark_id: str) -> Path:
    return PROTEOPHOSPHO_PROGRAM_DIR / f"{benchmark_id}.json"


def load_proteophospho_programs(benchmark_id: str) -> list[dict[str, Any]]:
    """Return curated proteo-phospho programs for one benchmark indication."""
    path = _program_path(benchmark_id)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return list(payload.get("programs") or [])


def _extract_member_text(member_name: str) -> str:
    archive_bytes = load_bytes_with_cache(HCC_ARCHIVE_URL, namespace=HCC_ARCHIVE_NAMESPACE)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        member = archive.getmember(member_name)
        handle = archive.extractfile(member)
        if handle is None:
            raise FileNotFoundError(member_name)
        return handle.read().decode("utf-8", "replace")


def _parse_optional_float(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned or cleaned.upper() == "NA":
        return None
    return float(cleaned)


def _average_rows(rows: list[list[float | None]]) -> list[float]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    averaged: list[float] = []
    for index in range(width):
        values = [row[index] for row in rows if index < len(row) and row[index] is not None]
        if not values:
            continue
        averaged.append(sum(values) / len(values))
    return averaged


def _scan_selected_rows(
    text: str,
    *,
    selector: Callable[[str], object | None],
) -> dict[object, list[float]]:
    reader = csv.reader(io.StringIO(text), delimiter="\t")
    next(reader, None)
    grouped: dict[object, list[list[float | None]]] = defaultdict(list)
    for row in reader:
        if not row:
            continue
        selected_key = selector(row[0])
        if selected_key is None:
            continue
        grouped[selected_key].append([_parse_optional_float(value) for value in row[1:]])
    return {key: _average_rows(value_rows) for key, value_rows in grouped.items()}


def _protein_selector(targets: set[str]):
    def _selector(raw_id: str) -> str | None:
        ensembl_gene_id = raw_id.split(".", 1)[0]
        if ensembl_gene_id in targets:
            return ensembl_gene_id
        return None

    return _selector


def _phosphosite_selector(targets: set[tuple[str, str]]):
    def _selector(raw_id: str) -> tuple[str, str] | None:
        parts = raw_id.split("|")
        if len(parts) < 3:
            return None
        key = (parts[0].split(".", 1)[0], parts[2].strip().upper())
        if key in targets:
            return key
        return None

    return _selector


def _mean_difference(case_values: list[float], control_values: list[float]) -> float:
    if not case_values or not control_values:
        return 0.0
    return (sum(case_values) / len(case_values)) - (sum(control_values) / len(control_values))


def _outlier_metrics(case_values: list[float], control_values: list[float], *, expected_direction: str) -> tuple[float, float]:
    if not case_values or not control_values:
        return 0.0, 0.0
    control_mean = sum(control_values) / len(control_values)
    control_sd = pstdev(control_values) if len(control_values) > 1 else 0.0
    if expected_direction == "up":
        threshold = control_mean + (2.0 * control_sd)
        outlier_fraction = sum(value > threshold for value in case_values) / len(case_values)
        sorted_case = sorted(case_values)
        q90_index = max(0, math.ceil(0.9 * len(sorted_case)) - 1)
        q90_shift = sorted_case[q90_index] - control_mean
    else:
        threshold = control_mean - (2.0 * control_sd)
        outlier_fraction = sum(value < threshold for value in case_values) / len(case_values)
        sorted_case = sorted(case_values)
        q10_index = max(0, math.floor(0.1 * len(sorted_case)))
        q90_shift = control_mean - sorted_case[q10_index]
    return round(outlier_fraction, 6), round(q90_shift, 6)


def _marker_score(mean_difference: float, adjusted_p_value: float, *, expected_direction: str) -> tuple[float, bool]:
    expected_sign = 1.0 if expected_direction == "up" else -1.0
    directional_effect = expected_sign * mean_difference
    if directional_effect <= 0.0:
        return 0.0, False
    effect_strength = min(abs(directional_effect) / 1.0, 1.0)
    significance_strength = min(-math.log10(max(adjusted_p_value, 1e-300)) / 10.0, 1.0)
    return round(0.55 * effect_strength + 0.45 * significance_strength, 6), True


@functools.lru_cache(maxsize=8)
def load_benchmark_proteophospho_statistics(benchmark_id: str) -> dict[str, Any]:
    """Load selected protein and phosphosite statistics for one benchmark."""
    programs = load_proteophospho_programs(benchmark_id)
    if benchmark_id != "hcc_cdk20" or not programs:
        return {
            "benchmark_id": benchmark_id,
            "protein_markers": {},
            "phosphosite_markers": {},
            "provenance": {},
        }

    reverse_map = load_hgnc_symbol_reverse_map()
    protein_marker_specs: dict[str, dict[str, Any]] = {}
    phosphosite_marker_specs: dict[tuple[str, str], dict[str, Any]] = {}
    for program in programs:
        for marker in program.get("protein_markers") or []:
            gene = reverse_map.get(marker["gene_symbol"])
            if gene is None:
                continue
            protein_marker_specs[gene["ensembl_gene_id"]] = {
                "gene_symbol": gene["symbol"],
                "ensembl_gene_id": gene["ensembl_gene_id"],
                "expected_direction": marker.get("expected_direction", "up"),
            }
        for marker in program.get("phosphosite_markers") or []:
            gene = reverse_map.get(marker["gene_symbol"])
            if gene is None:
                continue
            phosphosite_marker_specs[(gene["ensembl_gene_id"], marker["site"].upper())] = {
                "gene_symbol": gene["symbol"],
                "ensembl_gene_id": gene["ensembl_gene_id"],
                "site": marker["site"].upper(),
                "expected_direction": marker.get("expected_direction", "up"),
            }

    protein_tumor = _scan_selected_rows(
        _extract_member_text(HCC_PROTEIN_TUMOR),
        selector=_protein_selector(set(protein_marker_specs)),
    )
    protein_normal = _scan_selected_rows(
        _extract_member_text(HCC_PROTEIN_NORMAL),
        selector=_protein_selector(set(protein_marker_specs)),
    )
    phospho_tumor = _scan_selected_rows(
        _extract_member_text(HCC_PHOSPHO_TUMOR),
        selector=_phosphosite_selector(set(phosphosite_marker_specs)),
    )
    phospho_normal = _scan_selected_rows(
        _extract_member_text(HCC_PHOSPHO_NORMAL),
        selector=_phosphosite_selector(set(phosphosite_marker_specs)),
    )

    records: list[dict[str, Any]] = []
    for ensembl_gene_id, marker in protein_marker_specs.items():
        tumor_values = protein_tumor.get(ensembl_gene_id, [])
        normal_values = protein_normal.get(ensembl_gene_id, [])
        if len(tumor_values) < 3 or len(normal_values) < 3:
            continue
        statistic, p_value, degrees_of_freedom = _safe_ttest_ind(tumor_values, normal_values)
        outlier_fraction, outlier_shift = _outlier_metrics(
            tumor_values,
            normal_values,
            expected_direction=marker["expected_direction"],
        )
        records.append(
            {
                "marker_kind": "protein",
                "marker_ref": marker["gene_symbol"],
                "gene_symbol": marker["gene_symbol"],
                "ensembl_gene_id": ensembl_gene_id,
                "expected_direction": marker["expected_direction"],
                "statistics": {
                    "t_statistic": round(statistic, 6),
                    "degrees_of_freedom": round(degrees_of_freedom, 6),
                    "p_value": round(p_value, 12),
                },
                "mean_difference": round(_mean_difference(tumor_values, normal_values), 6),
                "outlier_fraction": outlier_fraction,
                "outlier_shift": outlier_shift,
                "tumor_sample_count": len(tumor_values),
                "normal_sample_count": len(normal_values),
            }
        )

    for (ensembl_gene_id, site), marker in phosphosite_marker_specs.items():
        tumor_values = phospho_tumor.get((ensembl_gene_id, site), [])
        normal_values = phospho_normal.get((ensembl_gene_id, site), [])
        if len(tumor_values) < 3 or len(normal_values) < 3:
            continue
        statistic, p_value, degrees_of_freedom = _safe_ttest_ind(tumor_values, normal_values)
        outlier_fraction, outlier_shift = _outlier_metrics(
            tumor_values,
            normal_values,
            expected_direction=marker["expected_direction"],
        )
        records.append(
            {
                "marker_kind": "phosphosite",
                "marker_ref": f"{marker['gene_symbol']}:{site}",
                "gene_symbol": marker["gene_symbol"],
                "ensembl_gene_id": ensembl_gene_id,
                "site": site,
                "expected_direction": marker["expected_direction"],
                "statistics": {
                    "t_statistic": round(statistic, 6),
                    "degrees_of_freedom": round(degrees_of_freedom, 6),
                    "p_value": round(p_value, 12),
                },
                "mean_difference": round(_mean_difference(tumor_values, normal_values), 6),
                "outlier_fraction": outlier_fraction,
                "outlier_shift": outlier_shift,
                "tumor_sample_count": len(tumor_values),
                "normal_sample_count": len(normal_values),
            }
        )

    _bh_adjust(records)

    protein_markers: dict[str, dict[str, Any]] = {}
    phosphosite_markers: dict[str, dict[str, Any]] = {}
    for record in records:
        score, directionally_supported = _marker_score(
            float(record["mean_difference"]),
            float(record["statistics"]["adjusted_p_value"]),
            expected_direction=str(record["expected_direction"]),
        )
        enriched_record = {
            **record,
            "score": score,
            "directionally_supported": directionally_supported,
            "analysis_notes": (
                "Computed from public HCC proteogenomic tumor-vs-normal log2 abundance matrices "
                "using Welch t-tests and BH FDR over the curated marker panel."
            ),
            "source_url": HCC_ARCHIVE_URL,
        }
        if record["marker_kind"] == "protein":
            protein_markers[str(record["marker_ref"])] = enriched_record
        else:
            phosphosite_markers[str(record["marker_ref"])] = enriched_record

    return {
        "benchmark_id": benchmark_id,
        "protein_markers": protein_markers,
        "phosphosite_markers": phosphosite_markers,
        "provenance": {
            "source_kind": "public_proteogenomic_archive",
            "source_url": HCC_ARCHIVE_URL,
            "protein_matrix_member": HCC_PROTEIN_TUMOR,
            "phosphosite_matrix_member": HCC_PHOSPHO_TUMOR,
            "analysis_scope": "curated_marker_panel_only",
        },
    }
