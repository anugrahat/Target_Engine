1. Add a GEO-backed transcriptomics ingestion module that fetches the GSE52463 series matrix, parses sample metadata and sample-level gene-count supplement URLs, and downloads count tables from official GEO endpoints.
2. Implement a real differential scoring path over accession-backed counts using transparent normalization and exact permutation p-values, returning Ensembl-keyed gene evidence for the curated IPF contrast.
3. Expose the real-data path through the service, CLI, and HTTP API while keeping the old fixture route isolated for tests only.
4. Add tests for GEO parsing and real-score computation using checked-in minimal fixtures that mirror the official metadata format, then run the full validation and unit test suite.
5. Update repo docs so the first real transcriptomics path is documented precisely, including its scientific limits and provenance.
