# Root-Cause Architect — Universal Agent Adapter

Canonical skill definition: `SKILL.md`.

Before editing code on any non-trivial task:
1. Classify task mode (A/B/C/D) and risk level (0–3) per `SKILL.md`.
2. Gather deterministic evidence via `python3 scripts/analyze.py map|graph|impact`.
3. Diagnose root cause with explicit confidence (`PROVEN`, `STRONGLY SUPPORTED`, `HYPOTHESIS`, `UNKNOWN`).
4. Remove superseded logic only with evidence, implement one unified fix, and report exact verification commands and results.
