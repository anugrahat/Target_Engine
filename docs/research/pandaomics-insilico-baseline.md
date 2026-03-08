# PandaOmics / Insilico Baseline

## Purpose

This document captures what is **verified from public Insilico/PandaOmics sources** and what remains **undisclosed or proprietary**. It is the baseline PrioriTx aims to exceed.

## Verified From the 2024 PandaOmics Paper

Primary source:

- Kamya et al., *PandaOmics: An AI-Driven Platform for Therapeutic Target and Biomarker Discovery*, J. Chem. Inf. Model. 2024.

Verified claims from the paper body:

- PandaOmics supports target discovery from multimodal omics and biomedical text.
- It uses gene expression, proteomics, methylation, genetic data, and text data.
- It exposes 23 disease-specific target-identification models.
- It uses pathway and PPI graphs plus publication-derived knowledge graphs.
- It offers dataset exploration with PCA, t-SNE, and UMAP.
- It supports batch correction, quality control, and meta-analysis across disease-relevant comparisons.
- It includes indication prioritization across a large bank of precomputed meta-analyses.
- It integrates with AlphaFold, Chemistry42, and inClinico in Insilico's broader stack.

Verified from the public PandaOmics knowledge graph manual page:

- PandaOmics exposes a literature-backed knowledge graph linking genes, diseases, chemicals, and biological processes.
- Graph edges are backed by citations to original publications.
- The graph is surfaced on gene, disease, gene-disease, and meta-analysis views.

The paper also states:

- More than 8000 disease meta-analyses were precalculated.
- More than 500 of those were manually curated.
- Manual curation emphasized untreated disease samples, paired controls, disease-relevant tissues, and minimum sample thresholds.

## Exact Public Source Databases Verified From Supplementary Table 1

The following sources are explicitly listed in `ci3c01619_si_001.xlsx`, which is now stored in this repo.

### Disease vocabularies and ontology

- EFO
- DOID
- ICD10
- Open Targets
- MeSH

### Drug and target resources

- OpenTargets / targetvalidation
- ChEMBL
- DrugCentral
- Pharos
- TTD

### Gene identifier and annotation resources

- Entrez Gene
- OMIM
- HGNC
- UniProt
- Ensembl
- RefSeq
- RGD
- MGI

### Interaction and network resources

- STRING
- BioGRID
- ChEA3

### Omics repositories

- GEO for RNA-seq, microarray, and methylation
- ArrayExpress
- PRIDE
- PAXdb
- Human Protein Atlas
- TCGA for RNA-seq and methylation
- LINCS L1000
- GTEx
- Broad Institute Single Cell Portal
- DDBJ
- Single Cell Expression Atlas
- Human Cell Atlas
- Allen Brain Atlas
- ARCHS4
- Glioblastoma Atlas Project

### Genetics resources

- GWAS Catalog
- ClinVar
- IntOGen

### Pathway, structure, tissue, and text resources

- ENCODE
- Reactome
- Protein Data Bank
- AlphaFold
- Surfaceome
- ClinicalTrials.gov
- SJR
- PubMed
- NIH ExPORTER
- CORDIS
- NSF
- NHMRC
- USPTO
- BRENDA

## Exact Public Score Families Verified From Supplementary Table 2

The following 23 score types are explicitly listed in `ci3c01619_si_002.xlsx`.

### Omics scores

1. Network Neighbors
2. Mutated Sub-modules
3. Disease Sub-Modules
4. Causal inference
5. Overexpression
6. Knockouts
7. Mutations
8. Pathways
9. Interactome Community
10. Relevance
11. Expression
12. Heterogenous graph walk
13. Matrix factorization

### Text-based scores

14. Attention Spike
15. Evidence
16. Attention Score
17. Trend

### Financial scores

18. Funding per Publication
19. Grant Funding
20. Grant size

### KOL scores

21. Credibility adjusted attention index
22. Mean Hirsch
23. Impact factor

## Verified Technical Patterns From Supplementary Table 2

These are explicitly described in the supplement, not inferred:

- Two-hop PPI-neighborhood enrichment scoring
- Diffusion-based propagation over PPI graphs
- Transcription factor causal inference
- LINCS-based knockout and overexpression similarity scoring
- iPANDA pathway activation scoring
- Guided heterogeneous graph walk (`HeroWalk`) with SkipGram node representation learning
- Graph-regularized matrix factorization on gene-disease graphs
- Neural-network prediction of future attention spikes from publications, grants, trials, and patents

## What Appears Proprietary or Underspecified

The public paper does **not** fully disclose:

- Exact accession-level dataset manifests for each disease meta-analysis
- The exact manually curated disease-gene-target knowledge used internally
- The full data cleaning, filtering, and harmonization logic per source
- The internal disease taxonomy aligned to pharma pipeline divisions
- The full training data and labels behind some proprietary models
- ChatPandaGPT implementation details

This matters because "what databases they use" is public, but "which exact datasets they studied for each disease run" is often not fully enumerated in the overview paper.

## PrioriTx Implication

PrioriTx should not try to win by being more opaque. It should win by being:

- fully accession-traceable
- manifest-driven
- benchmarkable at the indication level
- modular enough to swap scoring models without rewriting the platform
- explicit about what is curated versus learned versus inferred

## Baseline We Should Reproduce Before Claiming Improvement

PrioriTx should reproduce an open, public-only baseline with:

- disease ontology normalization
- accession-level dataset manifests
- per-dataset QC and harmonization
- disease meta-analysis across transcriptomics
- pathway scoring
- graph-derived features
- genetics evidence
- text-derived novelty and momentum
- transparent ranking outputs with evidence attribution

Only after reproducing that baseline should we add RL-driven sequential prioritization and stronger causal validation logic.

## Research Gaps To Resolve Before Implementation

These are the highest-value unresolved items:

- Recover accession-level dataset manifests for high-profile case studies such as ALS, HCC, fibrosis, and AD where possible.
- Decide which proprietary PandaOmics score families can be replaced by reproducible open equivalents.
- Define a reproducible benchmark set of indications with public downstream validation labels.
- Define a gold-standard evaluation protocol that does not leak literature popularity into the ranker.

## Sources

- PandaOmics paper: https://pubs.acs.org/doi/10.1021/acs.jcim.3c01619
- Open-access mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC11134400/
- iPANDA paper: https://www.nature.com/articles/ncomms13427
- PandaOmics knowledge graph help page: https://pharma.ai/pandaomics/help/knowledge_graph
- Local supplement files:
  - `/Users/felarof99/Documents/Target_Engine/ci3c01619_si_001.xlsx`
  - `/Users/felarof99/Documents/Target_Engine/ci3c01619_si_002.xlsx`
