# Claude Code Settings & Installation Guide

## Installation

1. Place or symlink the package at `.claude/skills/root-cause-architect/` (project) or `~/.claude/skills/root-cause-architect/` (user).
2. Add the contents of `adapters/claude-code/CLAUDE.md` to your repository's `CLAUDE.md`.

## Recommended Tool Permissions

Allow read-only execution of the local analysis CLI without friction:
- `python3 scripts/analyze.py health`
- `python3 scripts/analyze.py map *`
- `python3 scripts/analyze.py graph *`
- `python3 scripts/analyze.py impact *`

Keep write/edit and destructive shell approvals enabled per `config/safety.yaml`.
