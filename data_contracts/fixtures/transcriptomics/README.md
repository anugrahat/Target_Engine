# Transcriptomics Fixtures

These files are small illustrative differential-expression style fixtures for
local development.

Important:

- they are not real accession-derived analysis outputs
- they exist to exercise contracts, loaders, ranking logic, and API routes
- they must never be described as benchmark evidence

Each file is JSON Lines (`.jsonl`) and each line must validate against
`data_contracts/schemas/transcriptomics_gene_stat.schema.json`.
