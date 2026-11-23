# Anti-Patch Rules

Non-negotiable rules enforced across all modes:
- **No symptom masking:** Do not add downstream `if x is None: return default` guards to hide an upstream producer bug.
- **No silent suppression:** Never add bare `except Exception: pass` or swallow errors to turn tests green.
- **No test overfitting:** Never branch on fixture IDs, test filenames, or hardcoded expected outputs.
- **No parallel implementations:** Do not add a second helper doing the same job as a broken one — fix and consolidate the original.
- **No unverified claims:** Never report a test or check as passing unless you executed it and observed exit code 0.

*Exception:* Legitimate domain fallbacks (e.g., idempotent retries, graceful degradation on external API outages) are valid when explicitly required by domain contracts.
