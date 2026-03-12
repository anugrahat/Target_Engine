# PrioriTx RL Benchmark Evaluation

## Purpose

This document defines the first PrioriTx RL-style evaluation harness and the current interpretation boundary.

The goal is narrow:

- build a non-leaky offline environment over current discovery-time evidence
- compare simple action policies against source-backed benchmark-positive targets
- determine whether the present evidence stack is already strong enough for an RL or contextual-bandit layer to add value

This harness is **not** a claim of prospective RL performance.

## Environment

The environment is built from:

- `fused_target_evidence(...)` candidate pools
- source-backed benchmark assertions in `data_contracts/assertions/*.json`
- benchmark policy modes: `strict` and `exploratory`

Each episode is a without-replacement target-selection sequence over one benchmark context.

Current reward:

- `1.0` if the selected gene is a source-backed positive target for that benchmark
- `0.0` otherwise

This reward intentionally excludes:

- downstream chemistry success
- later animal validation
- clinical progression
- retrospective paper discussion logic

## State

Each candidate exposes a compact feature vector derived from current fused evidence:

- fused score
- transcriptomics component
- genetics component
- tractability component
- pathway component
- network component
- transcriptomics support count
- evidence availability flags
- transcriptomics direction-conflict flag

## Agents

Current agents:

- `random`
- `fused_greedy`
  Uses the current PrioriTx fused score directly.
- `linear_ucb`
  Minimal contextual bandit over the evidence feature vector.

## Scientific Interpretation Rules

- If a positive target is not inside the candidate pool, RL cannot rescue it.
- If a positive target is inside the candidate pool but no agent finds it within a reasonable horizon, the current evidence stack is still too weak for RL to add practical value.
- Any apparent improvement on this tiny benchmark set must be treated as exploratory only.

## Bounded Replay Profile

For practical live evaluation, the current harness defaults to a bounded evidence profile:

- `genetics_size = 0`
- `tractability_top_n = 0`
- `pathway_top_n = 0`
- `network_top_n = 0`

Reason:

- full fused reranking across all orthogonal enrichment layers is still too slow for routine RL replay
- the bounded profile keeps the environment usable while preserving discovery-time validity

This should be treated as an RL evaluation over the **core current evidence state**, not the final production ranking stack.

## Current Live Findings

Verified on March 11, 2026 / March 12, 2026 UTC:

### Strict mode

With `candidate_limit = 250` and `horizon = 25`:

- `ipf_tnik`: benchmark positive not covered in candidate pool
- `hcc_cdk20`: benchmark positive not covered in candidate pool

Interpretation:

- under strict first-wave benchmark slices, the current evidence stack does not surface the source-backed positives high enough for RL replay to matter

### Exploratory IPF

With:

- `benchmark_id = ipf_tnik`
- `mode = exploratory`
- `candidate_limit = 2000`
- `horizon = 100`
- `episodes = 3`

Result:

- `TNIK` is covered in the candidate pool
- `random`: no hit
- `fused_greedy`: no hit
- `linear_ucb`: no hit

Interpretation:

- broader curated IPF evidence makes `TNIK` available to the environment, but still not salient enough for a simple bandit to recover within a practical search horizon

### Exploratory HCC

With:

- `benchmark_id = hcc_cdk20`
- `mode = exploratory`
- `candidate_limit = 12000`
- `horizon = 100`
- `episodes = 1`

Result:

- `CDK20` is covered in the candidate pool
- `random`: no hit
- `fused_greedy`: no hit
- `linear_ucb`: no hit

Interpretation:

- `CDK20` remains far too deep in the current discovery-time ordering for the present RL harness to help

## Conclusion

Current conclusion:

- PrioriTx now has a real RL evaluation harness
- the harness is scientifically honest
- the current evidence stack is **not yet strong enough** for RL to produce convincing benchmark recovery gains

That is a useful result.

It means the next scientific work should prioritize stronger evidence engineering and benchmark recovery before treating RL as a likely performance multiplier.
