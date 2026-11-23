# Data Flow Analysis Guide

For every critical function along a failing execution path, record:
- **Inputs:** Parameter names, types/shapes, and trust level (untrusted external vs internal).
- **Transformations:** Parsing, normalization, coercion, defaults, and domain calculations.
- **Outputs:** Return values, serialized payloads, and error shapes.
- **Side Effects:** Database writes, cache updates, queue publishes, external HTTP calls, file I/O.
- **Invariants:** Pre-conditions and post-conditions that must hold.

Trace backward from the failure site to find the earliest step where an invariant is violated.
