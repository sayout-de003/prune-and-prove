# Workflow: Regression Investigation (Mode B)

**When to use:** Previously working behavior broke after a recent commit, dependency bump, or refactor.

## Steps
1. **Pinpoint Failing Behavior:** Capture minimal reproduction and exact expected vs actual output.
2. **Inspect Git History:** Use `git log`, `git diff`, or `git bisect` to isolate the introducing commit and understand why that change was made.
3. **Analyze Both Requirements:** Ensure fixing the regression does not re-introduce the original bug the introducing commit tried to solve.
4. **Implement Unified Resolution:** Reconcile both invariants in one clean design rather than reverting blindly or stacking conditionals.
5. **Lock with Tests:** Add regression tests covering both the original requirement and the regressed behavior.
