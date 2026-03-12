"""Load source-backed Reactome pathway enrichment and gene membership evidence."""

from __future__ import annotations

import functools
from typing import Any
from urllib.error import HTTPError, URLError

from prioritx_data.remote_cache import load_json_text_post_with_cache

REACTOME_ANALYSIS_URL = "https://reactome.org/AnalysisService/identifiers/projection"


def _analysis_url(*, page_size: int = 1000, page: int = 1) -> str:
    return f"{REACTOME_ANALYSIS_URL}?pageSize={page_size}&page={page}"


def _identifier_payload(identifiers: tuple[str, ...]) -> str:
    lines = ["#Identifiers", *identifiers]
    return "\n".join(lines) + "\n"


def _pathway_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list((payload or {}).get("pathways") or [])


def _normalize_pathway_record(
    row: dict[str, Any],
    *,
    source_kind: str,
    query_identifiers: tuple[str, ...],
) -> dict[str, Any]:
    entities = row.get("entities") or {}
    species = row.get("species") or {}
    return {
        "schema_version": "0.1.0",
        "evidence_kind": source_kind,
        "pathway": {
            "st_id": row.get("stId"),
            "db_id": row.get("dbId"),
            "name": row.get("name"),
            "species_name": species.get("name"),
            "species_tax_id": species.get("taxId"),
        },
        "statistics": {
            "found_entities": int(entities.get("found") or 0),
            "total_entities": int(entities.get("total") or 0),
            "entity_ratio": float(entities.get("ratio") or 0.0),
            "p_value": float(entities.get("pValue") or 1.0),
            "fdr": float(entities.get("fdr") or 1.0),
        },
        "provenance": {
            "source_kind": "reactome_analysis_service",
            "api_url": REACTOME_ANALYSIS_URL,
            "query_identifiers": list(query_identifiers),
        },
    }


@functools.lru_cache(maxsize=32)
def load_reactome_pathway_enrichment(identifiers: tuple[str, ...]) -> list[dict[str, Any]]:
    """Load Reactome pathway enrichment for a disease-support identifier set."""
    filtered = tuple(sorted({item for item in identifiers if item}))
    if not filtered:
        return []
    payload = load_json_text_post_with_cache(
        _analysis_url(),
        namespace="reactome_cache",
        payload=_identifier_payload(filtered),
    )
    return [
        _normalize_pathway_record(
            row,
            source_kind="reactome_pathway_enrichment",
            query_identifiers=filtered,
        )
        for row in _pathway_rows(payload)
    ]


@functools.lru_cache(maxsize=512)
def load_reactome_gene_pathways(identifier: str) -> list[dict[str, Any]]:
    """Load the Reactome pathways returned for one gene identifier."""
    normalized = identifier.strip()
    if not normalized:
        return []
    try:
        payload = load_json_text_post_with_cache(
            _analysis_url(),
            namespace="reactome_cache",
            payload=_identifier_payload((normalized,)),
        )
    except (HTTPError, URLError, TimeoutError):
        return []
    return [
        _normalize_pathway_record(
            row,
            source_kind="reactome_gene_membership",
            query_identifiers=(normalized,),
        )
        for row in _pathway_rows(payload)
    ]
