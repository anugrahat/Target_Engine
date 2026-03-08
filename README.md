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
- research, architecture, benchmark packs, curated subsets, and generated registry fixtures are in place
- next milestone is implementing the dataset-registry and contrast-registry service layer on top of the generated fixtures

## Validation

Benchmark packs in `configs/indications/` are the canonical machine-readable definitions for the first PrioriTx benchmark cases.

Validate them with:

```bash
ruby scripts/validate_benchmark_packs.rb
ruby scripts/validate_subset_configs.rb
ruby scripts/validate_contract_examples.rb
ruby scripts/generate_first_wave_registry.rb
ruby scripts/validate_registry_artifacts.rb
PYTHONPATH=packages/py python3 -m unittest discover -s tests/unit -p 'test_*.py'
```
