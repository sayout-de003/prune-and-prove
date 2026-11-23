# Root-Cause Architect — Claude Code Adapter

Follow the canonical engineering protocol in `SKILL.md` (install at `.claude/skills/root-cause-architect/SKILL.md` or reference from repository root).

Before editing code on any non-trivial task:
1. Run `python3 scripts/analyze.py map .` to inventory languages, frameworks, and entrypoints.
2. Run `python3 scripts/analyze.py impact . <target>` to inspect callers, callees, and covering tests.
3. Follow the evidence-driven workflow, anti-patch rules, and risk-level approval policy in `SKILL.md`.
