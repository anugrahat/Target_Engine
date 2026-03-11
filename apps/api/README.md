# API App

Current implementation:

- `server.py`
  - Minimal dependency-free read-only HTTP API over the generated registry fixtures.

Run locally:

```bash
PYTHONPATH=packages/py python3 apps/api/server.py
```

Current routes:

- `/health`
- `/benchmarks`
- `/benchmark-dashboard-summary`
- `/benchmark-health-summary`
- `/subsets`
- `/subsets/{subset_id}`
- `/dataset-manifests`
- `/study-contrasts`
- `/contrast-readiness`
- `/open-targets-genetics?benchmark_id=...`
- `/open-targets-tractability?ensembl_gene_id=...`
- `/pubmed-literature-support?benchmark_id=...`
- `/reactome-pathway-support?benchmark_id=...`
- `/fused-target-evidence?benchmark_id=...`
- `/benchmark-evaluation?benchmark_id=...`
- `/benchmark-integrity?benchmark_id=...`
- `/benchmark-mode-comparison?benchmark_id=...`
- `/target-explanation?benchmark_id=...&gene_symbol=...`
- `/target-shortlist-explanations?benchmark_id=...`
- `/target-evidence-graph?benchmark_id=...&gene_symbol=...`
- `/target-audit?benchmark_id=...&gene_symbol=...`
- `/transcriptomics-evidence?subset_id=...`
- `/transcriptomics-real-scores?contrast_id=...`
- `/transcriptomics-fixture-scores?contrast_id=...`

Important:

- `transcriptomics-real-scores` fetches accession-backed GEO inputs on demand, caches GEO and HGNC resources under `tmp/`, and returns Ensembl-primary records with HGNC-backed symbols when available
- `open-targets-genetics` fetches benchmark-disease associations from the official Open Targets GraphQL API, caches the responses under `tmp/`, and scores genetics evidence with an explicit weighting toward the `genetic_association` datatype score
- `open-targets-tractability` fetches target tractability buckets from the official Open Targets GraphQL API and summarizes modality-level tractability evidence
- `pubmed-literature-support` queries official NCBI E-utilities for disease-gene mention counts and top PubMed hits in the current candidate slice, but remains diagnostic-only rather than fused into ranking
- `reactome-pathway-support` submits the current disease-support gene slice to the official Reactome Analysis Service, then overlaps enriched pathways with per-gene Reactome memberships for the candidate slice
- `fused-target-evidence` now applies a transparent four-stage rerank: transcriptomics plus genetics define the candidate set, Open Targets tractability and Reactome pathway support enrich the larger candidate slice, and STRING network support reranks a smaller top slice
- `benchmark-evaluation` scores the live fused ranking against source-backed benchmark positives and reports whether PrioriTx recovers targets such as `TNIK` and `CDK20`
- `benchmark-dashboard-summary` aggregates the current benchmark set into one dashboard-friendly payload with strict and exploratory leaders plus source-backed positive-target movement per indication
- `benchmark-health-summary` reduces the dashboard payload into benchmark health metrics such as recovered-in-top-N counts, improved versus worsened positives, and a simple readiness flag per indication
- `benchmark-evaluation` and `target-audit` now accept `mode=strict|exploratory`; strict uses the benchmark core subset, while exploratory uses the broader curated subset when one exists
- `benchmark-integrity` reports the subset, evidence-family leakage review, and benchmark-specific forbidden leakage items without running a full rank
- `benchmark-mode-comparison` compares strict and exploratory shortlist behavior, including how source-backed positive targets move in rank when the broader curated subset is enabled
- `target-explanation` returns a deterministic explanation summary for one target, including fused rank, evidence rationale, and caveats derived only from the current source-backed stack
- `target-shortlist-explanations` returns the top fused targets for a disease slice with deterministic overview, rationale, caveats, and a benchmark-positive overlay showing whether source-backed targets are recovered in the ranking or inside the current top slice
- `target-evidence-graph` returns a compact source-backed evidence graph for one target, linking the disease node to accession-backed transcriptomics contrasts, genetics support, tractability, Reactome pathways, and STRING partners
- `target-audit` explains benchmark misses by showing raw per-contrast transcriptomics measurements, support-rule pass/fail, and presence or absence in genetics and fused ranking
- `benchmark-evaluation` and `target-audit` use full paginated Open Targets genetics coverage by default so benchmark misses are not caused by an arbitrary top-`N` cutoff
- `transcriptomics-evidence` aggregates accession-backed transcriptomics outputs across the real contrasts admitted for a benchmark slice and applies an explicit support rule (`adjusted_p_value <= 0.05` and `|log2_fold_change| >= 0.5`)
- current live real-data contrast IDs now cover strict and extended subsets for `GSE52463`, `GSE24206`, `GSE92592`, `GSE150910`, `GSE60502`, `GSE45267`, `GSE77314`, and `GSE36376`
- current inferential statistics use transparent t-statistics, Student t distribution p-values, BH correction, and explicit degrees of freedom
- transcriptomics fixture score routes expose illustrative local fixtures only
- they are scaffolding for future real differential-expression ingestion
