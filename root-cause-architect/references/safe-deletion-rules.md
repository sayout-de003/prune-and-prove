# Safe Deletion Rules

Before deleting any function, class, branch, or file:
1. Run `python3 scripts/analyze.py impact <repo> <target> --depth 4`.
2. Check all static callers, importers, and subclasses.
3. Inspect `dynamic_warnings` (`getattr`, `importlib`, `@register`, `@shared_task`, `@receiver`, routes, CLI entrypoints).
4. Check configuration files, templates, migrations, and public package exports (`__all__`, `index.ts`).
5. Classify:
   - `SAFE`: Zero static/dynamic/config callers, or responsibility cleanly superseded in the same change.
   - `REVIEW`: Likely unused, but dynamic/external usage cannot be ruled out statically.
   - `PROTECTED`: Public API, dynamically registered, migration, or critical path.

Never auto-delete `PROTECTED` code.
