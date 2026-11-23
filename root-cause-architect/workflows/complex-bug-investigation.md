# Workflow: Complex Bug Investigation (Mode B)

**When to use:** Multi-module, async/event, API/DB, or intermittent state-corruption bugs (Risk Level 2–3).

## Steps
1. **Map Context:** Run `python3 scripts/analyze.py map <repo>` and `python3 scripts/analyze.py graph <repo> -o dependency-graph.json`.
2. **Trace End-to-End Flow:** Build `execution-flow.md` from entrypoint through every state mutation and downstream consumer.
3. **Inspect History:** Check `git log -p` / `git blame` for prior patches, workarounds, and contract shifts.
4. **Isolate Root Cause:** Produce `root-cause-report.md` separating symptom, trigger, immediate failure, earliest invalid state, and underlying defect.
5. **Audit Redundancy:** Identify duplicate rules and obsolete workarounds; classify each deletion candidate (`SAFE` / `REVIEW` / `PROTECTED`).
6. **Design Unified Fix:** Write `implementation-plan.md` and obtain approval if Risk Level 2/3.
7. **Delete-First Implementation:** Remove approved superseded logic, fix the root cause, update callers and contracts.
8. **Verify & Adversarial Review:** Run static, unit, integration, and regression checks; run `agents/adversarial-reviewer.md` before producing `final-engineering-report.md`.
