# Workflow: Quick Bug Fix (Mode A)

**When to use:** Localized defect within 1–2 modules, Risk Level 1.

## Steps
1. **Locate & Scope:** Run `python3 scripts/analyze.py impact <repo> <target> --depth 2` to confirm callers and covering tests.
2. **Reproduce & Diagnose:** Reproduce the failing behavior (or trace exact inputs/outputs) and separate symptom from earliest invalid state. Label confidence (`PROVEN` / `STRONGLY SUPPORTED`).
3. **Check for Duplicates:** Search nearby modules for duplicated logic or old workarounds handling the same invariant.
4. **Fix at Source:** Remove superseded workaround if proven safe; apply the smallest unified fix at the source of truth.
5. **Verify:** Run covering tests plus a new regression test proving the root cause is fixed. Record exact commands and outputs.
6. **Self-Review:** Verify no anti-patch rules were violated and no unrelated code was modified.
