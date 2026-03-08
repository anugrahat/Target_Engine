# Idiopathic Pulmonary Fibrosis / TNIK Case Study Verification

## Primary source

- *A small-molecule TNIK inhibitor targets fibrosis in preclinical and clinical models*, Nature Biotechnology 2024.
- Open-access mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC11738990/

## What is explicitly verified

- TNIK was selected as an anti-fibrotic target through Insilico's AI-driven discovery pipeline.
- The resulting inhibitor `INS018_055` showed anti-fibrotic and anti-inflammatory activity in preclinical models.
- Human phase I studies were reported:
  - `NCT05154240`
  - `CTR20221542`
- The paper includes single-cell RNA-seq analysis using `GSE136831` from Adams et al. to localize TNIK expression patterns in IPF versus control lungs.
- The paper's `Data availability` section explicitly lists the 15 GEO cohorts used for IPF target-ID scoring.

## Exact datasets disclosed in the paper

### Explicitly disclosed

- `GSE93606`
- `GSE38958`
- `GSE28042`
- `GSE33566`
- `GSE101286`
- `GSE72073`
- `GSE150910`
- `GSE92592`
- `GSE52463`
- `GSE83717`
- `GSE21369`
- `GSE15197`
- `GSE99621`
- `GSE138283`
- `GSE24206`
- `GSE136831` for single-cell RNA-seq follow-up analysis

## Validation evidence

### Computational

- target discovery through the Insilico pipeline
- scRNA-seq analysis of TNIK expression by cell type
- pathway and network interpretation

### Experimental

- multiple in vitro and in vivo anti-fibrotic studies
- medicinal chemistry optimization to INS018_055
- human phase I safety and PK trials

This is an unusually strong target-to-molecule validation story, and the discovery cohort list is public.

## Benchmark readiness

### Readiness: High

Reason:

- target validation is excellent
- discovery GEO cohorts are explicitly listed in the paper
- validation spans computational ranking, preclinical work, and phase I studies

## Remaining gaps

- reconstruct the exact target-discovery contrasts for each listed cohort
- ensure IPF benchmark labels do not improperly use later clinical progress as if it were an unbiased discovery-time label

## PrioriTx implication

IPF is suitable for a first-pass accession manifest now. The remaining work is contrast reconstruction and defensible benchmark-label design.
