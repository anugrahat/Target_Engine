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
- four accession-backed transcriptomics evidence paths are now live:
  - `ipf_lung_core_gse52463` via GEO RNA-seq sample-level gene-count tables
  - `ipf_lung_core_gse24206` via unpaired GEO series-matrix microarray values plus `GPL570.annot.gz`
  - `hcc_adult_core_gse60502` via paired GEO series-matrix microarray values plus `GPL96.annot.gz`
  - `hcc_adult_core_gse45267` via unpaired GEO series-matrix microarray values plus `GPL570.annot.gz`
- all real-data paths expose inferential statistics, BH-adjusted p-values, and HGNC-backed identifiers where recoverable
- Open Targets genetics evidence is now available for benchmark diseases through the official GraphQL API
- a first fused target-evidence layer now combines transcriptomics and genetics by Ensembl gene
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
PYTHONPATH=packages/py python3 -m unittest discover -s tests/unit -p 'test_*.py'
PYTHONPATH=packages/py python3 apps/api/server.py
PYTHONPATH=packages/py python3 -m prioritx_rank.cli
```
