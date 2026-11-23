# Workflow: Performance Optimization (Mode B/D)

**When to use:** High latency, excessive DB queries, memory spikes, or CPU hotspots (Risk Level 1–2).

## Steps
1. **Measure First:** Capture reproducible baseline metrics (latency, query count, allocations, or profiling output). Do not optimize on guesswork.
2. **Trace Hot Path:** Map the execution path from entrypoint to bottleneck using `scripts/analyze.py impact` and `execution-flow.md`.
3. **Identify Structural Cause:** Distinguish algorithmic complexity, N+1 queries, redundant I/O, or missing indexes from micro-overhead.
4. **Implement Focused Fix:** Fix the structural bottleneck without breaking contracts or adding unnecessary caching complexity.
5. **Re-Measure & Verify:** Capture after-metrics under the same conditions, run regression tests, and review with `agents/performance-reviewer.md`.
