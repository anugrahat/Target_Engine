# PrioriTx Project Instructions

## Project Scope

PrioriTx is a scientifically rigorous therapeutic target prioritization platform intended to outperform the public PandaOmics baseline on:

- reproducibility
- dataset provenance
- evidence calibration
- graph-aware ranking
- explanation quality
- evaluation rigor

This repository is in the specification phase. Do not jump into implementation without checking the docs in `docs/`.

Current benchmark indication candidates:

- idiopathic pulmonary fibrosis
- amyotrophic lateral sclerosis
- hepatocellular carcinoma
- Alzheimer's disease

Current repo state:

- greenfield
- no implementation yet
- design, research, and validation docs exist under `docs/`

## Current Source of Truth

Read these first:

- `docs/README.md`
- `docs/research/pandaomics-insilico-baseline.md`
- `docs/research/open-replacement-map.md`
- `docs/architecture/prioritx-system-architecture.md`
- `docs/architecture/repository-layout.md`
- `docs/specs/prioritx-platform-spec.md`

## Science and Accuracy Rules

- Scientific accuracy is the top priority.
- Prefer primary sources over summaries.
- Distinguish verified facts from inference and proposed design.
- Do not claim accession-level dataset coverage unless the accession list is explicitly verified.
- When describing PandaOmics or Insilico methods, separate public disclosures from proprietary or unknown details.
- Do not let novelty, publication volume, journal prestige, or other popularity signals masquerade as biological causality.
- When uncertain, say what is verified, what is inferred, and what remains unresolved.
- For every scientific case study, verify the disease, dataset, and claimed validation evidence before repeating it as fact.
- Treat paper supplements, methods, and official docs as higher priority than blog posts or secondary summaries.
- Record unresolved scientific ambiguity in the docs instead of silently assuming.

## Research Workflow

- For scientific or product claims, verify against papers, supplements, or official documentation.
- Maintain accession-level dataset manifests for each benchmark indication before implementation.
- Keep benchmark evaluation design explicit and versioned.
- If a case-study paper names a disease program but not exact accessions, mark the manifest as incomplete rather than filling gaps by guesswork.
- Preserve the distinction between:
  - verified PandaOmics baseline
  - PrioriTx proposed replacement
  - open research question

## Implementation Gate

Do not begin major implementation until:

- benchmark indications are locked
- indication manifests exist
- data contracts are defined
- evaluation protocol is defined

Do not implement RL-first architecture before a strong transparent baseline exists.

## Communication

- Think like a scientist reviewing a methods section.
- Surface accuracy risks early.
- Prefer precise statements over optimistic ones.
- When making recommendations, explain whether they are source-backed, inferred, or chosen as an engineering tradeoff.
