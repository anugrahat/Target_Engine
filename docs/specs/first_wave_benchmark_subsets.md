# First-Wave Benchmark Subsets

## Purpose

The benchmark packs in `configs/indications/` preserve what the source papers
publicly disclosed.

That is not the same as what PrioriTx should benchmark first.

This document defines the stricter first-wave benchmark subsets that PrioriTx
should use to minimize cohort-mixing, disease-definition drift, and leakage.

## IPF

Curated subset:

- `configs/subsets/ipf_lung_core.yaml`

Why:

- focuses on lung-tissue case-control cohorts
- excludes blood-only cohorts from the first-wave benchmark
- excludes mixed-ILD, mixed-IIP, longitudinal, or unresolved-count cohorts

Included directly:

- `GSE52463`
- `GSE72073`
- `GSE92592`
- `GSE24206`
- `GSE138283`

Held out for later curation:

- `GSE150910`
- `GSE83717`
- `GSE21369`
- `GSE99621`

## HCC

Curated subset:

- `configs/subsets/hcc_adult_core.yaml`

Why:

- excludes hepatoblastoma cohorts
- excludes mixed cirrhosis-HCC cohorts
- excludes unresolved multiregional cohorts until per-arm counts are explicit

Included directly:

- `GSE45267`
- `GSE60502`
- `GSE77314`
- `TCGA-LIHC` using public `primary tumor` and `solid tissue normal` arms

Held out for later curation:

- `GSE36376`
- `GSE102079`
- `E-MTAB-5905`

Excluded from adult-HCC benchmarking:

- `GSE107170`
- `GSE133039`
- `GSE104766`

## Rule

If a cohort is listed in a source paper but does not meet first-wave subset
rules, it stays in the benchmark pack and out of the first-wave subset.
