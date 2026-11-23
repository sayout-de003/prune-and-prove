# Workflow: Final Verification (All Modes)

**When to use:** Mandatory closing gate before declaring any engineering task complete.

## Steps
1. **Check Quality Gates:** Evaluate every applicable gate in `config/quality-gates.yaml`.
2. **Run Verification Layers:** Execute static analysis, unit, contract, integration, and regression tests per `config/verification.yaml`.
3. **Re-Validate Graph:** For refactors/deletions, re-run `python3 scripts/analyze.py graph <repo>` to verify zero dangling edges or unintended import cycles.
4. **Independent Challenge:** For Modes B and D, run `agents/adversarial-reviewer.md` against the diff and evidence.
5. **Publish Evidence Report:** Emit `final-engineering-report.md` (using `templates/completion-report.md`) listing exact commands executed, actual results, unexecuted checks, and remaining risks.
