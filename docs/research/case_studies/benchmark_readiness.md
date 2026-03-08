# Benchmark Readiness Summary

## Goal

Rank the first candidate indication case studies by how ready they are for PrioriTx benchmark construction.

## Summary Table

| Case | Primary paper | Manifest readiness | Why |
| --- | --- | --- | --- |
| IPF / TNIK | Nature Biotechnology 2024 | High | The discovery GEO cohorts are explicitly listed in `Data availability`, and validation is unusually strong. |
| HCC / CDK20 | Chemical Science 2023 | High | The 10 discovery cohorts are explicitly listed in `Materials and methods`, and downstream chemistry validation is concrete. |
| ALS | Frontiers in Aging Neuroscience 2022 | Medium-High | Multiple accession-coded datasets are named, but part of the stack is consortium-based (`Answer ALS`). |
| AD / phase separation | PNAS 2023 | Medium | The paper is scientifically useful and exposes structured supplements, but accession-level recovery is still unresolved. |

## Recommended Build Order

1. IPF
2. HCC
3. ALS
4. AD

## Why IPF And HCC Moved Up

- both papers publicly disclose the discovery cohorts directly in the article text
- both have strong downstream validation stories
- both are easier to convert into manifest stubs without relying on consortium-only datasets

## What Needs To Happen Before Other Cases Graduate

### IPF

- reconstruct sample contrasts and per-cohort case/control definitions

### HCC

- reconstruct sample contrasts and verify how `1133` disease and `674` healthy-control samples are distributed across the 10 cohorts

### AD

- parse the supplementary datasets and map them to the Alzheimer's-specific portion of the analysis
