# Alzheimer's Disease / Phase-Separation Targets Case Study Verification

## Primary source

- *Targeting phase separation of disease proteins in human diseases with small molecules through an AI-powered drug discovery platform*, PNAS 2023.
- Open-access mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC10556643/

## What is explicitly verified

- The paper studies `64` diseases across `10` disease groups in a PPS-oriented disease landscape.
- For Alzheimer's disease, the paper highlights `CAMKK2`, `MARCKS`, and `SQSTM1/p62` as phase-separation-related targets.
- Experimental validation was performed in:
  - `SH-SY5Y` cells treated with `Aβ42`
  - `hiPSC`-derived neurons with the `APPSwe` mutation
- The paper explicitly states that:
  - the top `500` targets per disease are provided in `Dataset S1`
  - disease-associated pathways are provided in `Dataset S2`
  - PPS-modulated pathways are provided in `Dataset S3`

## Exact datasets disclosed in the paper

### Explicitly disclosed

- disease-level study design across 64 diseases
- existence of three structured supplemental datasets (`Dataset S1`, `Dataset S2`, `Dataset S3`)
- target names and validation models

### Not yet recovered

- the exact accession-level manifests appear to be in supplementary datasets (`Dataset S1`, `Dataset S2`, `Dataset S3`) exposed on the PMCID page
- those supplemental files were identified, but accession extraction remains unresolved in this pass

## Validation evidence

### Computational

- retrospective AI-driven prioritization across multiple disease data collections

### Experimental

- cell-model validation of candidate phase-separation target behavior under AD-like conditions

## Benchmark readiness

### Readiness: Medium

Reason:

- disease-specific targets and validation system are clear
- the paper exposes structured supplements, not just narrative claims
- accession-level discovery manifest is not yet recovered

## Remaining gaps

- extract the supplementary dataset files and identify which collections correspond specifically to the Alzheimer's disease component
- avoid overstating the paper as an AD-only target-discovery benchmark when it is broader in scope

## PrioriTx implication

This is useful as a validation-style AD benchmark candidate, but it is not yet accession-complete without supplement recovery.
