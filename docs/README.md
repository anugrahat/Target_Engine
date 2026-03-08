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

Principles:

- Prefer public, reproducible data over opaque internal curation.
- Distinguish verified literature claims from our design choices.
- Make dataset lineage explicit at the accession level for every indication.
- Optimize for scientific traceability, not just model novelty.
