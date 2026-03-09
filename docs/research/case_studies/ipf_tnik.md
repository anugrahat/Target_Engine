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

- `GSE93606`
  - `60` IPF subjects and `20` matched controls at baseline
  - additional IPF longitudinal follow-up samples were also collected
  - useful for blood-based discovery, but not a simple one-time case-control set
- `GSE38958`
  - `70` IPF patients
  - `45` healthy controls
- `GSE28042`
  - `75` IPF patients in a replication cohort
  - no clean control arm disclosed in the GEO design text
- `GSE33566`
  - `93` IPF patients
  - `30` healthy controls
- `GSE101286`
  - `12` Japanese patients with chronic fibrosing idiopathic interstitial pneumonia
  - accession text does not expose a clean IPF-only versus healthy-control split
- `GSE150910`
  - `103` IPF lung samples
  - `103` unaffected control lungs
  - the full study also includes chronic hypersensitivity pneumonitis, so the benchmark must subset the IPF arm explicitly
- `GSE92592`
  - `20` IPF lung samples
  - `19` control lung samples
- `GSE24206`
  - `17` IPF lung samples from `11` patients
  - `6` control specimens from healthy donor lungs obtained at transplantation
  - Important caveat: the IPF arm includes repeated upper/lower lobe samples rather than one sample per patient
- `GSE52463`
  - `8` IPF lung samples
  - `7` healthy control lung samples
  - the accession-resolved `*.genes.txt.gz` sample supplements are cleaner than the aggregate `GSE52463_genes.txt.gz` file, whose column labels do not perfectly match the 15-sample GEO series record
- `GSE72073`
  - `5` IPF lung samples
  - `3` normal-control lung samples from patients with primary spontaneous pneumothorax
- `GSE83717`
  - GEO summary reports `7` IPF and `5` control FFPE lung tissues
  - GEO overall-design text reports `6` IPF and `5` control FFPE lung tissues
  - this count discrepancy should remain explicit until the sample table is checked directly
- `GSE21369`
  - `11` UIP/IPF lung samples within a broader interstitial lung disease cohort
  - `6` controls from uninvolved lung tissue or transplant tissue
  - not a clean IPF-only cohort
- `GSE15197`
  - `8` IPF subjects with secondary pulmonary hypertension
  - `13` normal controls
  - the series also includes `18` PAH subjects, so this requires explicit subsetting
- `GSE99621`
  - `26` total lung tissue RNA-seq samples from IPF affected areas, IPF unaffected areas, and healthy controls
  - accession text does not expose the split counts by subgroup
- `GSE138283`
  - `28` IPF lung biopsy samples
  - `20` age-matched controls
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
- many cohort-level sample definitions can already be recovered from GEO without relying on the supplement
- validation spans computational ranking, preclinical work, and phase I studies

## Remaining gaps

- reconstruct the exact target-discovery contrasts for every listed cohort
- recover the remaining per-cohort sample counts for the unresolved blood and lung GEO series
- distinguish the clean IPF-vs-control cohorts from the mixed or longitudinal series before benchmark scoring
- ensure IPF benchmark labels do not improperly use later clinical progress as if it were an unbiased discovery-time label

## PrioriTx implication

IPF is suitable for a first-pass accession manifest now. The remaining work is contrast reconstruction and defensible benchmark-label design.
