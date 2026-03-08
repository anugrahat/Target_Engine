"""Load generated first-wave registry artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    """Return the repository root based on this module location."""
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class RegistryArtifact:
    """Metadata plus parsed JSON for one registry artifact."""

    artifact_type: str
    path: Path
    payload: dict[str, Any]

    @property
    def benchmark_id(self) -> str:
        return str(self.payload["benchmark_id"])


def _registry_dir(artifact_type: str) -> Path:
    mapping = {
        "dataset_manifest": repo_root() / "data_contracts" / "registries" / "dataset_manifests",
        "study_contrast": repo_root() / "data_contracts" / "registries" / "study_contrasts",
    }
    try:
        return mapping[artifact_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported artifact type: {artifact_type}") from exc


def _load_artifact(path: Path, artifact_type: str) -> RegistryArtifact:
    payload = json.loads(path.read_text())
    return RegistryArtifact(artifact_type=artifact_type, path=path, payload=payload)


def list_registry_artifacts(artifact_type: str) -> list[RegistryArtifact]:
    """Load all generated artifacts of a given type."""
    directory = _registry_dir(artifact_type)
    paths = sorted(directory.glob("*.json"))
    return [_load_artifact(path, artifact_type) for path in paths]


def list_dataset_manifests() -> list[RegistryArtifact]:
    """Load all generated dataset manifest fixtures."""
    return list_registry_artifacts("dataset_manifest")


def list_study_contrasts() -> list[RegistryArtifact]:
    """Load all generated study contrast fixtures."""
    return list_registry_artifacts("study_contrast")


def group_by_benchmark(artifacts: list[RegistryArtifact]) -> dict[str, list[RegistryArtifact]]:
    """Group registry artifacts by benchmark id."""
    grouped: dict[str, list[RegistryArtifact]] = {}
    for artifact in artifacts:
        grouped.setdefault(artifact.benchmark_id, []).append(artifact)
    return grouped
