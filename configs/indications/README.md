# Indication Benchmark Packs

These files are the structured benchmark definitions for PrioriTx.

They translate the research notes into machine-readable inputs for future pipeline work.

Conventions:

- `status: verified` means the value is explicitly backed by a paper or supplement.
- `status: partial` means the case is useful but still has unresolved manifest gaps.
- `null` means the field is intentionally unknown and must not be guessed.

Current packs:

- `ipf_tnik.yaml`
- `hcc_cdk20.yaml`
- `als.yaml`
- `ad_phase_separation.yaml`

Validation:

```bash
ruby scripts/validate_benchmark_packs.rb
```

The validator is dependency-free and uses the schema in
`data_contracts/schemas/benchmark_pack.schema.json`.
