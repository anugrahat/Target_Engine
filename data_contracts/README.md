# Data Contracts

PrioriTx uses explicit data contracts before implementation so that research assets
become stable machine-readable interfaces.

Current contract layers:

- `schemas/benchmark_pack.schema.json`
  - the benchmark-case contract used by `configs/indications/*.yaml`
- `schemas/dataset_manifest.schema.json`
  - one structured dataset record, including cohorts and provenance
- `schemas/study_contrast.schema.json`
  - one analysis-ready case vs control contrast definition
- `schemas/target_rank_record.schema.json`
  - one ranked-target output record, including component-level provenance
- `schemas/benchmark_subset.schema.json`
  - one PrioriTx-curated admissible benchmark subset definition
- `schemas/transcriptomics_gene_stat.schema.json`
  - one illustrative local gene-level transcriptomics record for scaffolded DE-style inputs
- `schemas/gene_evidence_aggregate.schema.json`
  - one cross-contrast transcriptomics evidence record aggregated at the indication slice level
- `schemas/open_targets_genetics_record.schema.json`
  - one source-backed Open Targets genetics evidence record for a benchmark disease
- `schemas/fused_target_evidence_record.schema.json`
  - one merged target-evidence record combining transcriptomics, genetics, tractability, and network support by Ensembl gene
- `schemas/open_targets_tractability_record.schema.json`
  - one source-backed Open Targets tractability evidence record for a set of gene targets
- `schemas/string_network_support_record.schema.json`
  - one STRING-based network support record over a disease-specific candidate slice
- `schemas/benchmark_target_assertion.schema.json`
  - one source-backed positive-target assertion pack for benchmark evaluation
- `assertions/`
  - machine-checkable benchmark target assertions used to score live fused rankings against paper-backed positives
- `registries/`
  - generated first-wave dataset-manifest and study-contrast fixtures
- `fixtures/transcriptomics/`
  - small illustrative local DE-style fixtures used only for loader and API scaffolding

Validation:

```bash
ruby scripts/validate_benchmark_packs.rb
ruby scripts/validate_subset_configs.rb
ruby scripts/validate_contract_examples.rb
ruby scripts/validate_transcriptomics_fixtures.rb
ruby scripts/generate_first_wave_registry.rb
ruby scripts/validate_registry_artifacts.rb
ruby scripts/validate_benchmark_assertions.rb
```

Conventions:

- verified facts stay in research docs first, then get promoted into contracts
- unresolved fields must remain `null` or `partial`, never guessed
- example records may be templates, but they must say so explicitly
