# Workflow: Feature Implementation (Mode A/B/D)

**When to use:** Adding new functionality to an existing codebase without creating parallel or inconsistent patterns.

## Steps
1. **Inspect Existing Patterns:** Run `scripts/analyze.py map <repo>` and inspect how similar features are structured (routes, services, models, tests).
2. **Reuse Before Creating:** Check whether existing helpers, services, or abstractions already cover part of the requirement.
3. **Define Contracts & Blast Radius:** Specify new/updated interfaces, data shapes, and affected consumers in `implementation-plan.md`.
4. **Implement Minimal Coherent Design:** Follow existing conventions; avoid speculative abstractions or "for later" config flags.
5. **Verify:** Add unit and integration tests covering happy paths, invalid inputs, and edge cases; verify existing callers remain green.
