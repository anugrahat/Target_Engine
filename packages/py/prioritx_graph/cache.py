"""Local graph artifacts for fast provenance-first KG assembly."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.registry import repo_root


def graph_cache_dir() -> Path:
    path = repo_root() / "tmp" / "graph_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reactome_membership_cache_path() -> Path:
    return graph_cache_dir() / "reactome_gene_memberships.json"


def load_reactome_membership_cache() -> dict[str, list[dict[str, Any]]]:
    path = reactome_membership_cache_path()
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return {str(key): list(value) for key, value in payload.items()}


def save_reactome_membership_cache(payload: dict[str, list[dict[str, Any]]]) -> Path:
    path = reactome_membership_cache_path()
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
