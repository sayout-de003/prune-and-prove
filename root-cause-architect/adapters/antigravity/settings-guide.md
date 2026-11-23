# Antigravity Settings & Installation Guide

## Workspace Installation (Recommended for Teams)

Copy or symlink `root-cause-architect/` into your repository's `.agents/skills/` directory:

```bash
mkdir -p .agents/skills .agents/rules
ln -s /path/to/root-cause-architect .agents/skills/root-cause-architect
cp /path/to/root-cause-architect/adapters/antigravity/rules.md .agents/rules/root-cause-architect.md
```

## Global Installation (All Projects)

```bash
mkdir -p ~/.gemini/config/skills
ln -s /path/to/root-cause-architect ~/.gemini/config/skills/root-cause-architect
```

## Verification

1. Run `python3 .agents/skills/root-cause-architect/scripts/analyze.py health`.
2. Confirm `"status": "ok"` and all 7 configs loaded.
3. Ask Antigravity to diagnose a bug or map a repository; verify it invokes `scripts/analyze.py` before editing code.
