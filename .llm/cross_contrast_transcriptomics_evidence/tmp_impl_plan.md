1. Add an indication-level transcriptomics aggregation contract and document the aggregation rules.
   - Verify by reading the schema/spec and checking they match the existing real-contrast model.
2. Implement aggregation utilities that combine real transcriptomics contrast outputs by Ensembl gene within a benchmark or subset.
   - Verify with focused unit tests on deterministic mocked contrast outputs.
3. Expose the aggregate evidence through the service layer, CLI, and read-only HTTP API.
   - Verify with route tests and a local CLI/API smoke test.
4. Update docs and run the full validation and unit test suite.
   - Verify with Ruby validators, Python unit tests, and a live smoke test against real contrasts.
