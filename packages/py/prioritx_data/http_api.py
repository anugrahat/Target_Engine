"""Dependency-free read-only HTTP surface for registry fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prioritx_data.service import (
    benchmark_index,
    contrast_readiness_scores,
    get_subset,
    list_benchmark_subsets,
    fused_target_evidence,
    query_dataset_manifests,
    query_study_contrasts,
    open_targets_genetics_scores,
    pubmed_literature_scores,
    reactome_pathway_scores,
    open_targets_tractability_scores,
    transcriptomics_indication_evidence,
    transcriptomics_fixture_scores,
    transcriptomics_real_scores,
)
from prioritx_eval.policy import BENCHMARK_MODES, benchmark_integrity_review
from prioritx_eval.service import (
    audit_target_evidence,
    compare_benchmark_modes,
    evaluate_fused_benchmark,
    export_benchmark_health_rows,
    explain_target_evidence,
    explain_target_shortlist,
    summarize_benchmark_health,
    summarize_benchmark_dashboard,
    target_evidence_graph,
)
from prioritx_rl.service import evaluate_bandit_agents

ROOT = Path(__file__).resolve().parents[3]
MATERIALIZED_EXPORTS_DIR = ROOT / "tmp" / "benchmark_exports" / "latest"


def _single(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def _mode(query: dict[str, list[str]]) -> str | None:
    mode = _single(query, "mode")
    if mode is None:
        return None
    if mode not in BENCHMARK_MODES:
        return "__invalid__"
    return mode


def _materialized_payload(filename: str) -> dict[str, Any] | None:
    path = MATERIALIZED_EXPORTS_DIR / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _materialized_benchmark_payload(folder: str, benchmark_id: str, mode: str | None = None) -> dict[str, Any] | None:
    filename = f"{benchmark_id}.{mode}.json" if mode else f"{benchmark_id}.json"
    path = MATERIALIZED_EXPORTS_DIR / folder / filename
    if not path.exists():
        return None
    return json.loads(path.read_text())


def handle_get(path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, Any]]:
    """Return status code plus JSON payload for a read-only GET route."""
    if path == "/":
        return 200, {
            "service": "prioritx-registry-api",
            "routes": [
                "/health",
                "/benchmarks",
                "/materialized/benchmark-dashboard-summary",
                "/materialized/benchmark-health-summary",
                "/materialized/benchmark-health-export",
                "/materialized/benchmark-mode-comparison",
                "/materialized/target-shortlist-explanations",
                "/benchmark-dashboard-summary",
                "/benchmark-health-summary",
                "/benchmark-health-export",
                "/subsets",
                "/subsets/{subset_id}",
                "/dataset-manifests",
                "/study-contrasts",
                "/contrast-readiness",
                "/open-targets-genetics",
                "/open-targets-tractability",
                "/pubmed-literature-support",
                "/reactome-pathway-support",
                "/fused-target-evidence",
                "/benchmark-evaluation",
                "/benchmark-integrity",
                "/benchmark-mode-comparison",
                "/target-explanation",
                "/target-shortlist-explanations",
                "/target-evidence-graph",
                "/target-audit",
                "/rl-benchmark-evaluation",
                "/transcriptomics-evidence",
                "/transcriptomics-real-scores",
                "/transcriptomics-fixture-scores",
            ],
        }

    if path == "/health":
        return 200, {"status": "ok"}

    if path == "/benchmarks":
        return 200, {"items": benchmark_index()}

    if path == "/materialized/benchmark-dashboard-summary":
        payload = _materialized_payload("benchmark_dashboard.json")
        if payload is None:
            return 404, {"error": "No materialized benchmark dashboard snapshot available"}
        return 200, payload

    if path == "/materialized/benchmark-health-summary":
        payload = _materialized_payload("benchmark_health.json")
        if payload is None:
            return 404, {"error": "No materialized benchmark health snapshot available"}
        return 200, payload

    if path == "/materialized/benchmark-health-export":
        payload = _materialized_payload("benchmark_health_rows.json")
        if payload is None:
            return 404, {"error": "No materialized benchmark health export available"}
        return 200, payload

    if path == "/materialized/benchmark-mode-comparison":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        payload = _materialized_benchmark_payload("benchmark_mode_comparisons", benchmark_id)
        if payload is None:
            return 404, {"error": f"No materialized benchmark mode comparison available for {benchmark_id}"}
        return 200, payload

    if path == "/materialized/target-shortlist-explanations":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}
        payload = _materialized_benchmark_payload("target_shortlists", benchmark_id, mode or "strict")
        if payload is None:
            return 404, {"error": f"No materialized target shortlist available for {benchmark_id} ({mode or 'strict'})"}
        return 200, payload

    if path == "/benchmark-dashboard-summary":
        top_n_raw = _single(query, "top_n")
        try:
            top_n = int(top_n_raw) if top_n_raw else 5
        except ValueError:
            return 400, {"error": "top_n must be an integer"}
        return 200, summarize_benchmark_dashboard(top_n=top_n)

    if path == "/benchmark-health-summary":
        top_n_raw = _single(query, "top_n")
        try:
            top_n = int(top_n_raw) if top_n_raw else 10
        except ValueError:
            return 400, {"error": "top_n must be an integer"}
        return 200, summarize_benchmark_health(top_n=top_n)

    if path == "/benchmark-health-export":
        top_n_raw = _single(query, "top_n")
        try:
            top_n = int(top_n_raw) if top_n_raw else 10
        except ValueError:
            return 400, {"error": "top_n must be an integer"}
        return 200, export_benchmark_health_rows(top_n=top_n)

    if path == "/subsets":
        benchmark_id = _single(query, "benchmark_id")
        subsets = list_benchmark_subsets()
        if benchmark_id:
            subsets = [subset for subset in subsets if subset["benchmark_id"] == benchmark_id]
        return 200, {"items": subsets}

    if path.startswith("/subsets/"):
        subset_id = path.split("/", 2)[2]
        subset = get_subset(subset_id)
        if subset is None:
            return 404, {"error": f"Unknown subset: {subset_id}"}
        return 200, subset

    if path == "/dataset-manifests":
        return 200, {
            "items": query_dataset_manifests(
                benchmark_id=_single(query, "benchmark_id"),
                subset_id=_single(query, "subset_id"),
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
            )
        }

    if path == "/study-contrasts":
        return 200, {
            "items": query_study_contrasts(
                benchmark_id=_single(query, "benchmark_id"),
                subset_id=_single(query, "subset_id"),
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
            )
        }

    if path == "/contrast-readiness":
        return 200, {
            "items": contrast_readiness_scores(
                benchmark_id=_single(query, "benchmark_id"),
                subset_id=_single(query, "subset_id"),
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
            )
        }

    if path == "/open-targets-genetics":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}

        size_raw = _single(query, "size")
        if size_raw:
            try:
                size = int(size_raw)
            except ValueError:
                return 400, {"error": "size must be an integer"}
        else:
            size = 200
        return 200, {"items": open_targets_genetics_scores(benchmark_id, size=size)}

    if path == "/open-targets-tractability":
        gene_ids = query.get("ensembl_gene_id") or []
        if not gene_ids:
            return 400, {"error": "at least one ensembl_gene_id query parameter is required"}
        return 200, {"items": open_targets_tractability_scores(gene_ids)}

    if path == "/pubmed-literature-support":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        candidate_top_n_raw = _single(query, "candidate_top_n")
        try:
            candidate_top_n = int(candidate_top_n_raw) if candidate_top_n_raw else 100
        except ValueError:
            return 400, {"error": "candidate_top_n must be an integer"}
        return 200, {
            "items": pubmed_literature_scores(
                benchmark_id=benchmark_id,
                subset_id=_single(query, "subset_id"),
                candidate_top_n=candidate_top_n,
            )
        }

    if path == "/reactome-pathway-support":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        return 200, {
            "items": reactome_pathway_scores(
                benchmark_id=benchmark_id,
                subset_id=_single(query, "subset_id"),
            )
        }

    if path == "/fused-target-evidence":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}

        min_support_raw = _single(query, "min_transcriptomics_support")
        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            min_transcriptomics_support = int(min_support_raw) if min_support_raw else 1
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 200
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 500
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 200
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 100
        except ValueError:
            return 400, {"error": "min_transcriptomics_support, genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, {
            "items": fused_target_evidence(
                benchmark_id=benchmark_id,
                subset_id=_single(query, "subset_id"),
                min_transcriptomics_support=min_transcriptomics_support,
                genetics_size=genetics_size,
                tractability_top_n=tractability_top_n,
                pathway_top_n=pathway_top_n,
                network_top_n=network_top_n,
            )
        }

    if path == "/benchmark-evaluation":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}

        min_support_raw = _single(query, "min_transcriptomics_support")
        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            min_transcriptomics_support = int(min_support_raw) if min_support_raw else 1
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 100
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 40
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 50
        except ValueError:
            return 400, {"error": "min_transcriptomics_support, genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, evaluate_fused_benchmark(
            benchmark_id,
            mode=mode or "strict",
            subset_id=_single(query, "subset_id"),
            min_transcriptomics_support=min_transcriptomics_support,
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/benchmark-integrity":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}
        return 200, benchmark_integrity_review(benchmark_id, mode=mode or "strict")

    if path == "/benchmark-mode-comparison":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        top_n_raw = _single(query, "top_n")
        try:
            top_n = int(top_n_raw) if top_n_raw else 10
        except ValueError:
            return 400, {"error": "top_n must be an integer"}
        return 200, compare_benchmark_modes(benchmark_id, top_n=top_n)

    if path == "/target-audit":
        benchmark_id = _single(query, "benchmark_id")
        gene_symbol = _single(query, "gene_symbol")
        if not benchmark_id or not gene_symbol:
            return 400, {"error": "benchmark_id and gene_symbol query parameters are required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}

        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 200
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 40
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 100
        except ValueError:
            return 400, {"error": "genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, audit_target_evidence(
            benchmark_id,
            gene_symbol=gene_symbol,
            mode=mode or "strict",
            subset_id=_single(query, "subset_id"),
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/target-evidence-graph":
        benchmark_id = _single(query, "benchmark_id")
        gene_symbol = _single(query, "gene_symbol")
        if not benchmark_id or not gene_symbol:
            return 400, {"error": "benchmark_id and gene_symbol query parameters are required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}

        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 200
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 40
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 100
        except ValueError:
            return 400, {"error": "genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, target_evidence_graph(
            benchmark_id,
            gene_symbol=gene_symbol,
            mode=mode or "strict",
            subset_id=_single(query, "subset_id"),
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/target-explanation":
        benchmark_id = _single(query, "benchmark_id")
        gene_symbol = _single(query, "gene_symbol")
        if not benchmark_id or not gene_symbol:
            return 400, {"error": "benchmark_id and gene_symbol query parameters are required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}

        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 200
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 40
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 100
        except ValueError:
            return 400, {"error": "genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, explain_target_evidence(
            benchmark_id,
            gene_symbol=gene_symbol,
            mode=mode or "strict",
            subset_id=_single(query, "subset_id"),
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/target-shortlist-explanations":
        benchmark_id = _single(query, "benchmark_id")
        if not benchmark_id:
            return 400, {"error": "benchmark_id query parameter is required"}
        mode = _mode(query)
        if mode == "__invalid__":
            return 400, {"error": "mode must be one of: strict, exploratory"}

        top_n_raw = _single(query, "top_n")
        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            top_n = int(top_n_raw) if top_n_raw else 10
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 200
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 40
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 100
        except ValueError:
            return 400, {"error": "top_n, genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, explain_target_shortlist(
            benchmark_id,
            mode=mode or "strict",
            subset_id=_single(query, "subset_id"),
            top_n=top_n,
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/rl-benchmark-evaluation":
        requested_modes = query.get("mode")
        if requested_modes:
            invalid_modes = [mode for mode in requested_modes if mode not in BENCHMARK_MODES]
            if invalid_modes:
                return 400, {"error": "mode must be one of: strict, exploratory"}
        benchmark_ids = query.get("benchmark_id")
        candidate_limit_raw = _single(query, "candidate_limit")
        horizon_raw = _single(query, "horizon")
        episodes_raw = _single(query, "episodes")
        seed_raw = _single(query, "seed")
        genetics_size_raw = _single(query, "genetics_size")
        tractability_top_n_raw = _single(query, "tractability_top_n")
        pathway_top_n_raw = _single(query, "pathway_top_n")
        network_top_n_raw = _single(query, "network_top_n")
        try:
            candidate_limit = int(candidate_limit_raw) if candidate_limit_raw else 500
            horizon = int(horizon_raw) if horizon_raw else 25
            episodes = int(episodes_raw) if episodes_raw else 10
            seed = int(seed_raw) if seed_raw else 0
            genetics_size = int(genetics_size_raw) if genetics_size_raw else 0
            tractability_top_n = int(tractability_top_n_raw) if tractability_top_n_raw else 0
            pathway_top_n = int(pathway_top_n_raw) if pathway_top_n_raw else 0
            network_top_n = int(network_top_n_raw) if network_top_n_raw else 0
        except ValueError:
            return 400, {"error": "candidate_limit, horizon, episodes, seed, genetics_size, tractability_top_n, pathway_top_n, and network_top_n must be integers"}
        return 200, evaluate_bandit_agents(
            benchmark_ids=benchmark_ids,
            modes=requested_modes or ["strict", "exploratory"],
            candidate_limit=candidate_limit,
            horizon=horizon,
            episodes=episodes,
            seed=seed,
            genetics_size=genetics_size,
            tractability_top_n=tractability_top_n,
            pathway_top_n=pathway_top_n,
            network_top_n=network_top_n,
        )

    if path == "/transcriptomics-evidence":
        benchmark_id = _single(query, "benchmark_id")
        subset_id = _single(query, "subset_id")
        if not benchmark_id and not subset_id:
            return 400, {"error": "benchmark_id or subset_id query parameter is required"}

        min_support_raw = _single(query, "min_support")
        if min_support_raw:
            try:
                min_support = int(min_support_raw)
            except ValueError:
                return 400, {"error": "min_support must be an integer"}
        else:
            min_support = 1
        return 200, {
            "items": transcriptomics_indication_evidence(
                benchmark_id=benchmark_id,
                subset_id=subset_id,
                tissue=_single(query, "tissue"),
                modality=_single(query, "modality"),
                min_support=min_support,
            )
        }

    if path == "/transcriptomics-fixture-scores":
        contrast_id = _single(query, "contrast_id")
        if not contrast_id:
            return 400, {"error": "contrast_id query parameter is required"}
        return 200, {"items": transcriptomics_fixture_scores(contrast_id)}

    if path == "/transcriptomics-real-scores":
        contrast_id = _single(query, "contrast_id")
        if not contrast_id:
            return 400, {"error": "contrast_id query parameter is required"}
        return 200, {"items": transcriptomics_real_scores(contrast_id)}

    return 404, {"error": f"Unknown route: {path}"}
