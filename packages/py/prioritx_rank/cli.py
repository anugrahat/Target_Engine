"""CLI for metadata-derived baseline contrast readiness scoring."""

from __future__ import annotations

from prioritx_data.real_transcriptomics import list_real_contrast_ids
from prioritx_data.transcriptomics import list_fixture_contrast_ids, load_transcriptomics_fixture
from prioritx_data.service import (
    fused_target_evidence,
    open_targets_genetics_scores,
    query_study_contrasts,
    transcriptomics_indication_evidence,
    transcriptomics_real_scores,
)
from prioritx_features.transcriptomics import derive_contrast_quality_features, derive_gene_transcriptomics_features
from prioritx_rank.baseline import score_contrast_readiness, score_gene_transcriptomics
from prioritx_eval.service import evaluate_fused_benchmark


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

    fixture_ids = list_fixture_contrast_ids()
    if fixture_ids:
        print("Transcriptomics fixture gene scores:")
        for contrast_id in fixture_ids:
            records = load_transcriptomics_fixture(contrast_id)
            gene_scores = [
                score_gene_transcriptomics(derive_gene_transcriptomics_features(record))
                for record in records
            ]
            gene_scores.sort(key=lambda item: item["score"], reverse=True)
            top = gene_scores[0]
            print(f"- {contrast_id}: top {top['gene_symbol']} ({top['score']})")

    real_ids = list_real_contrast_ids()
    if real_ids:
        print("Real transcriptomics gene scores:")
        for contrast_id in real_ids:
            gene_scores = transcriptomics_real_scores(contrast_id)
            if not gene_scores:
                continue
            top = gene_scores[0]
            print(f"- {contrast_id}: top {top['ensembl_gene_id']} ({top['score']})")

    print("Cross-contrast transcriptomics evidence:")
    for subset_id in ("ipf_lung_core", "hcc_adult_core"):
        items = transcriptomics_indication_evidence(subset_id=subset_id)
        if not items:
            continue
        top = items[0]
        label = top["gene_symbol"] or top["ensembl_gene_id"]
        print(f"- {subset_id}: top {label} ({top['score']}) across {top['supporting_contrast_count']} supporting contrasts")

    print("Open Targets genetics evidence:")
    for benchmark_id in ("ipf_tnik", "hcc_cdk20"):
        items = open_targets_genetics_scores(benchmark_id, size=50)
        if not items:
            continue
        top = items[0]
        label = top["gene_symbol"] or top["ensembl_gene_id"]
        print(f"- {benchmark_id}: top {label} ({top['score']})")

    print("Fused target evidence:")
    for benchmark_id, subset_id in (("ipf_tnik", "ipf_lung_core"), ("hcc_cdk20", "hcc_adult_core")):
        items = fused_target_evidence(benchmark_id=benchmark_id, subset_id=subset_id, genetics_size=50)
        if not items:
            continue
        top = items[0]
        label = top["gene_symbol"] or top["ensembl_gene_id"]
        print(f"- {benchmark_id}: top {label} ({top['score']})")

    print("Benchmark target evaluation:")
    for benchmark_id in ("ipf_tnik", "hcc_cdk20"):
        result = evaluate_fused_benchmark(benchmark_id)
        print(
            f"- {benchmark_id}: found {result['positive_targets_found']}/{result['positive_target_count']} "
            f"positives, best_rank={result['metrics']['best_rank']}, hit@10={result['metrics']['hit_at_10']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
