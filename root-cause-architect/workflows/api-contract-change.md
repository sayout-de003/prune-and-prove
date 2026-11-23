# Workflow: API Contract Change (Mode B/D — Risk Level 2–3)

**When to use:** Modifying request/response payloads, status codes, route paths, headers, or webhook schemas.

## Steps
1. **Enumerate Consumers:** Run `scripts/analyze.py impact <repo> <route_or_handler> --depth 4` to locate all internal, frontend, and test consumers.
2. **Audit Compatibility:** Classify the change as additive (backward-compatible) or breaking (requires versioning or explicit approval).
3. **Update Source of Truth:** Update schema definitions, validators, serializers, handlers, and API clients together.
4. **Contract & Regression Tests:** Verify valid payloads, invalid payloads, and backward-compatibility guarantees.
5. **Document:** Record contract diff and any external consumer coordination required in `final-engineering-report.md`.
