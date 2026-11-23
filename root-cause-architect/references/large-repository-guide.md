# Large Repository Guide

When operating on large or monorepo codebases:
1. Start with `python3 scripts/analyze.py map <repo> --json` instead of reading directories recursively in model context.
2. Rely on `config/exclusions.yaml` to skip `node_modules`, `.venv`, `dist`, `build`, `target`, and binaries.
3. Build `dependency-graph.json` once and query slices with `python3 scripts/analyze.py impact <repo> <target> --depth 2`.
4. Read only files directly on the failing execution flow or in the target's blast radius.
5. Re-run `map` / `graph` only after structural edits invalidate the fingerprint.
