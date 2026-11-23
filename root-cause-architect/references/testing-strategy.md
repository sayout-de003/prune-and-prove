# Testing Strategy

Match verification layers to the actual blast radius (per `config/verification.yaml`):
- **Static:** Syntax, type checker, linter, and `GraphValidator` integrity.
- **Unit:** Fast, isolated tests covering the root-cause logic and edge cases.
- **Contract:** Request/response payloads, serialization, and public interface shapes.
- **Integration / DB:** Real interactions across modules, transactions, and migrations.
- **Regression:** Existing covering tests from `scripts/analyze.py impact` plus a new test that fails before the fix and passes after.
- **Security:** Negative tests verifying unauthorized or malformed inputs fail closed.
