1. Add source-backed Open Targets disease identifiers to the benchmark configs where resolved.
   - Verify with benchmark-pack validation.
2. Implement a cached Open Targets GraphQL loader and a genetics-association evidence record path for benchmark diseases.
   - Verify with focused unit tests using patched API responses.
3. Expose Open Targets genetics scores through the service layer, CLI, and read-only API.
   - Verify with service and route tests.
4. Update docs and run the full validation/unit suite plus a live Open Targets smoke test.
