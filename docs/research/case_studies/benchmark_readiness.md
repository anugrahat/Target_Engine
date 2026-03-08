# Benchmark Readiness Summary

## Goal

Rank the first candidate indication case studies by how ready they are for PrioriTx benchmark construction.

## Summary Table

| Case | Primary paper | Manifest readiness | Why |
| --- | --- | --- | --- |
| IPF / TNIK | Nature Biotechnology 2024 | High | The discovery GEO cohorts are explicitly listed in `Data availability`, and validation is unusually strong. |
| ALS | Frontiers in Aging Neuroscience 2022 | Medium-High | Multiple accession-coded datasets are named, and the disease framing is cleaner than the public HCC pool, though part of the stack is consortium-based (`Answer ALS`). |
| HCC / CDK20 | Chemical Science 2023 | Medium | The 10 discovery cohorts are explicitly listed, but the public pool is heterogeneous and includes hepatoblastoma and mixed liver-disease cohorts. |
| AD / phase separation | PNAS 2023 | Medium | The paper is scientifically useful and exposes structured supplements, but accession-level recovery is still unresolved. |

## Recommended Build Order

1. IPF
2. ALS
3. HCC
4. AD

## Why IPF Stays First

- the paper publicly discloses the discovery cohorts directly in the article text
- several cohort-level sample definitions are already recoverable from GEO
- the disease framing is cleaner than the public HCC case
- some IPF cohorts are still mixed or longitudinal, but the public pool is easier to curate into defensible first-wave contrasts

## Why HCC Moved Down

- the accession list is public, but the cohort pool is more heterogeneous than it first appeared
- at least two disclosed cohorts are hepatoblastoma, not HCC
- several controls are adjacent-normal or mixed liver-disease comparators rather than clean healthy controls
- target-discovery evaluation is at higher risk of label leakage from downstream chemistry success

## What Needs To Happen Before Other Cases Graduate

### IPF

- reconstruct sample contrasts and per-cohort case/control definitions
- separate clean IPF-vs-control cohorts from longitudinal, mixed-IIP, and mixed-ILD series

### HCC

- reconstruct sample contrasts and verify how `1133` disease and `674` healthy-control samples are distributed across the 10 cohorts
- decide whether the benchmark should use the paper's full heterogeneous pool or a curated HCC-only subset

### AD

- parse the supplementary datasets and map them to the Alzheimer's-specific portion of the analysis
