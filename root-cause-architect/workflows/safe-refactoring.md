# Workflow: Safe Refactoring (Mode D)

**When to use:** Restructuring shared modules, abstractions, or boundaries without changing intended behavior (Risk Level 2–3).

## Steps
1. **Establish Baseline:** Run existing tests and record baseline pass/fail results before editing anything.
2. **Map Blast Radius:** Run `python3 scripts/analyze.py impact <repo> <target> --depth 4` and inspect all upstream dependents, covering tests, and `dynamic_warnings`.
3. **Plan Migration:** Write `implementation-plan.md` specifying contracts to preserve, code to delete/consolidate, and rollback steps.
4. **Approval Gate:** Obtain review/approval per `config/safety.yaml` before modifying shared interfaces.
5. **Execute Delete-First:** Remove approved superseded code, consolidate responsibilities, and update every caller in one coherent change.
6. **Verify Behavior Equivalence:** Run unit, contract, integration, and regression checks; pass `agents/regression-reviewer.md` and `agents/adversarial-reviewer.md`.
