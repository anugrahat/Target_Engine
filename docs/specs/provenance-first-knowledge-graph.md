# Provenance-First Knowledge Graph

## Goal

Build a disease-slice knowledge graph that is useful for target prioritization without hiding evidence quality.

The graph should improve on opaque platform graphs by making every edge auditable.

## Current Scope

The first implementation is intentionally narrow:

- disease nodes
- gene nodes
- pathway nodes

Current edge families:

- `disease_gene_transcriptomics`
- `disease_gene_genetics`
- `disease_pathway_enrichment`
- `pathway_gene_membership`
- `shared_pathway_neighbor`

## Edge Rules

Each edge must carry:

- type
- weight
- evidence family
- discovery-time validity
- leakage risk
- provenance

This is the main differentiator.

The graph is not allowed to silently mix:

- discovery-time evidence
- retrospective paper rationale
- downstream validation
- medicinal chemistry success

## Transparent Graph Features

The first graph features are intentionally interpretable:

- neighborhood support
- path counts
- disease-pathway-gene connectivity
- propagation support

These are exposed separately from the base fused score.

## Ranking Rule

The first graph-augmented ranker is a transparent rerank over the core fused candidate pool:

- `0.75 * core_fused_score`
- `0.25 * knowledge_graph_support_score`

This weight is an engineering tradeoff, not a learned optimum.

## Runtime Strategy

Live Reactome membership lookups are too slow to support large benchmark slices.

The KG therefore uses a local membership cache built from:

- `scripts/build_reactome_membership_cache.py`
- `tmp/graph_cache/reactome_gene_memberships.json`

The cache is keyed by gene symbol and stores Reactome memberships so repeated benchmark runs stay local after the first warmup.

## Current Measured Result

The first cache-backed IPF exploratory benchmark run is informative:

- base fused rank for `TNIK`: `1176`
- graph-augmented rank for `TNIK`: `1208`

So the current provenance-first KG implementation is faster and scientifically auditable, but it does not yet improve `TNIK` recovery. That is the correct result to keep until stronger graph evidence is added.

## Why This Before GNNs

This phase should answer:

- does a real provenance-first KG help benchmark recovery?
- which graph signals help?
- does the graph improve `TNIK` or `CDK20` without leakage?

If this phase does not help, a GNN is unlikely to fix the underlying science.
