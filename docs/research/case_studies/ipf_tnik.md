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

## Recovered cohort details from GEO

- `GSE24206`
  - `17` IPF lung samples from `11` patients
  - `6` control specimens from healthy donor lungs obtained at transplantation
  - Important caveat: the IPF arm includes repeated upper/lower lobe samples rather than one sample per patient
- `GSE52463`
  - `8` IPF lung samples
  - `7` healthy control lung samples
- `GSE72073`
  - `5` IPF lung samples
  - `3` normal-control lung samples from patients with primary spontaneous pneumothorax
- `GSE136831`
  - `32` IPF samples
  - `28` control samples
  - used for scRNA-seq follow-up rather than bulk discovery ranking

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
- several cohort-level sample definitions can already be recovered from GEO without relying on the supplement
- validation spans computational ranking, preclinical work, and phase I studies

## Remaining gaps

- reconstruct the exact target-discovery contrasts for every listed cohort
- recover the remaining per-cohort sample counts for the unresolved blood and lung GEO series
- ensure IPF benchmark labels do not improperly use later clinical progress as if it were an unbiased discovery-time label

## PrioriTx implication

IPF is suitable for a first-pass accession manifest now. The remaining work is contrast reconstruction and defensible benchmark-label design.
