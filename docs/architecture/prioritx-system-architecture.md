# PrioriTx System Architecture

## Objective

PrioriTx is an open, reproducible therapeutic target prioritization platform designed to outperform the public PandaOmics baseline on scientific rigor, dataset traceability, and decision quality.

It should beat the baseline by being better at:

- accession-level reproducibility
- evidence calibration
- graph-aware ranking
- causal and translational validation
- explanation quality
- evaluation discipline

## Design Principles

- Public-first: every baseline signal must be obtainable from public data.
- Manifest-driven: every indication run is backed by an explicit dataset manifest.
- Modular ranking: signals, graph features, and policies are separable components.
- Traceable outputs: every ranked target must carry machine-readable evidence provenance.
- No hidden curation: manual curation must be represented as versioned data artifacts.
- Benchmark before ambition: prove value against a transparent non-RL baseline first.

## System Layers

### 1. Research and Dataset Registry

Inputs:

- disease concept
- ontology mappings
- inclusion and exclusion criteria
- accession-level dataset manifests

Responsibilities:

- normalize indication terms across EFO, MeSH, DOID, ICD10, and Open Targets
- store exact dataset manifests for transcriptomics, proteomics, methylation, genetics, and text
- version dataset eligibility decisions

Outputs:

- `indication_manifest.yaml`
- `dataset_manifest.parquet`
- provenance logs

### 2. Data Ingestion and Harmonization

Responsibilities:

- fetch raw or processed source data
- harmonize identifiers to Ensembl as the primary gene key
- enforce tissue, disease-state, and sample-group metadata standards
- run QC, batch handling, and normalization

Canonical data products:

- `samples.parquet`
- `gene_expression_matrix.parquet`
- `methylation_matrix.parquet`
- `proteomics_matrix.parquet`
- `genetic_associations.parquet`
- `literature_features.parquet`

### 3. Per-Dataset Analysis

Responsibilities:

- differential expression or abundance analysis
- covariate-aware modeling where metadata allows it
- pathway activity estimation
- per-dataset evidence extraction

Preferred open methods:

- DESeq2 or limma-voom for bulk transcriptomics
- scanpy / scvi-tools for single-cell derived summaries
- fgsea, decoupleR, or iPANDA-like pathway scoring where reproducible
- robust z-score or empirical Bayes normalization across cohorts

### 4. Cross-Dataset Meta-analysis

Responsibilities:

- aggregate evidence across datasets for the same indication
- model study heterogeneity explicitly
- keep study-level effects available for audit

Outputs:

- meta effect size
- meta significance
- consistency metrics
- pathway consensus metrics
- tissue-specificity and off-target risk features

### 5. Knowledge Graph and Representation Layer

Graph node types:

- gene
- disease
- pathway
- drug
- publication cluster
- tissue or cell type

Graph edge types:

- gene-disease association
- gene-gene interaction
- gene-pathway membership
- drug-target interaction
- drug-disease trial relation
- gene-tissue expression
- publication evidence

Responsibilities:

- assemble a versioned heterogeneous graph
- preserve evidence-source weights on edges
- produce graph features for ranking
- support explanation subgraph extraction

Recommended implementation:

- NetworkX or graph-tool for early graph construction
- PyTorch Geometric for learned embeddings
- optional Neo4j only when interactive traversal is needed

### 6. Evidence Feature Store

This is the critical boundary between science code and ranking code.

Feature families:

- transcriptomic evidence
- pathway evidence
- genetics evidence
- network and graph evidence
- text and novelty evidence
- tractability and chemistry evidence
- safety and tissue liability evidence
- translational evidence

Each feature must record:

- feature name
- source data version
- derivation code version
- normalization method
- directionality
- confidence score

### 7. Ranking Layer

PrioriTx should have three ranking stages:

1. Transparent baseline ranker
   - calibrated weighted evidence model
2. Learning-to-rank model
   - gradient-boosted ranking or pairwise ranker on validated outcomes
3. Optional sequential policy layer
   - contextual bandit or RL only after baseline ranking is strong

Reason:

- RL should optimize investigation order or portfolio selection, not substitute for poor evidence engineering.

### 8. Explanation Layer

Outputs per target:

- top evidence contributions
- supporting datasets and accessions
- graph rationale
- risk flags
- novelty and tractability tradeoff

The explanation system should be deterministic first:

- feature attribution
- supporting studies
- graph paths

An LLM can then convert those artifacts into a narrative, but the source explanation graph must exist without the LLM.

## How PrioriTx Should Improve on the Public PandaOmics Baseline

### Improvement 1: Accession-Level Reproducibility

PandaOmics publicly discloses source databases but not all exact dataset manifests for each disease run. PrioriTx should require:

- exact accession lists
- sample inclusion logs
- normalization reports
- frozen manifests per experiment

### Improvement 2: Stronger Evaluation Discipline

PrioriTx should benchmark against:

- approved targets
- clinical progression events
- external CRISPR dependency evidence
- held-out disease areas
- time-sliced validation to avoid information leakage

### Improvement 3: Better Causal and Translational Signals

Add signals not clearly described in the PandaOmics supplement:

- colocalization and fine-mapped genetics where available
- perturb-seq or CRISPR screen integration
- cell-type specificity
- orthogonal safety liabilities
- target class feasibility

### Improvement 4: Cleaner Separation of Signals

Separate:

- biological relevance
- tractability
- novelty
- confidence
- portfolio fit

This prevents "hot target" popularity from masquerading as disease causality.

## Recommended Technology Choices

Backend:

- Python 3.11+
- FastAPI for APIs
- Pydantic for schemas
- Prefect or Dagster for pipelines

Data and analytics:

- DuckDB and Parquet for local analytical datasets
- Postgres for metadata and manifests
- optional object storage for raw artifacts

ML:

- scikit-learn / XGBoost for baseline ranking
- PyTorch Geometric for graph embeddings
- LightGBM or CatBoost for tabular ranking

Frontend:

- Next.js
- TypeScript
- visualization focused on evidence provenance, not just rank tables

## Hard Non-Goals for v1

- No opaque end-to-end foundation model ranker
- No RL-first architecture
- No hidden manual curation without versioned artifacts
- No single-score output without evidence decomposition

## Decision Gate Before Build

Implementation should not start until we have:

- a locked benchmark indication list
- an accession-manifest schema
- a baseline evidence schema
- a defined offline evaluation protocol
- a repository layout that matches the pipeline boundaries
