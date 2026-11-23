# Workflow: Security Fix (Mode B/D — Risk Level 3)

**When to use:** Vulnerabilities involving auth, authorization, injection, secrets, cryptography, or trust boundaries.

## Steps
1. **Contain & Classify:** Treat as Risk Level 3 per `config/safety.yaml`. Never print or commit secrets.
2. **Trace Untrusted Input:** Map every entrypoint and data flow reaching the vulnerable sink (`execution-flow.md`).
3. **Check All Sibling Paths:** Search the knowledge graph for other endpoints or modules sharing the same flawed pattern.
4. **Design Defense at Boundary:** Fix validation/auth at the authoritative trust boundary — never with fragile client-side or downstream-only checks.
5. **Approval & Implementation:** Obtain explicit approval, apply the unified fix, and add negative security tests (unauthorized/malicious inputs must fail closed).
6. **Security & Adversarial Review:** Require sign-off from `agents/security-reviewer.md` and `agents/adversarial-reviewer.md`.
