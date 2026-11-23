# Workflow: Duplicate Logic Consolidation (Mode B/D)

**When to use:** The same business rule, validation, or transformation is implemented in two or more modules (Risk Level 2).

## Steps
1. **Find All Copies:** Locate every implementation of the rule and list behavioral differences (edge cases, error types, side effects).
2. **Choose Source of Truth:** Select the canonical module/owner based on existing architecture boundaries (`architecture-map.md`).
3. **Analyze Blast Radius:** Run `python3 scripts/analyze.py impact` on every duplicate to enumerate all callers and tests.
4. **Consolidate & Prune:** Migrate all callers to the canonical implementation, delete the superseded duplicates, and merge edge-case tests.
5. **Verify:** Confirm all callers preserve expected contracts and zero behavioral regressions occur.
