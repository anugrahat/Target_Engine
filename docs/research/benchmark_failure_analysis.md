# Why TNIK and CDK20 Are Still Missed

## Short answer

The current PrioriTx stack is missing the kinds of evidence that made these two targets attractive in the first place.

- `TNIK` in IPF looks more like a cell-state and causal-network target than a bulk-expression or human-genetics target.
- `CDK20/CCRK` in HCC looks more like a context-specific kinase-program target than a pan-HCC differential-expression or GWAS target.

That means our current stack is scientifically honest, but structurally biased toward targets like `MUC5B` that have strong bulk and genetics signal.

## What the primary papers actually show

### TNIK in IPF

The TNIK fibrosis paper does not present TNIK as a simple bulk RNA hit. It says TNIK ranked highly because of multiple PandaOmics score families, including graph and causal signals:

- the paper reports TNIK was `number 1` in the kinase approach with high `network neighbors`, `causal inference`, `pathways`, `interactome community`, `expression`, `heterogeneous graph walk`, and `matrix factorization` scores
- the transparency section says TNIK is connected to fibrosis biology through `focal adhesion`, `myofibroblast differentiation`, and `mesenchymal cell migration`
- the same section says TNIK is causally connected to IPF-associated genes including `TGFB1`, `FGR`, `FLT1`, and `KDR`

Source:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC11738990/

The same paper then adds evidence we do not currently use:

- single-cell RNA-seq from `GSE136831`
- cell-type-specific TNIK elevation in `myofibroblasts`, `cytotoxic T cells`, and `club cells`
- a virtual knockout analysis (`scTenifoldKnk`) in IPF myofibroblasts showing TNIK-linked perturbation of `Hippo` and `YAP/TAZ` signaling

This matters because TNIK is being supported as a regulator of fibrotic cell programs, not mainly as a top bulk differential-expression gene.

### CDK20/CCRK in HCC

The HCC literature around CDK20 is also not a “top bulk HCC RNA” story.

The foundational CCRK paper shows:

- `AR` directly induces `CCRK`
- CCRK activates `GSK3β` and `β-catenin/TCF`
- CCRK drives `G1/S` progression and tumor growth
- the mechanism is especially tied to male hepatocarcinogenesis and androgen signaling

Source:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC3148736/

Later HCC papers push the same target into even more context-specific biology:

- obesity/NASH-associated HCC: `AR` and inflammatory signaling cooperate through CCRK to activate `mTORC1`
- immune microenvironment: CCRK promotes `IL-6` and `MDSC`-linked immunosuppression
- metastasis-related liver microenvironment: CCRK acts as a signaling hub linking `NF-kB`, `STAT3`, `β-catenin`, and `mTOR`

Sources:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC6283830/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8115036/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6347020/

This means CDK20 is a subtype-, etiology-, and signaling-context target. It is not expected to dominate broad heterogeneous HCC expression cohorts.

## Why our current stack misses them

### 1. We are over-weighting bulk differential signal

This is appropriate for many targets, but both benchmark targets are closer to regulatory nodes than to dominant marker genes.

- `MUC5B` in IPF has strong human-genetics support and strong disease expression support
- `TNIK` appears to rely more on graph, pathway, and cell-state logic
- `CDK20` appears to rely more on kinase-circuit and etiology-specific logic

### 2. We are under-using cell-type resolution

For TNIK, the paper itself leans on single-cell evidence and virtual knockout in IPF myofibroblasts. Our current benchmark ranker mostly aggregates bulk public contrasts.

Consequence:

- a target can be biologically central in the pathogenic niche
- but still look weak in bulk disease-vs-control averages

### 3. We are under-using kinase activity and signaling-state evidence

For CDK20, the literature is about pathway activation and signaling circuitry:

- `AR -> CCRK -> GSK3β -> β-catenin`
- `CCRK -> EZH2/NF-kB`
- `CCRK -> IL-6/MDSC`
- `CCRK -> mTORC1`

Bulk transcript abundance is a poor readout for that kind of biology. Kinase targets are often better recovered by:

- phosphoproteomics
- inferred kinase activity
- upstream regulator inference
- perturbation sensitivity

### 4. The HCC cohorts are biologically heterogeneous

The CDK20 literature is especially strong in:

- male-predominant disease
- HBV-associated disease
- obesity/NASH-associated disease
- immune-suppressive tumor microenvironment settings

Our current HCC benchmark slices are scientifically cleaner than the original paper pool, but still broad relative to the specific biology emphasized by the CCRK literature.

### 5. Our graph is still too generic

The current KG mostly uses:

- disease-gene transcriptomics
- disease-gene genetics
- disease-pathway enrichment
- pathway-gene membership
- shared-pathway neighbors

