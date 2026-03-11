# PrioriTx

PrioriTx is a scientifically rigorous therapeutic target prioritization platform being designed to outperform the public PandaOmics baseline on reproducibility, provenance, evaluation rigor, and evidence quality.

This repository is currently in the pre-implementation phase.

## Current Focus

- verify benchmark case studies from primary literature
- recover accession-level manifests where public sources allow it
- define architecture, repository layout, and implementation gates before coding

## Start Here

- [AGENTS.md](./AGENTS.md)
- [docs/README.md](./docs/README.md)
- [docs/research/case_studies/benchmark_readiness.md](./docs/research/case_studies/benchmark_readiness.md)
- [docs/research/manifests/README.md](./docs/research/manifests/README.md)
- [configs/indications/README.md](./configs/indications/README.md)
- [configs/subsets/README.md](./configs/subsets/README.md)
- [data_contracts/README.md](./data_contracts/README.md)
- [data_contracts/schemas/benchmark_pack.schema.json](./data_contracts/schemas/benchmark_pack.schema.json)

## Benchmark Priority

Current benchmark ordering after source verification:

1. idiopathic pulmonary fibrosis / TNIK
2. amyotrophic lateral sclerosis
3. hepatocellular carcinoma / CDK20
4. Alzheimer's disease / phase separation

## Repository Status

- monorepo scaffolding is in place for Python packages, pipelines, apps, infra, and tests
- research, architecture, benchmark packs, curated subsets, generated registry fixtures, and a minimal read-only registry API are in place
- a first metadata-derived transcriptomics readiness layer is in place over curated study contrasts
- the read-only API also exposes metadata-derived contrast readiness scores
- fourteen accession-backed transcriptomics contrast IDs are now live across strict and extended benchmark subsets, covering:
  - `GSE52463` via GEO RNA-seq sample-level gene-count tables
  - `GSE24206` via unpaired GEO series-matrix microarray values plus `GPL570.annot.gz`
  - `GSE92592` via GEO series-level RNA-seq count matrix plus HGNC-backed symbol-to-Ensembl mapping
  - `GSE150910` via explicit IPF/control subsetting from a public mixed-diagnosis gene-count matrix
  - `GSE60502` via paired GEO series-matrix microarray values plus `GPL96.annot.gz`
  - `GSE45267` via unpaired GEO series-matrix microarray values plus `GPL570.annot.gz`
  - `GSE77314` via GEO supplementary expression workbook parsed directly from the official `.xlsx` package
  - `GSE36376` via GEO series-matrix microarray values plus the official `GPL10558` Illumina supplementary platform table
- all real-data paths expose inferential statistics, BH-adjusted p-values, and HGNC-backed identifiers where recoverable
- Open Targets genetics evidence is now available for benchmark diseases through the official GraphQL API
- Open Targets tractability evidence is now available for target genes through the official GraphQL API
- Reactome pathway support is now available through the official Reactome Analysis Service by intersecting disease-enriched pathways with per-gene Reactome memberships
- STRING-based network support is now available over the top disease-specific candidate slice
- a first fused target-evidence layer now combines transcriptomics, genetics, tractability, Reactome pathway support, and STRING network support by Ensembl gene
- source-backed benchmark target assertions now evaluate whether the live fused ranking recovers paper-backed positives such as `TNIK` and `CDK20`
- illustrative transcriptomics gene-stat fixtures remain isolated for test scaffolding only

## Validation

Benchmark packs in `configs/indications/` are the canonical machine-readable definitions for the first PrioriTx benchmark cases.

Validate them with:

```bash
ruby scripts/validate_benchmark_packs.rb
ruby scripts/validate_subset_configs.rb
ruby scripts/validate_contract_examples.rb
ruby scripts/validate_transcriptomics_fixtures.rb
ruby scripts/generate_first_wave_registry.rb
ruby scripts/validate_registry_artifacts.rb
ruby scripts/validate_benchmark_assertions.rb
PYTHONPATH=packages/py python3 -m unittest discover -s tests/unit -p 'test_*.py'
PYTHONPATH=packages/py python3 apps/api/server.py
PYTHONPATH=packages/py python3 -m prioritx_rank.cli
PYTHONPATH=packages/py python3 -m prioritx_eval.cli
python3 scripts/save_verification_report.py
```

Saved verification reports are written locally under `tmp/verification_reports/`.
