# Platform Compatibility

| Platform | Skill / Rule Integration | Adapter File | Subagent Support |
| --- | --- | --- | --- |
| **Google Antigravity** | `.agents/skills/root-cause-architect/SKILL.md` + `.agents/rules/` | `adapters/antigravity/rules.md` | Native subagents |
| **Claude Code** | `.claude/skills/root-cause-architect/SKILL.md` + `CLAUDE.md` | `adapters/claude-code/CLAUDE.md` | Native subagents |
| **Cursor** | `.cursor/skills/` + `.cursor/rules/root-cause-architect.mdc` | `adapters/cursor/root-cause-architect.mdc` | Sequential or task agents |
| **OpenAI Codex** | `AGENTS.md` + skill directory | `adapters/codex/AGENTS.md` | Sequential stages |
| **Windsurf** | Workspace rules + skill directory | `adapters/windsurf/rules.md` | Sequential stages |
| **Cline / Roo Code** | `.clinerules/` / project rules | `adapters/cline/rules.md` | Sequential stages |

Where a platform does not support subagents, execute the selected `agents/*.md` roles as sequential reasoning stages in one session. Test activation independently on each platform.
