"""CLI for metadata-derived baseline contrast readiness scoring."""

from __future__ import annotations

from prioritx_data.service import query_study_contrasts
from prioritx_features.transcriptomics import derive_contrast_quality_features
from prioritx_rank.baseline import score_contrast_readiness


def main() -> int:
    contrasts = query_study_contrasts()
    scored = [
        score_contrast_readiness(derive_contrast_quality_features(contrast))
        for contrast in contrasts
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)

    print("Contrast readiness scores:")
    for item in scored:
        print(f"- {item['contrast_id']}: {item['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
