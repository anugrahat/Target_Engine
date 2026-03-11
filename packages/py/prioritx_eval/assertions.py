"""Load source-backed benchmark target assertions."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from prioritx_data.registry import repo_root


def _assertions_dir() -> Path:
    return repo_root() / "data_contracts" / "assertions"


def list_benchmark_assertion_ids() -> list[str]:
    return sorted(path.stem for path in _assertions_dir().glob("*.json"))


@lru_cache(maxsize=None)
def load_benchmark_assertion(benchmark_id: str) -> dict[str, Any]:
    path = _assertions_dir() / f"{benchmark_id}.json"
    if not path.exists():
        raise ValueError(f"Unknown benchmark assertion: {benchmark_id}")
    return json.loads(path.read_text())
