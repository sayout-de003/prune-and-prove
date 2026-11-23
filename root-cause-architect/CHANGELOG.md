# Changelog

## 2.0.0

### Phase 1 — Core Skill, Config & Adapters
- Upgraded `SKILL.md` to v2.0.0 with 4 operating modes, 14 adaptive specialist roles, anti-patch rules, safety risk levels 0–3, and CLI toolkit integration.
- Added `config/default.yaml` and stdlib-only `engine/config_loader.py` (with PyYAML fallback).
- Added thin cross-platform discovery adapters for Claude Code, Cursor, Antigravity, Codex, Windsurf, Cline, and universal `AGENTS.md`.

### Phase 2 — Repository Scanner, Detectors & Language Parsers
- Built `ProjectDetector`, `FrameworkDetector`, `EntrypointDetector`, and `ManifestBuilder` on top of `FileClassifier` and `RepositoryScanner`.
- Built `ParserRegistry`, native AST `PythonParser`, structural `JavaScriptParser` / `TypeScriptParser`, and `FallbackParser`.

### Phase 3 — Knowledge Graph, Impact Analysis & CLI
- Built `SymbolIndex`, `ImportGraph`, `CallGraph`, `DependencyGraph`, `GraphBuilder`, `GraphExporter` (JSON, Mermaid, Markdown), and `GraphValidator`.
- Implemented runnable CLIs: `scripts/analyze.py`, `scripts/map_project.py`, `scripts/generate_graph.py`, `scripts/analyze_impact.py`, and `scripts/health_check.py`.
- Added Python and TypeScript test fixtures plus unit and CLI integration test suites.
