# PrioriTx Design Docs

This directory is the pre-implementation source of truth for PrioriTx.

Documents:

- `research/pandaomics-insilico-baseline.md`
  - Verified findings from the PandaOmics paper and supplementary tables.
  - Separates public facts from inference and from PrioriTx proposals.
- `research/open-replacement-map.md`
  - Maps the verified PandaOmics score families to open, reproducible PrioriTx replacements.
- `research/case_studies/`
  - Case-by-case verification notes for ALS, IPF/TNIK, HCC/CDK20, and AD phase-separation work.
  - Includes a benchmark readiness ranking so implementation starts with the strongest public evidence.
- `research/manifests/`
  - Pre-implementation manifest stubs with verified datasets and unresolved gaps for the benchmark cases.
- `../data_contracts/`
  - Machine-readable schema layer for benchmark packs, dataset manifests, study contrasts, and rank outputs.
- `architecture/prioritx-system-architecture.md`
  - Proposed end-to-end system design for PrioriTx.
- `architecture/repository-layout.md`
  - Recommended repository and package structure.
- `specs/prioritx-platform-spec.md`
  - Product, data, ML, API, and evaluation specs that gate implementation.
- `specs/benchmark-evaluation-protocol.md`
  - Benchmarking rules that prevent downstream translational success from leaking into discovery-time evaluation.
- `specs/first_wave_benchmark_subsets.md`
  - Curated first-wave cohort subsets that are stricter than the paper-disclosed benchmark packs.
- `../data_contracts/registries/`
  - Generated registry fixtures that turn curated subset decisions into implementation-ready dataset manifests and study contrasts.

Principles:

- Prefer public, reproducible data over opaque internal curation.
- Distinguish verified literature claims from our design choices.
- Make dataset lineage explicit at the accession level for every indication.
- Optimize for scientific traceability, not just model novelty.

Implementation scaffold:

- `packages/py/prioritx_data/registry.py`
  - Minimal loader for generated first-wave registry fixtures.
- `packages/py/prioritx_data/service.py`
  - Query layer for benchmarks, subsets, dataset manifests, and study contrasts.
- `apps/api/server.py`
  - Minimal dependency-free read-only HTTP API over the curated registry layer.
- `packages/py/prioritx_features/transcriptomics.py`
  - Metadata-derived transcriptomics readiness features over curated study contrasts.
- `packages/py/prioritx_rank/baseline.py`
  - Transparent baseline scoring for contrast readiness, explicitly not yet a target-ranking model.
- `tests/unit/test_registry.py`
  - Sanity checks that the registry fixtures are consumable by code.
