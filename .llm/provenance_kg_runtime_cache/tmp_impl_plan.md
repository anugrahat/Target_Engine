1. Add a local Reactome membership cache module and cache-builder script, then verify the files are importable.
2. Refactor KG pathway assembly to use cached gene memberships plus a single enrichment call, and keep live fallback only for cache misses.
3. Add unit coverage for cache-aware graph assembly and graceful fallback behavior.
4. Run the relevant Python test suite, build a bounded cache, and rerun a bounded live graph benchmark to confirm runtime and target-rank output.
