# Architecture Patterns

When mapping a repository, identify which structural patterns govern the codebase and respect them:
- **Layered / Service-Repository:** Routes/Controllers → Services (business rules) → Repositories/Models (persistence). Keep business rules out of controllers and raw SQL out of views.
- **Event-Driven / Queue-Based:** Producers emit immutable events; consumers must be idempotent and handle retries/out-of-order delivery.
- **Modular Monolith / Feature Slices:** Prefer clear module boundaries with explicit public entrypoints over cross-module internal imports.
- **Frontend–Backend Split:** Treat backend schemas/APIs as the authoritative domain contract; keep UI state derived and synchronized.
