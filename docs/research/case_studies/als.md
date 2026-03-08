# ALS Case Study Verification

## Primary source

- Pun et al., *Identification of Therapeutic Targets for Amyotrophic Lateral Sclerosis Using PandaOmics*, Frontiers in Aging Neuroscience 2022.
- Open-access: https://pmc.ncbi.nlm.nih.gov/articles/PMC9273868/

## What is explicitly verified

- This is one of the strongest publicly reproducible benchmark cases among the first four indications.
- PandaOmics was applied to ALS target discovery using both postmortem CNS and induced motor neuron datasets.
- The paper reports 17 high-confidence targets and 11 novel targets, for 28 total candidates.
- Experimental validation was done in a Drosophila model of C9ORF72-mediated ALS.
- Eight previously unreported genes were reported to rescue neurodegeneration in that model:
  - `KCNB2`
  - `KCNS3`
  - `ADRA2B`
  - `NR3C1`
  - `P2RY14`
  - `PPP3CB`
  - `PTPRC`
  - `RARA`

## Exact datasets disclosed in the paper

The paper explicitly names these ALS datasets or data resources:

### CNS transcriptomic comparisons explicitly disclosed in Table 1

- `E-MTAB-1925`
- `A-MEXP-2246`
- `GSE67196`
- `GSE68605`
- `GSE20589`
- `GSE122649`
- `GSE124439`
- `GSE19332`
- `GSE76220`

### Induced motor neuron data explicitly disclosed

- `Answer ALS` transcriptomic data
- `Answer ALS` proteomic data

Note:

- In the verified paper text, `Answer ALS` is explicitly named as a data source but is not represented as a GEO accession in the same table.

## Validation evidence

### Computational

- ranked therapeutic targets from PandaOmics
- pathway dysregulation analysis using iPANDA

### Experimental

- Drosophila c9ALS rescue experiments on prioritized genes

This is stronger than papers that stop at ranking plus narrative interpretation.

## Benchmark readiness

### Readiness: Medium-High

Reason:

- multiple explicit accession-coded datasets are named in the paper
- validation model is clear
- discovered targets and experimental readout are concrete
- part of the data stack is consortium-based rather than fully accession-coded

## Remaining gaps

- exact inclusion and exclusion logic across those accessions still needs to be reconstructed from methods and any supplementary material
- sample grouping and covariate handling should be extracted before building the final manifest
- validation labels should be encoded carefully so Drosophila rescue is not over-generalized to human translational success

## PrioriTx implication

ALS is a strong benchmark candidate, but it no longer looks uniquely cleaner than IPF or HCC after the latest verification pass.
