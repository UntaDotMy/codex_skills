# Codex Skills Repository

This repository is a Codex-first skill pack for OpenAI Codex CLI. It ships specialist skills, repo-wide orchestration guidance, sync tooling for `~/.codex`, and a memory-status workflow that turns saved artifacts into human-style learning reports.

## Directory Structure

```text
codex_skills/
├── AGENTS.md
├── 00-skill-routing-and-escalation.md
├── README.md
├── VALIDATION_REPORT.md
├── docs/
│   └── context-efficiency-playbook.md
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
├── memory-status-reporter/
└── sync-skills.sh
```

Located in root directories (12 skill directories total).

### Codex CLI Skills (12 Total)

1. **reviewer** - Production readiness, quality gates, DRY enforcement
2. **software-development-life-cycle** - Architecture, planning, delivery, validation
3. **web-development-life-cycle** - Web implementation, browser/runtime quality
4. **mobile-development-life-cycle** - Mobile lifecycle, release, offline, platform behavior
5. **backend-and-data-architecture** - APIs, contracts, data flow, service integration
6. **cloud-and-devops-expert** - Infrastructure, CI/CD, release reliability, observability
7. **qa-and-automation-engineer** - Test strategy, regression coverage, automation
8. **security-and-compliance-auditor** - Threat modeling, secrets, remediation, compliance
9. **ui-design-systems-and-responsive-interfaces** - Design systems, accessibility, visual execution
10. **ux-research-and-experience-strategy** - UX framing, jobs-to-be-done, usability strategy
11. **git-expert** - Repository-state safety, branching, recovery, review handoff
12. **memory-status-reporter** - Daily learnings, mistake ledgers, tool-mistake tracking, and heuristic memory-health reporting

## Setup

### Requirements

- Codex CLI with `js_repl`, `memories`, and `multi_agent` enabled
- Python 3 for memory-report tooling and sync helpers
- Git Bash on Windows if you want to run `sync-skills.sh` directly

### Install the Skill Pack

```bash
./sync-skills.sh validate
./sync-skills.sh codex
./sync-skills.sh status
```

The sync does all of the following:

- copies root skills into `~/.codex/skills/`
- copies `AGENTS.md` and `00-skill-routing-and-escalation.md` into `~/.codex/`
- refreshes `~/.codex/agents/*.toml` from each root `agents/openai.yaml`
- keeps `~/.codex/config.toml` wired for `memory-status-reporter`
- injects shared execution-policy lines for working briefs, context efficiency, modular structure, surgical patches, and compact learning snapshots

### macOS and Linux

Codex home: `~/.codex`

### Windows

The sync script detects Windows shells and maps Codex home to `%USERPROFILE%\\.codex`. In Git Bash this usually appears as `/c/Users/<user>/.codex`.

Inside Codex runtime, route shell work through `js_repl` and `codex.tool("exec_command", ...)`:

```javascript
await codex.tool("exec_command", {
  shell: "C:\\Program Files\\Git\\bin\\bash.exe",
  cmd: "./sync-skills.sh validate",
  workdir: "D:\\path\\to\\codex_skills"
})
```

## Context Efficiency Playbook

This repo now treats context efficiency like a product requirement.

### Default Retrieval Ladder

1. **Working brief first** — restate the user story, outcome, constraints, acceptance criteria, and validation plan
2. **Exact retrieval first** — use file, symbol, or keyword search before broad reads
3. **Targeted reads second** — inspect only the relevant snippets, callers, callees, and direct dependencies
4. **Full reads only for edit scope** — fully read only files you will edit or that directly drive the change
5. **Surgical patching** — change only the impacted ranges instead of rewriting whole files
6. **Final re-read** — re-read the working brief plus touched files before validating or answering

### Token-Saving Techniques

- keep stable prompt prefixes so caches can hit more often
- move volatile evidence to the end of prompts
- summarize long histories into reusable notes instead of replaying raw logs
- use compact memory snapshots instead of pasting entire memory files
- avoid regenerating unchanged code when a diff or narrow patch is enough
- prefer modular files so future reads stay narrow and traceable

### Research Summary

The detailed research-backed version lives in `docs/context-efficiency-playbook.md`. The practical conclusions are:

- use retrieval-augmented generation for large bodies of reference text or project memory
- combine exact search with semantic retrieval when the corpus is broad
- compress or summarize before sending long context to the model
- reuse cached prefixes and small focused models for narrow classification or filtering work
- separate working memory, episodic memory, and durable memory so you do not keep replaying everything

## Memory Growth Reporting

The memory workflow is intentionally human-style, but still evidence-bound.

### Memory Layers

- **Working memory** — the current working brief, active files, and validation target
- **Episodic memory** — rollout summaries and recent task evidence
- **Durable memory** — indexed learnings and recurring user preferences in `~/.codex/memories/MEMORY.md` and `~/.codex/memories/memory_summary.md`

### Compact Learning Snapshot

For non-trivial tasks, the repo guidance now supports a compact final-answer footer with:

- what Codex learned today
- mistakes and tool-use mistakes captured today
- whether they are resolved, open, or unclear
- heuristic memory-health stats such as brain size, brain growth, and momentum

These values are derived from saved artifacts. They are not literal cognition measurements.

### Run the Full Report

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories
```

### Run the Compact Footer Version

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories --format compact
```

## Development Workflow

### Update Skills

```bash
./sync-skills.sh validate
./sync-skills.sh codex
./sync-skills.sh status
```

### Add a New Skill

1. Create a new root skill directory.
2. Add `SKILL.md`.
3. Add `references/`.
4. Add `agents/openai.yaml`.
5. Validate and sync.

### Modular Code Preference

When you extend scripts or supporting utilities in this repo:

- keep entrypoints thin
- extract focused helpers instead of growing one giant function
- separate documentation, sync logic, validation logic, and reporting logic cleanly
- prefer incremental, surgical patches over full rewrites unless the rewrite is clearly safer

## Validation

The sync script validates:

- YAML frontmatter and required metadata
- root prompt/runtime guidance for Codex
- same-role agent reuse and robust handoff wording
- UI/UX strengthening and memory tool-mistake wording
- README and validation-report inventory parity
- top-level guidance drift and Codex-home wiring

## Troubleshooting

### Sync says config is partial

Run:

```bash
./sync-skills.sh codex
./sync-skills.sh status
```

Then verify `~/.codex/config.toml` contains the `memory-status-reporter` route line, the `memory-status-reporter` agent block, and the injected execution-policy lines for working briefs, context retrieval, surgical patching, modular structure, and learning snapshots.

### Memory footer looks thin

That usually means the current memory window is quiet or the rollout summaries did not capture reusable learnings or mistakes. The system should say that directly instead of fabricating certainty.

## Related Docs

- `docs/context-efficiency-playbook.md`
- `AGENTS.md`
- `00-skill-routing-and-escalation.md`
- `VALIDATION_REPORT.md`

## License

These skills are intended for personal or team use with Codex CLI.
