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
- `/subsets`
- `/subsets/{subset_id}`
- `/dataset-manifests`
- `/study-contrasts`
- `/contrast-readiness`
- `/open-targets-genetics?benchmark_id=...`
- `/open-targets-tractability?ensembl_gene_id=...`
- `/fused-target-evidence?benchmark_id=...`
- `/benchmark-evaluation?benchmark_id=...`
- `/target-audit?benchmark_id=...&gene_symbol=...`
- `/transcriptomics-evidence?subset_id=...`
- `/transcriptomics-real-scores?contrast_id=...`
- `/transcriptomics-fixture-scores?contrast_id=...`

Important:

- `transcriptomics-real-scores` fetches accession-backed GEO inputs on demand, caches GEO and HGNC resources under `tmp/`, and returns Ensembl-primary records with HGNC-backed symbols when available
- `open-targets-genetics` fetches benchmark-disease associations from the official Open Targets GraphQL API, caches the responses under `tmp/`, and scores genetics evidence with an explicit weighting toward the `genetic_association` datatype score
- `open-targets-tractability` fetches target tractability buckets from the official Open Targets GraphQL API and summarizes modality-level tractability evidence
- `fused-target-evidence` now applies a transparent three-stage rerank: transcriptomics plus genetics define the candidate set, Open Targets tractability enriches a larger top slice, and STRING network support reranks a smaller top slice
- `benchmark-evaluation` scores the live fused ranking against source-backed benchmark positives and reports whether PrioriTx recovers targets such as `TNIK` and `CDK20`
- `target-audit` explains benchmark misses by showing raw per-contrast transcriptomics measurements, support-rule pass/fail, and presence or absence in genetics and fused ranking
- `benchmark-evaluation` and `target-audit` use full paginated Open Targets genetics coverage by default so benchmark misses are not caused by an arbitrary top-`N` cutoff
- `transcriptomics-evidence` aggregates accession-backed transcriptomics outputs across the real contrasts admitted for a benchmark slice and applies an explicit support rule (`adjusted_p_value <= 0.05` and `|log2_fold_change| >= 0.5`)
- current live real-data contrast IDs are `ipf_lung_core_gse52463`, `ipf_lung_core_gse24206`, `ipf_lung_core_gse92592`, `hcc_adult_core_gse60502`, and `hcc_adult_core_gse45267`
- current inferential statistics use transparent t-statistics, Student t distribution p-values, BH correction, and explicit degrees of freedom
- transcriptomics fixture score routes expose illustrative local fixtures only
- they are scaffolding for future real differential-expression ingestion
