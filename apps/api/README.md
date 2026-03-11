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
- `/fused-target-evidence?benchmark_id=...`
- `/transcriptomics-evidence?subset_id=...`
- `/transcriptomics-real-scores?contrast_id=...`
- `/transcriptomics-fixture-scores?contrast_id=...`

Important:

- `transcriptomics-real-scores` fetches accession-backed GEO inputs on demand, caches GEO and HGNC resources under `tmp/`, and returns Ensembl-primary records with HGNC-backed symbols when available
- `open-targets-genetics` fetches benchmark-disease associations from the official Open Targets GraphQL API, caches the responses under `tmp/`, and scores genetics evidence with an explicit weighting toward the `genetic_association` datatype score
- `fused-target-evidence` merges cross-contrast transcriptomics and Open Targets genetics evidence by Ensembl gene into a transparent first-pass target-ranking surface
- `transcriptomics-evidence` aggregates accession-backed transcriptomics outputs across the real contrasts admitted for a benchmark slice and applies an explicit support rule (`adjusted_p_value <= 0.05` and `|log2_fold_change| >= 0.5`)
- current live real-data contrast IDs are `ipf_lung_core_gse52463`, `ipf_lung_core_gse24206`, `hcc_adult_core_gse60502`, and `hcc_adult_core_gse45267`
- current inferential statistics use transparent t-statistics, Student t distribution p-values, BH correction, and explicit degrees of freedom
- transcriptomics fixture score routes expose illustrative local fixtures only
- they are scaffolding for future real differential-expression ingestion
