# Workflow: Frontend–Backend Tracing (Mode B/C)

**When to use:** Full-stack defects where UI state, API payloads, and backend persistence disagree.

## Steps
1. **Map Both Sides:** Run `scripts/analyze.py map <repo>` and `scripts/analyze.py graph <repo>` across frontend and backend roots.
2. **Trace the Request Chain:** UI component → state/store → API client → HTTP route → validation/serializer → service → DB model → response → UI rendering.
3. **Compare Contracts:** Check field names, types, nullability, enum values, and error shapes at every boundary.
4. **Locate First Divergence:** Identify where expected and actual state first diverge — fix the authoritative side rather than patching the UI to mask bad API data.
5. **Verify End-to-End:** Test backend response shape and frontend handling of success, validation error, and retry states.
