# PrioriTx Platform Spec

## Status

Pre-implementation spec. This document defines what must be locked before any serious build begins.

## Product Goal

PrioriTx must generate ranked therapeutic target hypotheses that are:

- scientifically grounded
- reproducible from public data
- explainable at the target and dataset level
- benchmarked against real translational outcomes

## Scope of v1

v1 is a benchmarkable target prioritization platform for a small set of high-value indications.

Recommended benchmark indications:

- idiopathic pulmonary fibrosis
- amyotrophic lateral sclerosis
- hepatocellular carcinoma
- Alzheimer's disease

Reason:

- all are highlighted in the PandaOmics literature or adjacent Insilico case studies
- they cover oncology and non-oncology settings
- they stress different data availability patterns

## Required Deliverables Before Coding

### 1. Indication Benchmark Pack

For each indication:

- ontology IDs
- exact accession manifest
- inclusion and exclusion criteria
- validation label sources
- expected known-positive targets
- a machine-readable benchmark pack in `configs/indications/` that passes `ruby scripts/validate_benchmark_packs.rb`

### 2. Data Contract Pack

Required contracts:

- `indication_manifest`
- `dataset_manifest`
- `sample_metadata`
- `study_contrast`
- `feature_vector`
- `target_rank_record`
- `explanation_record`

The first contract milestone should ship:

- schemas for `benchmark_pack`, `dataset_manifest`, `study_contrast`, and `target_rank_record`
- validated example records for IPF and HCC
- explicit template status for any non-scientific example output

### 3. Evaluation Protocol

Must define:

- rank metrics: NDCG, MAP, precision@k, recall@k
- enrichment metrics over known-positive targets
- time-split evaluation where possible
- ablations by evidence family
- calibration checks on top-ranked targets

Current source of truth:

- `docs/specs/benchmark-evaluation-protocol.md`

## Scientific Requirements

### Dataset Provenance

Every target ranking must be traceable to:

- the indication manifest version
- the source datasets used
- the sample groups used
- the derived study contrasts
- the feature derivation code version

### Identifier Standard

Primary gene key:

- Ensembl gene ID

Supporting IDs:

- HGNC symbol
- UniProt accession
- Entrez Gene ID

Disease keys:

- EFO preferred
- MeSH, DOID, ICD10, and Open Targets cross-mapped

### Evidence Families Required in v1

- transcriptomic differential signal
- pathway activity signal
- genetics signal
- network proximity signal
- text novelty and momentum
- tractability signal
- tissue liability or safety signal

## Ranking Spec

### Baseline Ranker

The baseline ranker must be transparent and reproducible.

Recommended approach:

- per-feature normalization
- disease-specific calibration
- weighted additive or gradient-boosted ranking model
- full feature attribution output

### Advanced Ranker

Only after the baseline is stable:

- pairwise or listwise learning-to-rank
- graph-embedding augmentation
- contextual bandit for investigation sequencing

RL is not a v1 prerequisite.

## Knowledge Graph Spec

### Minimal node types

- gene
- disease
- pathway
- drug
- publication cluster

### Minimal edge types

- interacts_with
- associated_with
- member_of
- targeted_by
- mentioned_in
- tested_in

### Requirements

- all edges must carry source provenance
- edge confidence must be explicit
- graph snapshots must be versioned

## API Spec

The first API should expose data products, not hidden model internals.

Required endpoints:

- `POST /indications/resolve`
- `GET /indications/{id}/manifest`
- `POST /runs`
- `GET /runs/{id}`
- `GET /runs/{id}/targets`
- `GET /targets/{ensembl_id}`
- `GET /targets/{ensembl_id}/evidence`
- `GET /targets/{ensembl_id}/explanation`

## UI Spec

The UI should support analyst workflows, not marketing demos.

Required screens:

- indication setup and manifest review
- dataset inclusion review
- ranked targets table
- target detail evidence view
- graph rationale view
- study provenance view
- evaluation dashboard

## Exit Criteria For Architecture Phase

We can move to implementation only when:

1. At least 3 benchmark indications have accession-level manifests.
2. The baseline evidence schema is finalized.
3. The evaluation protocol is written and accepted.
4. The repository layout is created.
5. The first set of public data connectors is prioritized.

## Initial Connector Priority

Build these first:

1. Open Targets
2. GEO
3. TCGA / GDC
4. GTEx
5. GWAS Catalog
6. STRING
7. Reactome
8. PubMed
9. ClinicalTrials.gov
10. ChEMBL

Reason:

- these recover the highest-value public signals with the lowest initial ambiguity.

## Key Risks

- literature popularity leakage into ranking
- disease-manifest ambiguity
- cross-platform normalization failure
- graph edges with mixed evidence quality
- hidden label leakage from post-hoc target success data

## Implementation Sequence Once Approved

1. Scaffold repo and contracts
2. Implement indication and dataset registry
3. Implement transcriptomics and genetics baseline features
4. Implement graph assembly and baseline ranking
5. Implement evaluation harness
6. Add explanation layer
7. Add advanced ranking and sequential policy
