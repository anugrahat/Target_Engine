1. Add GSE24206 to the real transcriptomics connector registry using official GEO series-matrix and GPL570 annotation inputs.
   - Verify by checking the real contrast registry and loader selection.
2. Add a focused unit test for the patched GSE24206 microarray loader path.
   - Verify with the Python unit suite.
3. Update docs/README references to the live real-data connector inventory.
   - Verify by reading the changed docs.
4. Run the unit suite and a live transcriptomics-evidence smoke test to confirm IPF now aggregates across two real contrasts.
