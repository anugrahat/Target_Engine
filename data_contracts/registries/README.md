# Registry Artifacts

These are generated first-wave registry fixtures derived from curated subset
configs in `configs/subsets/`.

The goal is to bridge specification and implementation:

- subset configs decide what PrioriTx is willing to benchmark
- registry artifacts turn those decisions into concrete dataset manifests and
  study contrasts

Directories:

- `dataset_manifests/`
- `study_contrasts/`

Build and validate:

```bash
ruby scripts/generate_first_wave_registry.rb
ruby scripts/validate_registry_artifacts.rb
```
