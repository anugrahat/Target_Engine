1. Verify current Open Targets disease-target retrieval against live GraphQL for benchmark disease IDs.
2. Determine whether benchmark positives are absent because of disease ID scope, API query shape, or true lack of genetics evidence.
3. Implement a source-backed genetics audit surface that exposes disease-mapping and per-target match status without changing ranking rules.
4. Add tests, run validators, and verify live output for TNIK and CDK20.
