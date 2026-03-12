"""Load curated mechanistic edges with explicit leakage-risk filtering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.registry import repo_root

MECHANISTIC_EDGE_DIR = repo_root() / "data_contracts" / "curated" / "mechanistic_edges"
LEAKAGE_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _edge_path(benchmark_id: str) -> Path:
    return MECHANISTIC_EDGE_DIR / f"{benchmark_id}.json"


def _normalize_edge(edge: dict[str, Any], *, benchmark_id: str) -> dict[str, Any]:
    normalized = dict(edge)
    normalized.setdefault("benchmark_id", benchmark_id)
    normalized.setdefault("discovery_time_valid", True)
    normalized.setdefault("leakage_risk", "medium")
    normalized.setdefault("sources", [])
    return normalized


def load_mechanistic_edges(
    benchmark_id: str,
    *,
    max_leakage_risk: str = "medium",
) -> list[dict[str, Any]]:
    """Return curated mechanistic edges for one benchmark indication."""
    if max_leakage_risk not in LEAKAGE_RISK_ORDER:
        raise ValueError(f"Unknown leakage risk level: {max_leakage_risk}")
    path = _edge_path(benchmark_id)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    threshold = LEAKAGE_RISK_ORDER[max_leakage_risk]
    edges = []
    for edge in payload.get("edges") or []:
        normalized = _normalize_edge(edge, benchmark_id=benchmark_id)
        if LEAKAGE_RISK_ORDER.get(normalized["leakage_risk"], 99) > threshold:
            continue
        edges.append(normalized)
    return edges
