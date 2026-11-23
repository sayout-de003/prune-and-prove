# Configuration Guide

All configuration files live in `config/` and are loaded by `engine/config_loader.py`:

| File | Purpose |
| --- | --- |
| `config/default.yaml` | Core system mode, engineering discipline flags, and reporting defaults. |
| `config/languages.yaml` | Supported extensions, filenames, file categories (`test`, `migration`, `configuration`, `generated`), and parser policy. |
| `config/exclusions.yaml` | Excluded build/vendor directories, binary extensions, max file size (`2 MiB`), and sensitive files (`inventory_only`). |
| `config/frameworks.yaml` | Evidence-based framework detection rules (`minimum_evidence: 2`, confidence thresholds). |
| `config/safety.yaml` | Risk levels 0–3, approval triggers, and non-negotiable secret/DB/git protections. |
| `config/verification.yaml` | Verification layers and honest-reporting policy. |
| `config/quality-gates.yaml` | Mandatory pre-edit, anti-patch, deletion-safety, graph-integrity, and review gates. |

`engine/config_loader.py` uses `PyYAML` when installed and falls back to its built-in stdlib block-YAML parser otherwise.
