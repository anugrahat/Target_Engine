# Repository Layout

## Goal

The repository should reflect the scientific workflow, not just the deployment topology.

PrioriTx is best structured as a monorepo with clear separation between:

- science pipelines
- reusable domain logic
- API and serving
- frontend product
- configs and dataset manifests
- docs and evaluation artifacts

## Proposed Top-Level Structure

```text
Target_Engine/
  apps/
    api/
    web/
  packages/
    py/
      prioritx_core/
      prioritx_data/
      prioritx_features/
      prioritx_graph/
      prioritx_rank/
      prioritx_eval/
    ts/
      ui/
      client/
  pipelines/
    registry/
    ingestion/
    harmonization/
    analysis/
    meta_analysis/
    graph/
    ranking/
    evaluation/
  data_contracts/
    schemas/
    manifests/
    examples/
  configs/
    indications/
    datasets/
    environments/
    features/
    ranking/
  docs/
    research/
    architecture/
    specs/
  notebooks/
    exploratory/
    validation/
  infra/
    docker/
    db/
    cloud/
  tests/
    unit/
    integration/
    pipeline/
    fixtures/
  scripts/
  Makefile
  pyproject.toml
  pnpm-workspace.yaml
  README.md
```

## Directory Responsibilities

### `apps/api`

- FastAPI service
- read-only serving of ranked outputs, manifests, and explanations
- job status and evidence retrieval endpoints

### `apps/web`

- analyst-facing product UI
- indication setup
- ranked target views
- target evidence drilldowns
- graph and study provenance views

### `packages/py/prioritx_core`

- shared domain models
- ontology mappings
- gene, disease, and study identifiers

### `packages/py/prioritx_data`

- dataset clients
- parsers
- harmonization helpers
- sample metadata normalization

### `packages/py/prioritx_features`

- feature definitions
- per-dataset scoring
- meta-analysis feature aggregation

### `packages/py/prioritx_graph`

- graph assembly
- edge weighting
- subgraph extraction
- embedding jobs

### `packages/py/prioritx_rank`

- transparent baseline ranking
- learning-to-rank models
- optional sequential policy layer

### `packages/py/prioritx_eval`

- benchmark tasks
- time-split validation
- ranking metrics
- calibration and ablation reports

### `pipelines/*`

Each pipeline directory should only orchestrate a stage and call package code.

That means:

- business logic belongs in `packages/py`
- orchestration belongs in `pipelines`

### `data_contracts`

This is central.

PrioriTx should formalize:

- indication manifests
- dataset manifests
- sample schemas
- feature schemas
- ranking output schemas
- explanation payload schemas

### `configs/indications`

One config per indication family or benchmark task.

Example:

- `ipf.yaml`
- `als.yaml`
- `hcc.yaml`
- `ad.yaml`

Each config should point to a versioned accession manifest.

## Naming Rules

- use `prioritx_` for Python packages
- use lowercase snake_case for files
- use explicit stage names, not vague names like `utils`
- avoid mixing exploratory notebooks with production pipeline code

## Artifact Rules

Generated artifacts should not be committed by default.

Use:

- `artifacts/raw/`
- `artifacts/processed/`
- `artifacts/features/`
- `artifacts/models/`
- `artifacts/eval/`

and keep them out of git unless a small fixture is intentionally checked in.

## Why This Layout Wins

This structure makes it possible to:

- reproduce an indication from a manifest
- unit-test feature logic separately from data fetching
- benchmark rankers independently from the UI
- keep scientific code reviewable
- swap ranking models without changing the data model
