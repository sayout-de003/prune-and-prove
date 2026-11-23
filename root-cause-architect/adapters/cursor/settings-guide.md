# Cursor Settings & Installation Guide

## Installation

1. Copy `adapters/cursor/root-cause-architect.mdc` into `.cursor/rules/root-cause-architect.mdc`.
2. Place or symlink `root-cause-architect/` into `.cursor/skills/root-cause-architect/`.

## Activation

- Default `alwaysApply: false` keeps context lean; attach `@root-cause-architect` or mention root-cause diagnosis/refactoring to trigger.
- Set `alwaysApply: true` only on repositories where every edit must pass the full evidence-driven protocol.
