# ALS Case Study Verification

## Primary source

- Pun et al., *Identification of Therapeutic Targets for Amyotrophic Lateral Sclerosis Using PandaOmics*, Frontiers in Aging Neuroscience 2022.
- Open-access: https://pmc.ncbi.nlm.nih.gov/articles/PMC9273868/

## What is explicitly verified

- This is one of the strongest publicly reproducible benchmark cases among the first four indications.
- PandaOmics was applied to ALS target discovery using both postmortem CNS and induced motor neuron datasets.
- The paper reports 17 high-confidence targets and 11 novel targets, for 28 total candidates.
- Experimental validation was done in a Drosophila model of C9ORF72-mediated ALS.
- Eight previously unreported genes were reported to rescue neurodegeneration in that model:
  - `KCNB2`
  - `KCNS3`
  - `ADRA2B`
  - `NR3C1`
  - `P2RY14`
  - `PPP3CB`
  - `PTPRC`
  - `RARA`

## Exact datasets disclosed in the paper

The paper explicitly names these ALS datasets or data resources:

### CNS transcriptomic comparisons explicitly disclosed in Table 1

- `E-MTAB-1925`
- `A-MEXP-2246`
- `GSE67196`
- `GSE68605`
- `GSE20589`
- `GSE122649`
- `GSE124439`
- `GSE19332`
- `GSE76220`

### Induced motor neuron data explicitly disclosed

- `Answer ALS` transcriptomic data
- `Answer ALS` proteomic data

Note:

- In the verified paper text, `Answer ALS` is explicitly named as a data source but is not represented as a GEO accession in the same table.
- Table 1 also reports explicit diMN sample counts for `Answer ALS`: `25` familial ALS versus `31` controls and `110` sporadic ALS versus `31` controls for both transcriptomic and proteomic analyses.
- `GSE67196` and `GSE124439` are useful but bundle multiple tissue-specific comparisons under one accession in the paper-level table.
- PrioriTx has now split `GSE67196` into four accession-backed exploratory contrasts using the public rawcount matrix and series metadata:
  - `GSE67196_c9_fcx`
  - `GSE67196_c9_cereb`
  - `GSE67196_sals_fcx`
  - `GSE67196_sals_cereb`
- PrioriTx has now also split `GSE124439` into the two paper-disclosed sporadic ALS contrasts using the public per-sample RNA-seq count tarball and series metadata:
  - `GSE124439_fcx`
  - `GSE124439_motor`
- GEO accession metadata indicates `GSE19332` is CHMP2B-related ALS rather than sporadic ALS, so PrioriTx should encode it as a familial/mechanistic ALS cohort instead of a generic sALS cohort.

## Validation evidence

### Computational

- ranked therapeutic targets from PandaOmics
- pathway dysregulation analysis using iPANDA

### Experimental

- Drosophila c9ALS rescue experiments on prioritized genes

This is stronger than papers that stop at ranking plus narrative interpretation.

## Benchmark readiness

### Readiness: Medium-High

Reason:

- multiple explicit accession-coded datasets are named in the paper
- validation model is clear
- discovered targets and experimental readout are concrete
- part of the data stack is consortium-based rather than fully accession-coded

## Remaining gaps

- exact inclusion and exclusion logic across those accessions still needs to be reconstructed from methods and any supplementary material
- sample grouping and covariate handling should be extracted before building the final manifest
- validation labels should be encoded carefully so Drosophila rescue is not over-generalized to human translational success
- the public `GSE76220` RPKM supplement appears to expose `12` ALS columns against the paper-level `13`-case comparison, so the missing sample alignment should be documented before treating that cohort as fully resolved
- `Answer ALS` is now clearly distributed through the official portal with structured omics data levels and participant-linked iPSC-derived motor-neuron assays, but the public stable file identifiers used in the PandaOmics paper are still not accession-coded in a way PrioriTx can ingest directly yet

## PrioriTx implication

ALS is a strong benchmark candidate and is now suitable for first-wave benchmark scaffolding in two layers:

- `als_cns_core`
  - conservative accession-coded CNS-only subset
- `als_cns_dimn_extended`
  - exploratory extension that admits `Answer ALS` induced motor-neuron resources with explicit provenance gaps

The right benchmark label is not a single nominated gene from the paper narrative. It is the set of eight previously unreported genes reported to rescue neurodegeneration in the Drosophila C9ORF72 ALS model, treated as evaluation labels only.

## Current live PrioriTx baseline

After wiring the first four real accession-backed ALS CNS cohorts (`GSE68605`, `GSE20589`, `GSE76220`, and `GSE122649`) and then adding the split `GSE67196` and `GSE124439` exploratory contrasts, the current PrioriTx baseline is still modest:

- cross-contrast ALS CNS transcriptomics currently yields only `2` supported genes in the strict core subset and still only `2` supported genes in the broader exploratory subset even after adding the split `GSE124439` cortex comparisons
- none of the eight Drosophila rescue genes are yet supported by either live cross-contrast transcriptomics layer
- the bounded fused ALS ranking is still dominated by established ALS genetics hits such as `SOD1`, `TUBA4A`, `FUS`, `TARDBP`, `OPTN`, `SQSTM1`, `TBK1`, and `CHMP2B`
- all eight Drosophila rescue genes are measured in the live `GSE122649` subject-collapsed RNA-seq cohort, but they remain weak and non-significant there rather than missing outright
- all four split `GSE67196` contrasts are now live and recover the expected paper-level sample counts:
  - `fALS C9ORF72 frontal cortex`: `8` case / `9` control
  - `fALS C9ORF72 cerebellum`: `8` case / `8` control
  - `sALS frontal cortex`: `10` case / `9` control
  - `sALS cerebellum`: `10` case / `8` control
- both split `GSE124439` contrasts are now live and recover the expected paper-level sample counts:
  - `sALS frontal cortex`: `65` case / `9` control
  - `sALS motor cortex`: `80` case / `8` control
- despite those added cohorts, the exploratory ALS transcriptomics layer still does not elevate the eight rescue genes above the current support threshold, and the only supported genes remain `SERPINA3` and `CDKN2B-AS1`

Interpretation:

- ALS is now benchmarked honestly with real CNS transcriptomics and genetics
- but the eight rescue genes still look more like downstream functional hits than easy first-wave public-expression hits
- the next high-value ALS additions are now `Answer ALS` reconstruction and, if needed, more phenotype-aware ALS subgrouping rather than more unsplit GEO accessions
