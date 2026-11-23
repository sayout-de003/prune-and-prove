# Root-Cause Architect — Antigravity Adapter

## Discovery & Installation

- **Workspace Skill:** `.agents/skills/root-cause-architect/SKILL.md` (or `.agent/skills/root-cause-architect/SKILL.md`)
- **Workspace Rules:** `.agents/rules/root-cause-architect.md` (or `AGENTS.md` / `GEMINI.md` at repo root)
- **Global Skill:** `~/.gemini/config/skills/root-cause-architect/SKILL.md`

## Canonical Protocol & Direct Routing

Do not stop at the overview in `SKILL.md`. On every non-trivial task, use **Section 4 & 4.1 of `SKILL.md`** to route directly to and read the exact companion files needed:

- **Core Protocol & Routing Table:** `SKILL.md` (4 operating modes, anti-patch rules, safety levels 0–3, full file index)
- **Workflows (read matching task workflow first):** `workflows/*.md` (15 task-specific procedures)
- **Specialist Roles (read `AGENT_CONTRACT.md` + active roles):** `agents/*.md` (14 adaptive roles)
- **References & Templates (read on demand):** `references/*.md` (17 guides), `templates/*.md` (9 templates), `schemas/*.schema.json` (9 schemas)
- **Configuration:** `config/{default,languages,exclusions,frameworks,safety,verification,quality-gates}.yaml`

## Deterministic Toolkit (Run Before Editing)

```bash
python3 scripts/analyze.py health
python3 scripts/analyze.py map <repo> [--output repository-map.md]
python3 scripts/analyze.py graph <repo> [--output dependency-graph.json] [--mermaid architecture.mmd] [--html architecture-3d.html]
python3 scripts/analyze.py impact <repo> <file_or_symbol> [--depth 3]
```
