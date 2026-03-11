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
    "als": {
        "disease_id": "MONDO_0004976",
        "disease_name": "amyotrophic lateral sclerosis",
    },
    "ad_phase_separation": {
        "disease_id": "MONDO_0004975",
        "disease_name": "Alzheimer disease",
    },
}

_ASSOCIATIONS_QUERY = """
query DiseaseAssociations($diseaseId: String!, $size: Int!) {
  disease(efoId: $diseaseId) {
    id
    name
    associatedTargets(page: {index: 0, size: $size}) {
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
        "variables": {"diseaseId": disease_id, "size": size},
    }


@functools.lru_cache(maxsize=16)
def load_open_targets_genetics(benchmark_id: str, *, size: int = 200) -> list[dict[str, Any]]:
    """Load Open Targets disease-target associations for one benchmark."""
    disease_config = OPEN_TARGETS_DISEASES.get(benchmark_id)
    if disease_config is None:
        return []

    payload = load_json_post_with_cache(
        OPEN_TARGETS_API_URL,
        namespace="open_targets_cache",
        payload=_graphql_payload(disease_config["disease_id"], size),
    )
    disease = ((payload or {}).get("data") or {}).get("disease")
    if disease is None:
        return []

    rows = (((disease.get("associatedTargets") or {}).get("rows")) or [])
    items: list[dict[str, Any]] = []
    for row in rows:
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
                    "requested_page_size": size,
                    "query_name": "DiseaseAssociations",
                },
            }
        )
    return items
