# Security Guidelines

- **Secrets:** Never read, print, or transmit `.env*`, private keys, or credential files (`config/exclusions.yaml` marks them `inventory_only`).
- **Trust boundaries:** Validate and authorize at the authoritative server boundary; never rely on client-side checks alone.
- **Injection & traversal:** Use parameterized queries, strict path containment (reject paths escaping repo root), and safe parsers (no `eval`/`exec` on untrusted data).
- **High-risk domains:** Treat auth, authorization, payments, encryption, and production config as Risk Level 3 requiring explicit approval.
