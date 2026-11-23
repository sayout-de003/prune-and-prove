# Workflow: Large Project Mapping (Mode C)

**When to use:** Monorepos or repositories with hundreds/thousands of files where full-context reading wastes tokens (Risk Level 0).

## Steps
1. **Run Deterministic Scan First:** Execute `python3 scripts/analyze.py map <repo> --json` to get language, manifest, and framework breakdown without reading all files.
2. **Partition by Subsystem:** Group directories by manifest (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`) and primary entrypoint.
3. **Graph & Slice:** Generate `dependency-graph.json`, then query `python3 scripts/analyze.py impact <repo> <target> --depth 2` only for the active subsystem.
4. **Respect Exclusions & Limits:** Verify `config/exclusions.yaml` skips vendor/build artifacts and marks sensitive/oversized files `inventory_only`.
5. **Summarize Incrementally:** Record subsystem boundaries, contracts, and known `parse_limitations` in `architecture-map.md`.
