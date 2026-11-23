# Root-Cause Architect — Universal Agent Adapter

Canonical skill & routing index: `SKILL.md`.

Before editing code on any non-trivial task:
1. Classify task mode (A/B/C/D) and risk level (0–3) per `SKILL.md`.
2. **Route directly** using `SKILL.md` Section 4 & 4.1: read the matching `workflows/<task>.md`, `agents/AGENT_CONTRACT.md` + required `agents/<role>.md`, and relevant `references/<topic>.md` / `templates/<name>.md`.
3. Gather deterministic evidence via `python3 scripts/analyze.py map|graph --html|impact`.
4. Diagnose root cause with explicit confidence (`PROVEN`, `STRONGLY SUPPORTED`, `HYPOTHESIS`, `UNKNOWN`).
5. Remove superseded logic only with evidence, implement one unified fix, and report exact verification commands and results.
