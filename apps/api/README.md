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
- `/transcriptomics-real-scores?contrast_id=...`
- `/transcriptomics-fixture-scores?contrast_id=...`

Important:

- `transcriptomics-real-scores` fetches accession-backed GEO inputs on demand, caches GEO and HGNC resources under `tmp/`, and returns Ensembl-primary records with HGNC-backed symbols when available
- current live real-data contrast IDs are `ipf_lung_core_gse52463` and `hcc_adult_core_gse60502`
- current inferential statistics use transparent t-statistics with a normal-approximation two-sided p-value in the stdlib-only runtime
- transcriptomics fixture score routes expose illustrative local fixtures only
- they are scaffolding for future real differential-expression ingestion
