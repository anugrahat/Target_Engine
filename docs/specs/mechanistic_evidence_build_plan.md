# Mechanistic Evidence Build Plan

## Goal

Improve benchmark recovery for `TNIK` in IPF and `CDK20/CCRK` in HCC without lowering scientific standards.

The current system is strong on:

- bulk transcriptomics
- Open Targets genetics
- tractability
- generic pathway overlap
- STRING-style neighborhood support

The next system must add the evidence families that these benchmark targets actually depend on:

- cell-state evidence
- typed causal-mechanistic edges
- signaling-state and kinase-activity evidence
- disease-context stratification

## Recommended Design

### Option A: Mechanistic Evidence Layering

Build the next science phase as three new evidence modules on top of the current stack:

1. `cell_state_evidence`
2. `typed_causal_graph`
3. `signaling_activity_evidence`

This keeps the existing repo shape:

- `prioritx_data` for source loaders
- `prioritx_features` for transparent feature derivation
- `prioritx_graph` for typed graph assembly
- `prioritx_rank` for additive fusion
- `prioritx_eval` for benchmark ablations

This is the recommended design because it fits the current codebase and directly addresses the observed scientific gap.

### Option B: Full Multi-omics Expansion First

Broaden immediately into proteomics, phosphoproteomics, metabolomics, CRISPR screens, and disease-wide KG ingestion before tightening the benchmark logic.

This could ultimately be powerful, but it is not the best next step. It adds too many moving parts before we know which missing evidence family is actually decisive.

### Option C: Model-first Graph Learning

Add graph embeddings or GNNs now and let the model discover latent mechanistic structure.

This is not recommended yet. The graph is not rich enough, the labels are too sparse, and a learned model would make it harder to see whether the recovery gain is biologically legitimate.

## Why Option A Wins

- it attacks the actual benchmark miss, not a hypothetical one
- it stays interpretable
- it can be benchmarked with ablations
- it preserves discovery-time validity and leakage controls
- it reuses the current repository architecture instead of restarting

## Build Order

### Phase 1: Typed Mechanistic Graph

Add literature-backed typed edges that are currently missing from the KG.

Examples:

- `TNIK -> TEAD/YAP-TAZ`
- `TNIK -> SMAD`
- `TNIK -> myofibroblast differentiation`
- `AR -> CCRK`
- `CCRK -> GSK3B`
- `CCRK -> CTNNB1`
- `CCRK -> mTORC1`
- `CCRK -> IL6`
- `CCRK -> PMN-MDSC`

Implementation shape:

- `data_contracts/schemas/mechanistic_edge.schema.json`
- `data_contracts/curated/mechanistic_edges/*.json`
- `packages/py/prioritx_data/mechanistic_edges.py`
- `packages/py/prioritx_graph/service.py`

Rules:

- every edge must have source paper provenance
- every edge must have edge type and polarity where known
- every edge must have `discovery_time_valid` and `leakage_risk`
- validation-only or post-discovery edges stay excluded from ranking

Success criterion:

- graph ablation shows whether typed edges move `TNIK` or `CDK20` upward relative to the current generic KG

### Phase 2: IPF Cell-state Evidence

Add single-cell and, if recoverable, spatial evidence for IPF.

Primary target:

- `GSE136831`

Evidence products:

- cell-type-specific expression support
- myofibroblast-specific target support
- fibroblast activation / ECM program alignment
- optional GRN or virtual-knockout-derived perturbation support if the source inputs are recoverable without leakage

Implementation shape:

- `packages/py/prioritx_data/single_cell_ipf.py`
- `packages/py/prioritx_features/cell_state.py`
- `packages/py/prioritx_rank/baseline.py`
- `packages/py/prioritx_eval/service.py`

Scoring principle:

- do not average the signal back into bulk
- keep cell-state evidence as a separate component
- reward pathogenic-cell enrichment more than global abundance

Success criterion:

- `TNIK` gains measurable support specifically from pathogenic IPF cell states

### Phase 3: HCC Signaling-state Evidence

Add HCC kinase and signaling-context evidence rather than more bulk cohorts only.

Primary evidence types:

- phosphoproteomics if public data are cleanly recoverable
- kinase activity inference from transcriptomics where phosphoproteomics are absent
- subtype / etiology context flags:
  - HBV-associated
  - NASH/obesity-associated
  - male/AR-linked
  - immune-suppressive microenvironment

