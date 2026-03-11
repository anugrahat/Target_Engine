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
- The dataset list is public, but the discovery pool is biologically heterogeneous and should not be treated as a clean HCC-only benchmark without curation.

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

## Recovered cohort details from GEO

- `GSE45267`
  - `48` primary HCC tissue samples
  - `39` non-cancerous tissue profiles from `61` patients
- `GSE60502`
  - `18` hepatocellular carcinoma samples
  - `18` adjacent non-tumorous liver tissue samples
  - paired design
- `GSE77314`
  - `50` paired normal and tumor samples
- `GSE36376`
  - `240` liver tumor samples
  - `193` adjacent non-tumor liver samples
  - adult HCC microarray cohort on `GPL10558`
- `GSE102079`
  - `152` HCC tumor samples
  - `14` adjacent liver samples from colorectal liver metastasis cases without chemotherapy
  - comparator is publicly disclosed but is not a clean adult-HCC adjacent or healthy liver control arm
- `GSE107170`
  - mixed liver-transplant cohort including HDV-HCC, HCV-HCC, HBV-HCC, and HDV cirrhosis without HCC
  - this is not a simple healthy-control comparison
- `E-MTAB-5905`
  - `62` multiregional RNA-seq samples
  - treatment-naive hepatocellular carcinoma patients at Mount Sinai
  - tumor and adjacent tissue were both sampled, but the public study record does not expose a simple per-arm count table in the retrieved metadata
- `GSE133039`
  - hepatoblastoma, not adult HCC
- `GSE104766`
  - hepatoblastoma, not adult HCC

## Validation evidence

### Computational

- PandaOmics target prioritization
- AlphaFold structure use
- Chemistry42 molecule generation

### Experimental

- synthesis of seven compounds
- biochemical and cellular validation around CDK20 inhibition

## Benchmark readiness

### Readiness: Medium

Reason:

- validation story is real and concrete
- discovery-data cohorts are explicitly listed in the paper
- however, the disclosed discovery pool is not a clean HCC-only case-control set
- at least two included cohorts are hepatoblastoma, and some controls are adjacent-normal rather than healthy liver

## Remaining gaps

- map the disease/control sample counts back to accession IDs
- separate true HCC cohorts from hepatoblastoma cohorts and other mixed liver-disease cohorts
- recover per-arm sample definitions for `E-MTAB-5905` and `TCGA-LIHC`
- separate target-ranking evidence from downstream structure-based chemistry steps
- decide whether PrioriTx should benchmark the public list as-is, or build curated strict and extended HCC-only subsets

## PrioriTx implication

HCC remains scientifically useful, but it should no longer be treated as a clean first-wave benchmark without explicit cohort curation. PrioriTx should either construct a curated HCC-only subset or downgrade this case below IPF for early benchmark work.

Current implementation note:

- `GSE60502` is now a real accession-backed PrioriTx transcriptomics path because the GEO series matrix is complete, the design is paired, and `GPL96.annot.gz` provides recoverable primary-source probe annotation
- `GSE45267` is now a second real accession-backed HCC transcriptomics path because the GEO series matrix is complete and `GPL570.annot.gz` provides recoverable primary-source probe annotation for an unpaired tumor-versus-noncancerous comparison
- `GSE36376` is now a third real accession-backed HCC microarray path for the extended subset because GEO exposes explicit tissue labels and the official `GPL10558` supplementary platform table contains recoverable `Probe_Id` to `Symbol` mappings
- `GSE36376` labels the target with the historical symbol `CCRK`; PrioriTx now maps that source-backed previous symbol to approved HGNC symbol `CDK20` with provenance preserved as `source_gene_symbols`
- even after the `CCRK` to `CDK20` identifier fix, `CDK20` remains weak in the extended HCC transcriptomics layer because the recovered effect size is small (`log2 fold change ~= 0.0945`), so it still fails the current support rule
