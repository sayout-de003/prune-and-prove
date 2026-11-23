# CLI Commands Reference

All Phase 1–3 analysis commands are exposed through `scripts/analyze.py` (or directly via individual scripts in `scripts/`):

## `health`
Verify `SKILL.md`, all 7 YAML configs, and active parsers:
```bash
python3 scripts/analyze.py health
```

## `map`
Scan a repository (read-only) and report languages, manifests, frameworks (with evidence), entrypoints, tests, and migrations:
```bash
python3 scripts/analyze.py map <repo_path> [--output repository-map.md] [--json]
```

## `graph`
Parse analyzable files, build the unified `DependencyGraph`, validate graph integrity and import cycles, and export JSON / Mermaid:
```bash
python3 scripts/analyze.py graph <repo_path> [--output dependency-graph.json] [--mermaid architecture.mmd] [--include-external]
```

## `impact`
Compute upstream dependents, downstream dependencies, covering tests, and dynamic-registration warnings for a file or symbol:
```bash
python3 scripts/analyze.py impact <repo_path> <file_or_symbol> [--depth 3] [--json]
```
