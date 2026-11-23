# Security & Safety Model

- **Read-only scanning:** `FileClassifier` and `RepositoryScanner` never modify files, never execute repository code, and never follow symlinks.
- **Path containment:** `FileClassifier.classify` rejects any path resolving outside the repository root.
- **Secret protection:** `.env`, `.env.*`, `id_rsa`, `id_ed25519`, `credentials.json`, and `service-account.json` are classified `inventory_only` — their presence is recorded without reading or exposing contents.
- **Tiered approvals:** Enforced via `config/safety.yaml` (Level 0–1 automatic, Level 2 review required, Level 3 explicit approval).
- **Conservative deletion:** Dynamic signals (`getattr`, `importlib`, decorator registrations, routes) are surfaced in blast-radius reports so agents never blindly prune dynamically invoked code.
