# Hepatocellular Carcinoma / CDK20 Case Study Verification

## Primary source

- Ren et al., *AlphaFold Accelerates Artificial Intelligence Powered Drug Discovery: Efficient Discovery of a Novel CDK20 Small Molecule Inhibitor*, Chemical Science 2023.
- Open-access mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC9906638/

## What is explicitly verified

- PandaOmics was used to prioritize `CDK20` for hepatocellular carcinoma.
- The paper states in `Materials and methods` that the selected analysis combined:
  - `10` datasets
  - `1133` disease samples
  - `674` healthy controls
- The target-selection setting followed a first-in-class scenario emphasizing novelty and small-molecule druggability.
- AlphaFold-predicted structure plus Chemistry42 were used to generate compounds.
- Seven compounds were synthesized and tested experimentally.

## Exact datasets disclosed in the paper

### Explicitly disclosed

- `GSE36376`
- `GSE107170`
- `GSE102079`
- `GSE45267`
- `GSE133039`
- `GSE104766`
- `GSE77314`
- `GSE60502`
- `E-MTAB-5905`
- `TCGA-LIHC`
- aggregate counts of `1133` disease and `674` healthy-control samples

## Validation evidence

### Computational

- PandaOmics target prioritization
- AlphaFold structure use
- Chemistry42 molecule generation

### Experimental

- synthesis of seven compounds
- biochemical and cellular validation around CDK20 inhibition

## Benchmark readiness

### Readiness: High

Reason:

- validation story is real and concrete
- discovery-data cohorts are explicitly listed in the paper

## Remaining gaps

- map the disease/control sample counts back to accession IDs
- separate target-ranking evidence from downstream structure-based chemistry steps

## PrioriTx implication

HCC is suitable for a first-pass accession manifest now. The remaining work is contrast reconstruction and benchmark-label design.