That is useful, but it is not yet the kind of typed causal graph implied by the papers.

For these two targets, the useful graph would carry edges like:

- `TNIK -> TCF/LEF`
- `TNIK -> SMAD`
- `TNIK -> TEAD/YAP-TAZ`
- `TNIK -> myofibroblast state`
- `AR -> CCRK`
- `CCRK -> GSK3β`
- `CCRK -> β-catenin`
- `CCRK -> IL-6`
- `CCRK -> PMN-MDSC`
- `CCRK -> mTORC1`

Generic pathway overlap is too weak a substitute.

## How other groups approach targets like this

### Network diffusion and propagation

Network propagation can rescue biologically real targets that are weak in direct genetic ranking, but only when strong neighbors exist in the input evidence.

Example:

- a benchmarking paper showed targets like `APP` and `TNF` moved substantially upward only after diffusion on STRING-based networks

Source:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC10363916/

Implication for PrioriTx:

- diffusion is useful
- but it will not rescue TNIK or CDK20 if the seed evidence itself is too weak or the graph edges are too generic

### Single-cell and spatial target prioritization

Recent IPF work increasingly uses:

- single-cell RNA-seq
- spatial transcriptomics
- fibroblast niche analysis
- cell-state-specific perturbation logic

Example:

- a recent IPF study identified `PAK` as a target by integrating spatial and single-cell data around fibroblastic foci and dense fibrosis

Source:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12501429/

Implication:

- for fibrosis, bulk meta-analysis alone is likely insufficient for kinase prioritization

### Phosphoproteomics and kinome reprogramming

For HCC, several groups use:

- phosphoproteomics
- kinase activity inference
- signaling-network reconstruction

Sources:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC5986249/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7779902/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11780156/

Implication:

- kinase targets like CDK20 are more likely to emerge from signaling-state methods than from bulk RNA alone

### Public proteogenomic readout is still weak for CDK20

The first public HCC proteo-phospho layer in PrioriTx now confirms that this is not just a missing-loader problem.

In the public HCC proteogenomic archive:

- weak activity is present for the curated `IL-6 / STAT3` and `beta-catenin` programs
- the current support is driven mostly by single protein markers like `RELA` or `AXIN2`
- the curated activating phosphosites do not currently pass the direction-aware support rule
- after fixing a graph-base inconsistency, `CDK20` re-enters the bounded graph slice but still only at rank `501`

Implication:

- a proteomics layer is necessary, but marker-level bulk proteomics is still not enough to rescue `CDK20`
- the remaining likely gap is subtype-aware kinase-activity or causal phospho-network inference, not just another abundance matrix

### Functional and perturbation screens

In HCC and other diseases, target discovery often uses:

- CRISPR screens
- perturbation sensitivity models
- synthetic lethality or resistance screens

Examples:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC6662966/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9237198/

Implication:

- if a target is functionally required but not strongly differentially expressed, expression-first ranking will miss it

## Best interpretation of the current benchmark failure

The current PrioriTx miss is probably not one single bug.

It is mostly this:

- `TNIK` and `CDK20` were selected in the literature using richer mechanistic evidence than the current public benchmark harness captures
- our current stack favors high-expression, high-genetics, broad-cohort targets
- these two targets are more dependent on `cell state`, `causal circuitry`, `signaling activity`, and `context-specific network logic`

## What is most likely to help next

### Highest-value additions

1. `Single-cell / spatial IPF evidence`

- use `GSE136831` directly
- add cell-type-specific support for myofibroblasts, club cells, and cytotoxic T cells
- treat virtual knockout or GRN perturbation as a separate evidence family

2. `Typed causal graph edges`

- add mechanistic edges from the literature instead of generic pathway overlap only
- score typed paths differently from broad Reactome membership

3. `Kinase-activity evidence for HCC`

- phosphoproteomics where public data are available
- upstream kinase inference
- pathway-activity rather than only transcript abundance

4. `Etiology-stratified HCC analysis`

- separate HBV-associated, NASH-associated, and broader HCC contexts where possible
- avoid assuming one averaged HCC signal should recover a context-driven kinase

5. `Functional screen evidence`

- use CRISPR/dependency/perturbation evidence only when the disease context is appropriate and provenance is explicit

### Lower-value additions right now

- more generic GNN complexity
- more generic pathway overlap
- looser thresholds designed only to rescue benchmark targets

## Bottom line

The benchmark failure is scientifically informative.

It suggests the next improvement should not be “more of the same ranking with more compute.”

It should be:

- `cell-state evidence for TNIK`
- `signaling-state evidence for CDK20`
- `typed causal graph edges for both`

That is the most plausible path to improving recovery without making the science sloppier.
