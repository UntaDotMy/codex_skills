# Claude Code Skills

This directory contains skills for Claude Code (the CLI tool).

## Claude Code Skill Structure

Claude Code auto-discovers skills from `~/.claude/skills/`. Each skill is a directory with `SKILL.md`:

```
skill-name/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── template.md        # Optional: template for Claude to fill
├── examples/          # Optional: example outputs
├── scripts/           # Optional: utility scripts
└── references/        # Optional: reference documentation
```

## SKILL.md Format

Every skill needs YAML frontmatter + markdown content:

```yaml
---
name: skill-name
description: What this skill does and when to use it
---

Your skill instructions here...
```

## Key Differences from Codex CLI

1. **No AGENTS.md** - Claude Code auto-discovers skills, no orchestration file needed
2. **YAML frontmatter required** - Must have `---` markers with `name` and `description`
3. **Auto-discovery** - Skills loaded from `~/.claude/skills/`, `.claude/skills/`, or plugin skills
4. **Optional files** - Can include `template.md`, `examples/`, `scripts/` in skill directory

## Syncing

To sync Claude skills to global directory:

```bash
cd /path/to/codex_skills
./sync-skills.sh claude
```

Skills will be synced to:
- Linux/Mac: `~/.claude/skills/`
- Windows: `C:\Users\<user>\.claude\skills\`

## Current Skills

This tree mirrors 7 shared skills from the root Codex set and adds one Claude-only skill:
1. reviewer
2. git-expert
3. mobile-development-life-cycle
4. software-development-life-cycle
5. ui-design-systems-and-responsive-interfaces
6. ux-research-and-experience-strategy
7. web-development-life-cycle
8. claude-api (Claude Code only)

Codex-only skills that are not mirrored here today:
- backend-and-data-architecture
- cloud-and-devops-expert
- qa-and-automation-engineer
- security-and-compliance-auditor

Each mirrored skill maintains the same quality standards and iterative loops as the root Codex skill, but follows Claude Code's skill format.
