"""Load curated single-cell-derived cell-state programs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.registry import repo_root

CELL_STATE_PROGRAM_DIR = repo_root() / "data_contracts" / "curated" / "cell_state_programs"


def _program_path(benchmark_id: str) -> Path:
    return CELL_STATE_PROGRAM_DIR / f"{benchmark_id}.json"


def load_cell_state_programs(benchmark_id: str) -> list[dict[str, Any]]:
    """Return curated cell-state programs for one benchmark indication."""
    path = _program_path(benchmark_id)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return list(payload.get("programs") or [])
