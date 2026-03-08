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

Validation:

```bash
ruby scripts/validate_benchmark_packs.rb
ruby scripts/validate_contract_examples.rb
```

Conventions:

- verified facts stay in research docs first, then get promoted into contracts
- unresolved fields must remain `null` or `partial`, never guessed
- example records may be templates, but they must say so explicitly
