# Installation Guide

## Prerequisites
- Python 3.11+ (uses stdlib only; `PyYAML` is optional).

## Verify Local Toolkit
```bash
cd root-cause-architect
python3 scripts/analyze.py health
```

## Platform Setup
Install the canonical package once, then add the thin adapter for your coding agent:
- **Antigravity:** Symlink into `.agents/skills/root-cause-architect/` (or `~/.gemini/config/skills/root-cause-architect/`). See `adapters/antigravity/settings-guide.md`.
- **Claude Code:** Symlink into `.claude/skills/root-cause-architect/` and include `adapters/claude-code/CLAUDE.md`. See `adapters/claude-code/settings-guide.md`.
- **Cursor:** Symlink into `.cursor/skills/root-cause-architect/` and copy `adapters/cursor/root-cause-architect.mdc` into `.cursor/rules/`. See `adapters/cursor/settings-guide.md`.
- **Codex / Universal:** Copy `adapters/universal/AGENTS.md` (or `adapters/codex/AGENTS.md`) to your repo root.
- **Windsurf / Cline / Roo Code:** Reference `adapters/windsurf/rules.md` or `adapters/cline/rules.md` in workspace rules.
