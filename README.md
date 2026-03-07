# Codex & Claude Skills Repository

This repository contains Codex-first skills in the root tree plus a smaller Claude mirror under `claude/`, with platform-specific configurations for each environment.

## Directory Structure

```text
codex_skills/
├── AGENTS.md
├── 00-skill-routing-and-escalation.md
├── README.md
├── VALIDATION_REPORT.md
├── reviewer/
├── software-development-life-cycle/
├── web-development-life-cycle/
├── mobile-development-life-cycle/
├── backend-and-data-architecture/
├── cloud-and-devops-expert/
├── qa-and-automation-engineer/
├── security-and-compliance-auditor/
├── ui-design-systems-and-responsive-interfaces/
├── ux-research-and-experience-strategy/
├── git-expert/
├── claude/
└── sync-skills.sh
```

## Skills Overview

### Codex CLI Skills (11 Total)

1. **reviewer** - Code review, quality gates, production readiness
2. **software-development-life-cycle** - Architecture, SDLC, testing
3. **web-development-life-cycle** - Web performance, SEO, browser compatibility
4. **mobile-development-life-cycle** - iOS/Android, app store submission
5. **backend-and-data-architecture** - APIs, microservices, data models, messaging
6. **cloud-and-devops-expert** - Infrastructure as Code, CI/CD, deployment automation
7. **qa-and-automation-engineer** - Test automation, TDD, E2E frameworks
8. **security-and-compliance-auditor** - Threat modeling, vulnerability hunting, compliance
9. **ui-design-systems-and-responsive-interfaces** - Design systems, accessibility
10. **ux-research-and-experience-strategy** - UX research, user testing
11. **git-expert** - Git workflows, conflict resolution

### Claude Mirror Skills (8 Total)

- Shared mirrors: `reviewer`, `software-development-life-cycle`, `web-development-life-cycle`, `mobile-development-life-cycle`, `ui-design-systems-and-responsive-interfaces`, `ux-research-and-experience-strategy`, `git-expert`
- Claude-only: `claude-api`
- Codex-only today: `backend-and-data-architecture`, `cloud-and-devops-expert`, `qa-and-automation-engineer`, `security-and-compliance-auditor`

## Platform Separation

### Codex CLI Runtime
- Located in root directories (11 skill directories total)
- Uses `AGENTS.md` for orchestration
- Supports multi-agent features (explorer, worker, reviewer, architect)
- Skills sync to `~/.codex/skills/` or `C:\Users\<user>\.codex\skills\` (plus `AGENTS.md` + routing doc into `~/.codex/`)

### Claude Code Skills
- Located in `claude/` directory
- **No orchestration file needed** - Claude Code auto-discovers skills
- Each skill is a directory with `SKILL.md` (YAML frontmatter + markdown)
- Syncs to `~/.claude/skills/` or `C:\Users\<user>\.claude\skills\`
- Supports optional files: `template.md`, `examples/`, `scripts/`
- Mirrors 7 shared skills plus the Claude-only `claude-api` skill

## Claude Code Skill Structure

Claude Code follows the Agent Skills open standard. Each skill needs:

```
skill-name/
├── SKILL.md           # Required: YAML frontmatter + instructions
├── template.md        # Optional: template for Claude to fill
├── examples/          # Optional: example outputs
│   └── sample.md
├── scripts/           # Optional: utility scripts
│   └── helper.py
└── references/        # Optional: reference documentation
    └── guide.md
```

**Minimal structure:**
```
skill-name/
└── SKILL.md
```

**SKILL.md format:**
```yaml
---
name: skill-name
description: What this skill does and when to use it
---

