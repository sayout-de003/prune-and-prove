# Root-Cause Architect — Antigravity Adapter

## Discovery & Installation

- **Workspace Skill:** `.agents/skills/root-cause-architect/SKILL.md` (or `.agent/skills/root-cause-architect/SKILL.md`)
- **Workspace Rules:** `.agents/rules/root-cause-architect.md` (or `AGENTS.md` / `GEMINI.md` at repo root)
- **Global Skill:** `~/.gemini/config/skills/root-cause-architect/SKILL.md`

## Canonical Protocol & Package Layout

Do not duplicate rules here. Load and follow the canonical skill and its companion specifications:

- **Core Protocol:** `SKILL.md` (4 operating modes, anti-patch rules, safety levels 0–3)
- **Specialist Roles:** `agents/*.md` (14 adaptive roles — activate only what task risk requires)
- **Workflows:** `workflows/*.md` (15 task-specific procedures)
- **Configuration:** `config/{default,languages,exclusions,frameworks,safety,verification,quality-gates}.yaml`
- **References & Templates:** `references/*.md`, `templates/*.md`, `schemas/*.schema.json`
- **Documentation:** `docs/*.md`

## Deterministic Toolkit (Run Before Editing)

```bash
python3 scripts/analyze.py health
python3 scripts/analyze.py map <repo> [--output repository-map.md]
python3 scripts/analyze.py graph <repo> [--output dependency-graph.json] [--mermaid architecture.mmd]
python3 scripts/analyze.py impact <repo> <file_or_symbol> [--depth 3]
```
