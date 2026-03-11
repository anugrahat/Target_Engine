# Curated Benchmark Subsets

These files define PrioriTx-curated first-wave benchmark subsets.

They are intentionally stricter than the paper-disclosed benchmark packs in
`configs/indications/` and are meant to answer a different question:

- `configs/indications/*.yaml`
  - what the source paper publicly disclosed
- `configs/subsets/*.yaml`
  - what PrioriTx should admit into a first-wave benchmark after curation

Current curated candidates:

- `ipf_lung_core.yaml`
- `ipf_lung_extended.yaml`
- `hcc_adult_core.yaml`

Validate with:

```bash
ruby scripts/validate_subset_configs.rb
```
