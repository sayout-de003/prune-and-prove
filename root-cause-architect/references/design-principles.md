# Design Principles

- **Single source of truth:** Each business rule, state machine, and schema should have one authoritative owner.
- **Smallest coherent change:** Solve the full root cause with the minimum necessary new abstractions.
- **Explicit invariants:** Validate at trust boundaries and fail fast with clear errors when invariants break.
- **Preserve contracts:** Keep public signatures, HTTP shapes, and persisted schemas backward-compatible unless an intentional breaking change is approved.
- **Local-first simplicity:** Reuse existing utilities and stdlib features before adding dependencies or new layers.
