1. Parse the official `GSE77314_expression.xlsx` workbook directly from the GEO supplement using stdlib ZIP/XML utilities.
2. Extract the sample-level expression matrix and paired sample identifiers without guessing hidden metadata.
3. Implement a real workbook-backed transcriptomics loader for `hcc_adult_core_gse77314` and score it with the existing paired-expression inference path.
4. Add tests, verify live `CDK20` output, and save a fresh verification report.
