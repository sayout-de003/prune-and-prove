# Git Investigation Guide

Use read-only Git history to understand *why* existing code looks the way it does before changing or deleting it:
- `git log -n 10 --oneline -- <file>` — recent changes and context.
- `git log -S "<symbol>" -p` — when a rule, workaround, or fallback was introduced.
- `git blame -L <start>,<end> <file>` — identify the commit behind a suspicious condition.
- `git status --short` — always check for uncommitted user changes and preserve them.

Never rewrite history, force-push, or discard uncommitted user changes without explicit approval.
