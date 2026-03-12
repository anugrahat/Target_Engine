from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.http_api import handle_get


class HttpApiTests(unittest.TestCase):
    def test_health_route(self) -> None:
        status, payload = handle_get("/health", {})
        self.assertEqual(200, status)
        self.assertEqual({"status": "ok"}, payload)

    def test_benchmarks_route(self) -> None:
        status, payload = handle_get("/benchmarks", {})
        self.assertEqual(200, status)
        self.assertEqual(2, len(payload["items"]))

    def test_benchmark_dashboard_summary_route(self) -> None:
        mocked_result = {"benchmark_count": 2, "items": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api.summarize_benchmark_dashboard", return_value=mocked_result):
            status, payload = handle_get("/benchmark-dashboard-summary", {"top_n": ["3"]})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["benchmark_count"])

    def test_materialized_benchmark_dashboard_summary_route(self) -> None:
        mocked_result = {"benchmark_count": 2, "items": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api._materialized_payload", return_value=mocked_result):
            status, payload = handle_get("/materialized/benchmark-dashboard-summary", {})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["benchmark_count"])

    def test_benchmark_health_summary_route(self) -> None:
        mocked_result = {"benchmark_count": 2, "items": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api.summarize_benchmark_health", return_value=mocked_result):
            status, payload = handle_get("/benchmark-health-summary", {"top_n": ["10"]})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["benchmark_count"])

    def test_materialized_benchmark_health_summary_route(self) -> None:
        mocked_result = {"benchmark_count": 2, "items": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api._materialized_payload", return_value=mocked_result):
            status, payload = handle_get("/materialized/benchmark-health-summary", {})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["benchmark_count"])

    def test_benchmark_health_export_route(self) -> None:
        mocked_result = {"row_count": 2, "rows": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api.export_benchmark_health_rows", return_value=mocked_result):
            status, payload = handle_get("/benchmark-health-export", {"top_n": ["10"]})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["row_count"])

    def test_materialized_benchmark_health_export_route(self) -> None:
        mocked_result = {"row_count": 2, "rows": [{"benchmark_id": "ipf_tnik"}]}
        with patch("prioritx_data.http_api._materialized_payload", return_value=mocked_result):
            status, payload = handle_get("/materialized/benchmark-health-export", {})
        self.assertEqual(200, status)
        self.assertEqual(2, payload["row_count"])

    def test_materialized_benchmark_mode_comparison_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "benchmark_positive_comparison": []}
        with patch("prioritx_data.http_api._materialized_benchmark_payload", return_value=mocked_result):
            status, payload = handle_get("/materialized/benchmark-mode-comparison", {"benchmark_id": ["ipf_tnik"]})
        self.assertEqual(200, status)
        self.assertEqual("ipf_tnik", payload["benchmark_id"])

    def test_materialized_target_shortlist_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "items": [{"gene_symbol": "TNIK"}]}
        with patch("prioritx_data.http_api._materialized_benchmark_payload", return_value=mocked_result):
            status, payload = handle_get(
                "/materialized/target-shortlist-explanations",
                {"benchmark_id": ["ipf_tnik"], "mode": ["exploratory"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("TNIK", payload["items"][0]["gene_symbol"])

    def test_subset_detail_route(self) -> None:
        status, payload = handle_get("/subsets/ipf_lung_core", {})
        self.assertEqual(200, status)
        self.assertEqual("ipf_lung_core", payload["subset_id"])

    def test_dataset_manifest_filter_route(self) -> None:
        status, payload = handle_get("/dataset-manifests", {"subset_id": ["hcc_adult_core"]})
        self.assertEqual(200, status)
        self.assertEqual(4, len(payload["items"]))

    def test_contrast_readiness_route(self) -> None:
        status, payload = handle_get("/contrast-readiness", {"subset_id": ["ipf_lung_core"]})
        self.assertEqual(200, status)
        self.assertEqual(5, len(payload["items"]))
        self.assertIn("score", payload["items"][0])

    def test_transcriptomics_fixture_scores_route(self) -> None:
        status, payload = handle_get(
            "/transcriptomics-fixture-scores",
            {"contrast_id": ["hcc_adult_core_gse77314"]},
        )
        self.assertEqual(200, status)
        self.assertEqual(5, len(payload["items"]))
        self.assertEqual("fixture_transcriptomics_gene_score", payload["items"][0]["score_name"])

    def test_transcriptomics_fixture_scores_requires_contrast_id(self) -> None:
        status, payload = handle_get("/transcriptomics-fixture-scores", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_transcriptomics_real_scores_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "real_transcriptomics_inferential_score"}]
        with patch("prioritx_data.http_api.transcriptomics_real_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/transcriptomics-real-scores",
                {"contrast_id": ["ipf_lung_core_gse52463"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("real_transcriptomics_inferential_score", payload["items"][0]["score_name"])

    def test_transcriptomics_evidence_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "cross_contrast_transcriptomics_evidence_score"}]
        with patch("prioritx_data.http_api.transcriptomics_indication_evidence", return_value=mocked_items):
            status, payload = handle_get(
                "/transcriptomics-evidence",
                {"subset_id": ["hcc_adult_core"], "min_support": ["2"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("cross_contrast_transcriptomics_evidence_score", payload["items"][0]["score_name"])

    def test_open_targets_genetics_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "open_targets_genetics_evidence_score"}]
        with patch("prioritx_data.http_api.open_targets_genetics_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/open-targets-genetics",
                {"benchmark_id": ["ipf_tnik"], "size": ["25"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("open_targets_genetics_evidence_score", payload["items"][0]["score_name"])

    def test_open_targets_genetics_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/open-targets-genetics", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_open_targets_genetics_validates_size(self) -> None:
        status, payload = handle_get("/open-targets-genetics", {"benchmark_id": ["ipf_tnik"], "size": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_open_targets_tractability_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "open_targets_tractability_score"}]
        with patch("prioritx_data.http_api.open_targets_tractability_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/open-targets-tractability",
                {"ensembl_gene_id": ["ENSG000001", "ENSG000002"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("open_targets_tractability_score", payload["items"][0]["score_name"])

    def test_open_targets_tractability_requires_gene_ids(self) -> None:
        status, payload = handle_get("/open-targets-tractability", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_reactome_pathway_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "reactome_pathway_support_score"}]
        with patch("prioritx_data.http_api.reactome_pathway_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/reactome-pathway-support",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_extended"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("reactome_pathway_support_score", payload["items"][0]["score_name"])

    def test_reactome_pathway_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/reactome-pathway-support", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_pubmed_literature_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "pubmed_literature_support_score"}]
        with patch("prioritx_data.http_api.pubmed_literature_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/pubmed-literature-support",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_extended"], "candidate_top_n": ["25"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("pubmed_literature_support_score", payload["items"][0]["score_name"])

    def test_pubmed_literature_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/pubmed-literature-support", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_pubmed_literature_validates_candidate_top_n(self) -> None:
        status, payload = handle_get("/pubmed-literature-support", {"benchmark_id": ["ipf_tnik"], "candidate_top_n": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_fused_target_evidence_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "fused_target_evidence_score"}]
        with patch("prioritx_data.http_api.fused_target_evidence", return_value=mocked_items):
            status, payload = handle_get(
                "/fused-target-evidence",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_core"], "genetics_size": ["25"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("fused_target_evidence_score", payload["items"][0]["score_name"])

    def test_fused_target_evidence_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/fused-target-evidence", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_fused_target_evidence_validates_int_params(self) -> None:
        status, payload = handle_get("/fused-target-evidence", {"benchmark_id": ["ipf_tnik"], "genetics_size": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_evaluation_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "metrics": {"best_rank": 4}}
        with patch("prioritx_data.http_api.evaluate_fused_benchmark", return_value=mocked_result):
            status, payload = handle_get(
                "/benchmark-evaluation",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_core"], "network_top_n": ["25"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("ipf_tnik", payload["benchmark_id"])

    def test_benchmark_evaluation_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/benchmark-evaluation", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_dashboard_summary_validates_top_n(self) -> None:
        status, payload = handle_get("/benchmark-dashboard-summary", {"top_n": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_health_summary_validates_top_n(self) -> None:
        status, payload = handle_get("/benchmark-health-summary", {"top_n": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_health_export_validates_top_n(self) -> None:
        status, payload = handle_get("/benchmark-health-export", {"top_n": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_materialized_benchmark_route_returns_not_found_when_missing(self) -> None:
        with patch("prioritx_data.http_api._materialized_payload", return_value=None):
            status, payload = handle_get("/materialized/benchmark-health-summary", {})
        self.assertEqual(404, status)
        self.assertIn("error", payload)

    def test_materialized_target_shortlist_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/materialized/target-shortlist-explanations", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_materialized_target_shortlist_validates_mode(self) -> None:
        status, payload = handle_get(
            "/materialized/target-shortlist-explanations",
            {"benchmark_id": ["ipf_tnik"], "mode": ["invalid"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_evaluation_validates_int_params(self) -> None:
        status, payload = handle_get("/benchmark-evaluation", {"benchmark_id": ["ipf_tnik"], "network_top_n": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_evaluation_validates_mode(self) -> None:
        status, payload = handle_get("/benchmark-evaluation", {"benchmark_id": ["ipf_tnik"], "mode": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_integrity_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "mode": "strict"}
        with patch("prioritx_data.http_api.benchmark_integrity_review", return_value=mocked_result):
            status, payload = handle_get("/benchmark-integrity", {"benchmark_id": ["ipf_tnik"], "mode": ["strict"]})
        self.assertEqual(200, status)
        self.assertEqual("strict", payload["mode"])

    def test_benchmark_mode_comparison_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "benchmark_positive_comparison": []}
        with patch("prioritx_data.http_api.compare_benchmark_modes", return_value=mocked_result):
            status, payload = handle_get("/benchmark-mode-comparison", {"benchmark_id": ["ipf_tnik"], "top_n": ["5"]})
        self.assertEqual(200, status)
        self.assertEqual("ipf_tnik", payload["benchmark_id"])

    def test_target_audit_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "gene_symbol": "TNIK"}
        with patch("prioritx_data.http_api.audit_target_evidence", return_value=mocked_result):
            status, payload = handle_get(
                "/target-audit",
                {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "genetics_size": ["500"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("TNIK", payload["gene_symbol"])

    def test_target_evidence_graph_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "gene_symbol": "TNIK", "graph": {"nodes": [], "edges": []}}
        with patch("prioritx_data.http_api.target_evidence_graph", return_value=mocked_result):
            status, payload = handle_get(
                "/target-evidence-graph",
                {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("TNIK", payload["gene_symbol"])

    def test_target_explanation_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "gene_symbol": "TNIK", "overview": "TNIK summary"}
        with patch("prioritx_data.http_api.explain_target_evidence", return_value=mocked_result):
            status, payload = handle_get(
                "/target-explanation",
                {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("TNIK", payload["gene_symbol"])

    def test_target_shortlist_explanations_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "items": [{"gene_symbol": "MUC5B"}]}
        with patch("prioritx_data.http_api.explain_target_shortlist", return_value=mocked_result):
            status, payload = handle_get(
                "/target-shortlist-explanations",
                {"benchmark_id": ["ipf_tnik"], "top_n": ["5"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("MUC5B", payload["items"][0]["gene_symbol"])

    def test_rl_benchmark_evaluation_route(self) -> None:
        mocked_result = {"evaluation_kind": "offline_contextual_bandit_replay", "agents": []}
        with patch("prioritx_data.http_api.evaluate_bandit_agents", return_value=mocked_result):
            status, payload = handle_get(
                "/rl-benchmark-evaluation",
                {"candidate_limit": ["250"], "episodes": ["3"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("offline_contextual_bandit_replay", payload["evaluation_kind"])

    def test_knowledge_graph_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "graph": {"nodes": [], "edges": []}}
        with patch("prioritx_data.http_api.build_benchmark_knowledge_graph", return_value=mocked_result):
            status, payload = handle_get("/knowledge-graph", {"benchmark_id": ["ipf_tnik"], "mode": ["strict"]})
        self.assertEqual(200, status)
        self.assertEqual("ipf_tnik", payload["benchmark_id"])

    def test_graph_feature_scores_route(self) -> None:
        mocked_items = [{"gene_symbol": "TNIK", "score_name": "knowledge_graph_support_score"}]
        with patch("prioritx_data.http_api.graph_feature_scores", return_value=mocked_items):
            status, payload = handle_get("/graph-feature-scores", {"benchmark_id": ["ipf_tnik"], "mode": ["strict"]})
        self.assertEqual(200, status)
        self.assertEqual("knowledge_graph_support_score", payload["items"][0]["score_name"])

    def test_mechanistic_support_route(self) -> None:
        mocked_items = [{"gene_symbol": "TNIK", "score_name": "mechanistic_support_score"}]
        with patch("prioritx_data.http_api.mechanistic_support_scores", return_value=mocked_items):
            status, payload = handle_get("/mechanistic-support", {"benchmark_id": ["ipf_tnik"], "mode": ["exploratory"]})
        self.assertEqual(200, status)
        self.assertEqual("mechanistic_support_score", payload["items"][0]["score_name"])

    def test_signaling_program_activity_route(self) -> None:
        mocked_items = [{"program_ref": "beta_catenin_signaling", "score_name": "signaling_program_activity_score"}]
        with patch("prioritx_data.http_api.signaling_program_activity_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/signaling-program-activity",
                {"benchmark_id": ["hcc_cdk20"], "subset_id": ["hcc_adult_extended"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("signaling_program_activity_score", payload["items"][0]["score_name"])

    def test_signaling_support_route(self) -> None:
        mocked_items = [{"gene_symbol": "CDK20", "score_name": "signaling_state_support_score"}]
        with patch("prioritx_data.http_api.signaling_support_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/signaling-support",
                {"benchmark_id": ["hcc_cdk20"], "subset_id": ["hcc_adult_extended"], "mode": ["exploratory"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("signaling_state_support_score", payload["items"][0]["score_name"])

    def test_proteophospho_program_activity_route(self) -> None:
        mocked_items = [{"program_ref": "beta_catenin_signaling", "score_name": "proteophospho_program_activity_score"}]
        with patch("prioritx_data.http_api.proteophospho_program_activity_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/proteophospho-program-activity",
                {"benchmark_id": ["hcc_cdk20"], "subset_id": ["hcc_adult_extended"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("proteophospho_program_activity_score", payload["items"][0]["score_name"])

    def test_proteophospho_support_route(self) -> None:
        mocked_items = [{"gene_symbol": "CDK20", "score_name": "proteophospho_support_score"}]
        with patch("prioritx_data.http_api.proteophospho_support_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/proteophospho-support",
                {"benchmark_id": ["hcc_cdk20"], "subset_id": ["hcc_adult_extended"], "mode": ["exploratory"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("proteophospho_support_score", payload["items"][0]["score_name"])

    def test_cell_state_program_activity_route(self) -> None:
        mocked_items = [{"program_ref": "ipf_myofibroblast_program", "score_name": "cell_state_program_activity_score"}]
        with patch("prioritx_data.http_api.cell_state_program_activity_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/cell-state-program-activity",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_extended"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("cell_state_program_activity_score", payload["items"][0]["score_name"])

    def test_cell_state_support_route(self) -> None:
        mocked_items = [{"gene_symbol": "TNIK", "score_name": "cell_state_support_score"}]
        with patch("prioritx_data.http_api.cell_state_support_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/cell-state-support",
                {"benchmark_id": ["ipf_tnik"], "subset_id": ["ipf_lung_extended"], "mode": ["exploratory"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("cell_state_support_score", payload["items"][0]["score_name"])

    def test_graph_augmented_target_evidence_route(self) -> None:
        mocked_items = [{"gene_symbol": "TNIK", "score_name": "graph_augmented_target_evidence_score"}]
        with patch("prioritx_data.http_api.graph_augmented_target_evidence", return_value=mocked_items):
            status, payload = handle_get(
                "/graph-augmented-target-evidence",
                {"benchmark_id": ["ipf_tnik"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("graph_augmented_target_evidence_score", payload["items"][0]["score_name"])

    def test_graph_augmented_benchmark_evaluation_route(self) -> None:
        mocked_result = {"benchmark_id": "ipf_tnik", "metrics": {"best_rank": 1}}
        with patch("prioritx_data.http_api.evaluate_graph_augmented_benchmark", return_value=mocked_result):
            status, payload = handle_get(
                "/graph-augmented-benchmark-evaluation",
                {"benchmark_id": ["ipf_tnik"], "mode": ["strict"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("ipf_tnik", payload["benchmark_id"])

    def test_target_audit_requires_benchmark_id_and_gene_symbol(self) -> None:
        status, payload = handle_get("/target-audit", {"benchmark_id": ["ipf_tnik"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_mode_comparison_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/benchmark-mode-comparison", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_benchmark_mode_comparison_validates_top_n(self) -> None:
        status, payload = handle_get("/benchmark-mode-comparison", {"benchmark_id": ["ipf_tnik"], "top_n": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_audit_validates_int_params(self) -> None:
        status, payload = handle_get(
            "/target-audit",
            {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "genetics_size": ["abc"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_audit_validates_mode(self) -> None:
        status, payload = handle_get(
            "/target-audit",
            {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "mode": ["bad"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_evidence_graph_requires_benchmark_id_and_gene_symbol(self) -> None:
        status, payload = handle_get("/target-evidence-graph", {"benchmark_id": ["ipf_tnik"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_evidence_graph_validates_mode(self) -> None:
        status, payload = handle_get(
            "/target-evidence-graph",
            {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "mode": ["bad"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_explanation_requires_benchmark_id_and_gene_symbol(self) -> None:
        status, payload = handle_get("/target-explanation", {"benchmark_id": ["ipf_tnik"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_explanation_validates_mode(self) -> None:
        status, payload = handle_get(
            "/target-explanation",
            {"benchmark_id": ["ipf_tnik"], "gene_symbol": ["TNIK"], "mode": ["bad"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_shortlist_explanations_requires_benchmark_id(self) -> None:
        status, payload = handle_get("/target-shortlist-explanations", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_shortlist_explanations_validates_mode(self) -> None:
        status, payload = handle_get(
            "/target-shortlist-explanations",
            {"benchmark_id": ["ipf_tnik"], "mode": ["bad"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_target_shortlist_explanations_validates_int_params(self) -> None:
        status, payload = handle_get(
            "/target-shortlist-explanations",
            {"benchmark_id": ["ipf_tnik"], "top_n": ["bad"]},
        )
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_rl_benchmark_evaluation_validates_mode(self) -> None:
        status, payload = handle_get("/rl-benchmark-evaluation", {"mode": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_rl_benchmark_evaluation_validates_int_params(self) -> None:
        status, payload = handle_get("/rl-benchmark-evaluation", {"episodes": ["bad"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_graph_routes_require_benchmark_id(self) -> None:
        for route in ("/knowledge-graph", "/mechanistic-support", "/cell-state-program-activity", "/cell-state-support", "/signaling-program-activity", "/signaling-support", "/graph-feature-scores", "/graph-augmented-target-evidence", "/graph-augmented-benchmark-evaluation"):
            status, payload = handle_get(route, {})
            self.assertEqual(400, status)
            self.assertIn("error", payload)

    def test_graph_routes_validate_mode(self) -> None:
        for route in ("/knowledge-graph", "/mechanistic-support", "/cell-state-support", "/signaling-support", "/graph-feature-scores", "/graph-augmented-target-evidence", "/graph-augmented-benchmark-evaluation"):
            status, payload = handle_get(route, {"benchmark_id": ["ipf_tnik"], "mode": ["bad"]})
            self.assertEqual(400, status)
            self.assertIn("error", payload)

    def test_transcriptomics_evidence_requires_scope(self) -> None:
        status, payload = handle_get("/transcriptomics-evidence", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_transcriptomics_evidence_validates_min_support(self) -> None:
        status, payload = handle_get("/transcriptomics-evidence", {"subset_id": ["hcc_adult_core"], "min_support": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_transcriptomics_real_scores_requires_contrast_id(self) -> None:
        status, payload = handle_get("/transcriptomics-real-scores", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_unknown_route_returns_404(self) -> None:
        status, payload = handle_get("/does-not-exist", {})
        self.assertEqual(404, status)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
