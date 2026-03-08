"""Load local transcriptomics fixture records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.registry import repo_root


def _fixture_dir() -> Path:
    return repo_root() / "data_contracts" / "fixtures" / "transcriptomics"


def list_fixture_contrast_ids() -> list[str]:
    """List contrast ids for available transcriptomics fixture files."""
    return sorted(path.stem for path in _fixture_dir().glob("*.jsonl"))


def load_transcriptomics_fixture(contrast_id: str) -> list[dict[str, Any]]:
    """Load one transcriptomics fixture file by contrast id."""
    path = _fixture_dir() / f"{contrast_id}.jsonl"
    records = []
    for line in path.read_text().splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records
