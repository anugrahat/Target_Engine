1. Define a simple fused target-evidence contract that combines cross-contrast transcriptomics and Open Targets genetics by Ensembl gene.
   - Verify the contract shape against current evidence records.
2. Implement the fusion service and scoring layer with transparent components and provenance.
   - Verify with focused unit tests on deterministic mocked evidence.
3. Expose the fused target-evidence layer through the read-only API and CLI.
   - Verify with route tests.
4. Update docs and run the full validation/test suite plus a live smoke test for IPF and HCC.
