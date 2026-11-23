# Verification Evidence Rules

Per `config/verification.yaml`:
- Every claimed pass must cite the exact command executed and its real exit status / test count.
- Static analysis (`ast`, linters, type checks) proves structural validity — **not** runtime correctness.
- Passing unit tests prove isolated logic — **not** end-to-end integration or database state.
- Explicitly list every verification layer that was **not** executed (e.g., E2E, live DB migration, production-like load) along with remaining risks.
