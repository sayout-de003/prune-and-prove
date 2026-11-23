# Performance Guidelines

- **Measure before optimizing:** Establish a concrete baseline (timing, query count, memory, or complexity) before changing code for speed.
- **Target structural wins:** Eliminate N+1 database queries, unbounded in-memory loads, redundant network round-trips, and quadratic loops on large inputs.
- **Avoid premature complexity:** Do not introduce caches, background workers, or concurrency without evidence of a bottleneck and a clear invalidation/error-handling strategy.
- **Verify equivalence:** Performance changes must preserve all functional and edge-case contracts.
