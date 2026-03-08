# PrioriTx Open Replacement Map

## Purpose

This document translates the verified PandaOmics score families into reproducible PrioriTx components. The point is not to clone their product. The point is to preserve the useful signal classes while replacing opaque or proprietary parts with auditable implementations.

## Replacement Strategy

- Keep the evidence family if it is scientifically useful.
- Replace proprietary implementation details with public-data equivalents.
- Make every feature accession-traceable.
- Avoid mixing popularity with causality in the final ranker.

## Score Family Mapping

| PandaOmics family | Verified baseline idea | PrioriTx replacement |
| --- | --- | --- |
| Network Neighbors | Two-hop PPI neighborhood perturbation | STRING or BioGRID graph neighborhood enrichment with source-weighted edge confidence |
| Mutated Sub-modules | Propagate genetic evidence through PPI graph | Fine-mapped genetics, Open Targets genetics, and graph diffusion over gene-gene edges |
| Disease Sub-Modules | Proximity to disease-relevant genes in graph | Disease module discovery with Open Targets, ClinVar, OMIM, and network propagation |
| Causal inference | TF-based causal evidence from expression | DoRothEA/CollecTRI plus perturbation-aware TF activity inference |
| Overexpression | Similarity to LINCS overexpression perturbations | LINCS transcriptomic matching with explicit cell-line compatibility filters |
| Knockouts | Similarity to LINCS knockout perturbations | LINCS knockout signature reversal plus CRISPR screen support where available |
| Mutations | GWAS and TWAS evidence | Open Targets genetics + GWAS Catalog + colocalization and TWAS where reproducible |
| Pathways | iPANDA pathway activation | Reactome-based pathway activity using fgsea, decoupleR, or VIPER-like scoring |
| Interactome Community | Graph diffusion over multi-signal perturbations | Unified graph propagation over transcriptomic, genetics, and known-target seeds |
| Relevance | Aggregate external disease evidence | Weighted external evidence score with source-specific calibration |
| Expression | Differential expression plus tissue expression | DE effect, meta significance, consistency, and disease-tissue relevance score |
| Heterogenous graph walk | HeroWalk on heterogeneous graph | Heterogeneous graph embeddings in PyG with reproducible edge schema |
| Matrix factorization | Latent gene-disease factorization | Explicit representation-learning benchmark, compared against graph embeddings |
| Attention Spike | Predict future target heat | Separate translational momentum score, excluded from causality score |
| Evidence | Combination of trend and attention | Research activity feature, used only as a secondary prioritization axis |
| Attention Score | Overall mention volume | Literature volume feature, never allowed to dominate final rank |
| Trend | Growth of mentions over 5 years | Time-aware publication and trial momentum with leakage controls |
| Funding per Publication | Grant productivity proxy | Optional ecosystem maturity feature, not part of biological relevance |
| Grant Funding | Total funding | Optional ecosystem signal only |
| Grant size | Mean grant size | Optional ecosystem signal only |
| Credibility adjusted attention index | Publication prestige signal | Optional KOL signal, displayed but downweighted in ranking |
| Mean Hirsch | Author h-index proxy | Optional KOL signal, not causal |
| Impact factor | Journal prestige proxy | Optional KOL signal, not causal |

## PrioriTx Scoring Architecture

PrioriTx should split final target prioritization into four explicitly separate axes:

### 1. Biological Causality

- disease differential signal
- pathway activity
- human genetics
- disease-module proximity
- perturbation consistency

### 2. Tractability

- target class
- chemistry support
- structure availability
- modality compatibility

### 3. Safety and Liability

- tissue breadth
- expression in protected tissues
- known safety liabilities
- essentiality risk

### 4. Strategic Context

- novelty
- literature momentum
- trial activity
- portfolio overlap

This prevents a "popular target" from outranking a biologically stronger but less fashionable target.

## What PrioriTx Should Add Beyond the Verified PandaOmics Baseline

### Public genetics rigor

- fine-mapping where available
- colocalization where possible
- source-level disease-variant-gene provenance

### Cell-type specificity

- single-cell signal aggregation
- cell-state-aware target relevance
- disease-relevant cell type weighting

### Safer novelty handling

- novelty shown as a tradeoff, not assumed to be good by default
- publication scarcity must not be mistaken for target quality

### Better validation

- independent external labels
- time-split evaluation
- ablation of popularity-derived features

## Recommendation

PrioriTx should beat PandaOmics with:

- stronger data lineage
- cleaner separation of biological and popularity features
- modern graph and perturbation evidence
- better evaluation hygiene

It should not try to win by increasing opacity.
