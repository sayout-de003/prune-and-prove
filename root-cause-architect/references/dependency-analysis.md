# Dependency Analysis Guide

Use `scripts/analyze.py graph` and `scripts/analyze.py impact` to inspect four linked views:
1. **Import Graph (`IMPORTS`):** File-to-file module dependencies and external packages. Check `GraphValidator.import_cycles` for circular imports.
2. **Call Graph (`CALLS`):** Function/method invocation edges tagged with provenance (`static_ast`, `static_structural`, `static_heuristic`).
3. **Route & Test Graph (`ROUTES_TO`, `TESTS`):** Connects HTTP routes to handlers and test files to the modules they exercise.
4. **Inheritance (`INHERITS`):** Base-class relationships that affect polymorphic dispatch.

Rule: Static edges establish candidate dependencies; never claim a static edge proves runtime execution.
