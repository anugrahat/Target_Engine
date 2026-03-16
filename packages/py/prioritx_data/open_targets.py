"""Load source-backed Open Targets genetics associations for benchmark diseases."""

from __future__ import annotations

import functools
from typing import Any

from prioritx_data.remote_cache import load_json_post_with_cache

OPEN_TARGETS_API_URL = "https://api.platform.opentargets.org/api/v4/graphql"

OPEN_TARGETS_DISEASES: dict[str, dict[str, str]] = {
    "ipf_tnik": {
        "disease_id": "EFO_0000768",
        "disease_name": "idiopathic pulmonary fibrosis",
    },
    "hcc_cdk20": {
        "disease_id": "EFO_0000182",
        "disease_name": "hepatocellular carcinoma",
    },
    "als_pandaomics": {
        "disease_id": "MONDO_0004976",
        "disease_name": "amyotrophic lateral sclerosis",
    },
    "ad_phase_separation": {
        "disease_id": "MONDO_0004975",
        "disease_name": "Alzheimer disease",
    },
}

_ASSOCIATIONS_QUERY = """
query DiseaseAssociations($diseaseId: String!, $index: Int!, $size: Int!) {
  disease(efoId: $diseaseId) {
    id
    name
    associatedTargets(page: {index: $index, size: $size}) {
      count
      rows {
        score
        target {
          id
          approvedSymbol
          approvedName
        }
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""


def _tractability_query(ensembl_gene_ids: list[str]) -> str:
    body = []
    for index, gene_id in enumerate(ensembl_gene_ids):
        body.append(
            f"""
  t{index}: target(ensemblId: "{gene_id}") {{
    id
    approvedSymbol
    approvedName
    tractability {{
      label
      modality
      value
    }}
  }}"""
        )
    return "query TargetTractability {" + "".join(body) + "\n}"


def list_open_targets_benchmark_ids() -> list[str]:
    """List benchmarks that have a configured Open Targets disease identifier."""
    return sorted(OPEN_TARGETS_DISEASES)


def _datatype_score_map(datatype_scores: list[dict[str, Any]]) -> dict[str, float]:
    return {
        str(item["id"]): float(item["score"])
        for item in datatype_scores
        if item.get("id") is not None and item.get("score") is not None
    }


def _graphql_payload(disease_id: str, size: int) -> dict[str, object]:
    return {
        "query": _ASSOCIATIONS_QUERY,
        "variables": {"diseaseId": disease_id, "index": 0, "size": size},
    }


def _tractability_payload(ensembl_gene_ids: list[str]) -> dict[str, object]:
    return {"query": _tractability_query(ensembl_gene_ids)}


@functools.lru_cache(maxsize=16)
def load_open_targets_genetics(benchmark_id: str, *, size: int = 200) -> list[dict[str, Any]]:
    """Load Open Targets disease-target associations for one benchmark."""
    disease_config = OPEN_TARGETS_DISEASES.get(benchmark_id)
    if disease_config is None:
        return []

    page_size = 500
    requested_size = size if size > 0 else None
    page_index = 0
    items: list[dict[str, Any]] = []
    total_count = None
    while True:
        current_size = page_size
        if requested_size is not None:
            remaining = requested_size - len(items)
            if remaining <= 0:
                break
            current_size = min(page_size, remaining)

        payload = load_json_post_with_cache(
            OPEN_TARGETS_API_URL,
            namespace="open_targets_cache",
            payload={
                "query": _ASSOCIATIONS_QUERY,
                "variables": {
                    "diseaseId": disease_config["disease_id"],
                    "index": page_index,
                    "size": current_size,
                },
            },
        )
        disease = ((payload or {}).get("data") or {}).get("disease")
        if disease is None:
            break

        associated_targets = disease.get("associatedTargets") or {}
        rows = associated_targets.get("rows") or []
        total_count = int(associated_targets.get("count") or 0)
        if not rows:
            break

        for row_offset, row in enumerate(rows, start=1):
            datatype_scores = _datatype_score_map(row.get("datatypeScores") or [])
            target = row.get("target") or {}
            items.append(
                {
                    "schema_version": "0.1.0",
                    "evidence_kind": "open_targets_genetics",
                    "benchmark_id": benchmark_id,
                    "disease": {
                        "id": disease.get("id"),
                        "name": disease.get("name"),
                    },
                    "gene": {
                        "ensembl_gene_id": target.get("id"),
                        "symbol": target.get("approvedSymbol"),
                        "approved_name": target.get("approvedName"),
                    },
                    "statistics": {
                        "association_score": float(row.get("score") or 0.0),
                        "genetic_association_score": float(datatype_scores.get("genetic_association", 0.0)),
                        "genetic_literature_score": float(datatype_scores.get("genetic_literature", 0.0)),
                        "literature_score": float(datatype_scores.get("literature", 0.0)),
                    },
                    "provenance": {
                        "source_kind": "open_targets_graphql",
                        "api_url": OPEN_TARGETS_API_URL,
                        "disease_id": disease.get("id"),
                        "page_index": page_index,
                        "page_size": current_size,
                        "association_rank": page_index * page_size + row_offset,
                        "requested_size": size,
                        "query_name": "DiseaseAssociations",
                    },
                }
            )

        if requested_size is not None and len(items) >= requested_size:
            break
        if total_count is not None and len(items) >= total_count:
            break
        page_index += 1

    return items


def load_open_targets_tractability(ensembl_gene_ids: list[str], *, chunk_size: int = 50) -> list[dict[str, Any]]:
    """Load Open Targets tractability records for a set of Ensembl gene identifiers."""
    items: list[dict[str, Any]] = []
    unique_gene_ids = sorted({gene_id for gene_id in ensembl_gene_ids if gene_id})
    for start in range(0, len(unique_gene_ids), chunk_size):
        chunk = unique_gene_ids[start : start + chunk_size]
        payload = load_json_post_with_cache(
            OPEN_TARGETS_API_URL,
            namespace="open_targets_cache",
            payload=_tractability_payload(chunk),
        )
        data = (payload or {}).get("data") or {}
        for index, gene_id in enumerate(chunk):
            target = data.get(f"t{index}")
            if not target:
                continue
            items.append(
                {
                    "schema_version": "0.1.0",
                    "evidence_kind": "open_targets_tractability",
                    "gene": {
                        "ensembl_gene_id": target.get("id"),
                        "symbol": target.get("approvedSymbol"),
                        "approved_name": target.get("approvedName"),
                    },
                    "tractability": target.get("tractability") or [],
                    "provenance": {
                        "source_kind": "open_targets_graphql",
                        "api_url": OPEN_TARGETS_API_URL,
                        "query_name": "TargetTractability",
                        "requested_gene_ids": chunk,
                    },
                }
            )
    return items
