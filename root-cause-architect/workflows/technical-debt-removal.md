# Workflow: Technical Debt Removal (Mode D)

**When to use:** Removing dead code, obsolete feature flags, legacy compatibility shims, or accumulated workarounds (Risk Level 2).

## Steps
1. **Inventory Candidates:** Build `dependency-graph.json` and identify unreferenced symbols, redundant wrappers, or deprecated paths.
2. **Prove Deletion Safety:** For every candidate, check static callers, `dynamic_warnings` (`getattr`, `importlib`, decorators, routes, tasks), config files, and public API exports.
3. **Classify:** Produce `deletion-plan.md` tagging each item `SAFE`, `REVIEW`, or `PROTECTED`. Never auto-delete `PROTECTED` items.
4. **Remove Incrementally:** Delete only approved `SAFE` items along with their obsolete tests and unused imports.
5. **Verify:** Run static checks (syntax/types/lint), unit tests, and regression tests; confirm zero dangling references via `scripts/analyze.py graph`.
