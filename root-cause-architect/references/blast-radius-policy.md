# Blast-Radius Policy

Every code modification must be scoped to its verified blast radius:
- **Depth 1 (Direct):** Immediate callers, importers, subclasses, and routes of the edited file/symbol — always inspect.
- **Depth 2–3 (Transitive):** Upstream services, entrypoints, and covering tests — inspect for Level 2/3 changes.
- **Dynamic Warnings:** Any `getattr`, `importlib`, decorator registration, or route binding in the affected files elevates deletion risk to `REVIEW` or `PROTECTED`.
- **Risk Escalation:** If blast radius crosses into shared business logic or public interfaces, escalate to Risk Level 2; if it touches DB migrations, auth, or payments, escalate to Risk Level 3.