Your skill instructions here...
```

## Sync Script Usage

### Sync Both Platforms
```bash
./sync-skills.sh
# or
./sync-skills.sh all
```

### Sync Codex Only
```bash
./sync-skills.sh codex
```

### Sync Claude Only
```bash
./sync-skills.sh claude
```

### Validate Without Syncing
```bash
./sync-skills.sh validate
```

### Check Status
```bash
./sync-skills.sh status
```

## Validation

The sync script validates:
- ✅ YAML frontmatter present
- ✅ Required fields (name, description)
- ✅ No shortform variable names in code
- ✅ File structure integrity
- ✅ Codex guidance avoids non-Codex tool and agent-profile names

## Key Features

### Iterative Development Loops

All skills enforce iterative loops until production-ready:

1. **Research Loop** - Understand technology and approach
2. **Planning Loop** - Document implementation strategy
3. **Implementation Loop** - Write clean, focused code
4. **Testing Loop** - Verify functionality
5. **Fix Loop** - Fix all issues (linting, types, tests, bugs)
6. **Verification Loop** - Confirm solution works
7. **Review Loop** - Self-review before presenting

**Loop continues until:**
- ✅ All tests passing
- ✅ No linting/type errors
- ✅ No bugs found
- ✅ Code review passes
- ✅ All requirements met

### Code Quality Standards

**Readability (Non-Negotiable):**
- ❌ NO shortform names: `usr`, `btn`, `tmp`, `data`, `res`, `req`
- ✅ MUST use full names: `user`, `button`, `temporaryValue`, `userData`, `response`

**Scope Discipline (Non-Negotiable):**
- ❌ NO unrequested features
- ❌ NO unnecessary refactoring
- ❌ NO backward compatibility (unless requested)
- ✅ ONLY implement what was requested

**Quality Gates:**
- All linting errors fixed (not disabled)
- All type errors fixed (not suppressed)
- All tests passing (not skipped)
- No security vulnerabilities
- No duplicate code

## Installation

### For Codex CLI

1. Clone or download this repository
2. Run sync script:
   ```bash
   cd /path/to/codex_skills
   ./sync-skills.sh codex
   ```
3. Skills will be synced to `~/.codex/skills/` (plus `AGENTS.md` + routing doc into `~/.codex/`)

### For Claude Code

1. Create Claude-specific skills in `claude/` directory
2. Run sync script:
   ```bash
   ./sync-skills.sh claude
   ```
3. Skills will be synced to `~/.claude/skills/`

## Windows Usage

On Windows, prefer Git Bash for the sync script:

```bash
cd /d/Nasri/Project/codex_skills
./sync-skills.sh validate
./sync-skills.sh all
```

Inside this Codex runtime, route validation through `js_repl` + `codex.tool("exec_command", ...)` and select Git Bash explicitly instead of wrapping the script in PowerShell:

```javascript
await codex.tool("exec_command", {
  shell: "C:\\Program Files\\Git\\bin\\bash.exe",
  cmd: "./sync-skills.sh validate",
  workdir: "D:\\Nasri\\Project\\codex_skills"
})
```

## Development Workflow

### Adding a New Skill

1. Create skill directory: `mkdir new-skill`
2. Create `SKILL.md` with YAML frontmatter
3. Add reference files in `references/` directory
4. Validate: `./sync-skills.sh validate`
5. Sync: `./sync-skills.sh`

### Updating Existing Skills

1. Edit skill files
2. Validate: `./sync-skills.sh validate`
3. Sync: `./sync-skills.sh`

### Creating Claude-Specific Skills

1. Create skill in `claude/` directory
2. Follow same structure as Codex skills
3. Sync: `./sync-skills.sh claude`

## Reference Documentation

Each skill includes comprehensive reference documentation:

- **00-knowledge-map.md** - Capability matrix
- **10-50 numbered files** - Domain-specific guidance
- **99-source-anchors.md** - Authoritative sources

## Troubleshooting

### Sync Script Not Executable

```bash
chmod +x sync-skills.sh
```

### Validation Failures

Check error messages and fix issues:
- Missing YAML frontmatter
- Missing required fields
- Shortform variable names in code

### Skills Not Loading

1. Check sync status: `./sync-skills.sh status`
2. Verify target directory exists
3. Re-sync: `./sync-skills.sh`

## Contributing

When contributing to skills:

1. Follow existing structure
2. Use full descriptive names (no shortforms)
3. Include comprehensive examples
4. Add reference documentation
5. Validate before committing
6. Test with actual Codex CLI or Claude Code

## License

These skills are for personal use with Codex CLI and Claude Code.

## Support

For issues or questions:
- Check validation output: `./sync-skills.sh validate`
- Review skill documentation
- Check Codex CLI or Claude Code documentation
