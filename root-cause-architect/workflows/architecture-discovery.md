# Workflow: Architecture Discovery (Mode C)

**When to use:** Onboarding to an unfamiliar codebase or documenting system boundaries (Risk Level 0 — read-only).

## Steps
1. **Inventory Repository:** Run `python3 scripts/analyze.py map <repo> -o repository-map.md`.
2. **Build Knowledge Graph:** Run `python3 scripts/analyze.py graph <repo> -o dependency-graph.json --mermaid architecture.mmd`.
3. **Identify Entrypoints & Boundaries:** Trace HTTP routes, CLI entrypoints, background workers, and database/external boundaries.
4. **Check Graph Health:** Inspect `import_cycles`, `dynamic_signals`, and `parse_limitations` reported by `GraphValidator`.
5. **Document System:** Produce `architecture-map.md` using `templates/architecture-map.md` with explicit provenance (`static_ast` vs `static_structural`).
