"""Shared identifier helpers for PrioriTx."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkId:
    """Stable identifier wrapper for a benchmark case."""

    value: str


@dataclass(frozen=True)
class DatasetId:
    """Stable identifier wrapper for a dataset accession or registry record."""

    value: str