Implementation shape:

- `packages/py/prioritx_data/hcc_signaling.py`
- `packages/py/prioritx_features/signaling_activity.py`
- `packages/py/prioritx_rank/baseline.py`
- `packages/py/prioritx_eval/service.py`

Scoring principle:

- treat signaling-state evidence as orthogonal to bulk RNA
- prefer pathway or kinase-activity support over raw abundance for `CDK20`

Success criterion:

- `CDK20/CCRK` gets support from pathway-activity or kinase-circuit evidence even when bulk differential expression remains weak

## Fusion Strategy

Do not replace the existing fused score. Extend it.

New additive components:

- `cell_state_component`
- `mechanistic_graph_component`
- `signaling_activity_component`

Rules:

- all components remain explicit
- each new family gets a benchmark ablation
- no component gets tuned just to rescue the positive target in one disease

## Evaluation Strategy

For each phase, run:

1. base fused benchmark
2. base plus new evidence family
3. base plus all mechanistic families added so far

Required outputs:

- rank shift for `TNIK`
- rank shift for `CDK20`
- hit@k and MRR
- evidence-family attribution on the moved target
- leakage review

## What Not To Do Yet

- no GNN-first rewrite
- no threshold loosening designed around the benchmark positives
- no broad multi-omics ingestion without disease-fit review
- no literature-count fusion into the main score

## Immediate Next Task

Build `Phase 1: Typed Mechanistic Graph` first.

Reason:

- lowest implementation risk
- highest reuse of current infrastructure
- directly tests whether the current graph is too generic
- creates the scaffold needed for both IPF cell-state and HCC signaling edges later

## First Measured Outcome

The first typed-mechanistic benchmark result is encouraging for IPF:

- `TNIK` base fused rank in `ipf_lung_extended` exploratory mode: `1176`
- `TNIK` graph-augmented rank after adding typed mechanistic edges: `308`

That is the first real indication that the benchmark miss was partly due to graph specificity rather than only missing bulk omics.

The bounded HCC result is more mixed:

- `CDK20` base fused rank in `hcc_adult_extended` exploratory mode: `11069`
- `CDK20` bounded graph rank with a `500`-candidate slice plus mechanistic seeding: `501`

Interpretation:

- mechanistic seeding is enough to admit `CDK20` into a practical graph slice
- but the current HCC mechanistic evidence is not yet strong enough to make `CDK20` a true top candidate

That means the mechanistic graph fixed one real problem:

- `CDK20` is no longer excluded purely because it sits too deep in the bulk-ranked universe

But it did not solve the full HCC benchmark yet. The next HCC-specific science layer still needs to be signaling-state evidence, not just typed literature edges.

## First HCC Signaling-state Result

The first transcriptomics-derived HCC signaling-state layer is now implemented and benchmarked.

What it found in `hcc_adult_extended` exploratory mode:

- `IL-6 / PMN-MDSC` program activity is present but weak
- `beta-catenin` program activity is effectively absent in the current public HCC slice
- `CDK20` gets non-zero signaling support, but the bounded graph rank remains `501` in a `500`-candidate slice with mechanistic seeding

Interpretation:

- the signaling family is behaving correctly and transparently
- but the current HCC cohorts do not show strong enough CDK20-linked program activation to rescue the benchmark

This is still useful because it narrows the scientific gap further:

- the remaining HCC miss is not just missing graph specificity
- it is now more likely a cohort-context problem, a missing phosphoproteomic/kinase-activity layer, or both

## First IPF Cell-state Result

The first single-cell-derived IPF cell-state layer is now implemented and benchmarked.

What it found in `ipf_lung_extended` exploratory mode:

- `myofibroblast` program activity is strong
- `club cell` program activity is also strong
- `cytotoxic T-cell` program activity is absent in the current bulk-cohort proxy
- `TNIK` gets strong cell-state support from these active programs

Measured effect:

- previous graph-augmented `TNIK` rank after typed mechanistic edges: `308`
- current graph-augmented `TNIK` rank after adding cell-state evidence: `257`

Interpretation:

- this is the second independent sign that the TNIK benchmark miss was caused by insufficient mechanistic specificity rather than a simple lack of public signal
- IPF is now behaving the way the paper suggests: TNIK improves when fibrosis-relevant cell-state biology is represented explicitly
