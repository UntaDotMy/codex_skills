# Codex Skills Repository

This repository is a Codex-first skill pack for OpenAI Codex CLI. It ships specialist skills, repo-wide orchestration guidance, sync tooling for `~/.codex`, and a memory-status workflow that turns saved artifacts into human-style learning reports.

## Quick Start

### AI-Assisted Install

If you want Codex to install this for you, copy and paste this prompt into a Codex session:

```text
Please install this Codex skill pack for me from GitHub and finish the setup.

Working brief:
- Goal: clone the repository, install the skill pack into Codex home, verify the install, and tell me whether everything is fully working.
- Repository: https://github.com/UntaDotMy/codex_skills.git
- Constraints: use the repo-managed install entrypoints only, keep changes surgical, and respect the current platform path detection or `CODEX_TARGET_OVERRIDE` if I provide it.

Required flow:
1. Clone the repo with `git clone https://github.com/UntaDotMy/codex_skills.git` if it is not already present.
2. Change into the repository root.
3. Read `README.md` and `AGENTS.md` first.
4. On Windows, prefer the PowerShell wrapper. Run `./sync-skills.ps1 validate`, `./sync-skills.ps1 install`, and `./sync-skills.ps1 status`. If PowerShell script execution is blocked, rerun the same commands with `powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 <command>`.
5. On macOS/Linux, run `./sync-skills.sh validate`, `./sync-skills.sh install`, and `./sync-skills.sh status`.
6. Tell me whether repo version, installed version, memory-status-reporter wiring, agent inheritance, and MD5 verification all pass.

If anything fails:
- identify the exact failing step,
- fix only the root cause,
- rerun the minimum necessary validation,
- then rerun `install` and `status`.
```

### Manual Install

#### macOS and Linux

```bash
git clone https://github.com/UntaDotMy/codex_skills.git
cd codex_skills
./sync-skills.sh validate
./sync-skills.sh install
./sync-skills.sh status
```

#### Windows PowerShell

```powershell
git clone https://github.com/UntaDotMy/codex_skills.git
Set-Location codex_skills
./sync-skills.ps1 validate
./sync-skills.ps1 install
./sync-skills.ps1 status
```

If your PowerShell execution policy blocks local scripts, use this fallback:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 validate
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 install
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 status
```

### Start Using It

After installation, you can immediately use the manager and verification flow:

```bash
./sync-skills.sh menu
./sync-skills.sh verify
./sync-skills.sh status
```

On Windows PowerShell, use the wrapper:

```powershell
./sync-skills.ps1 menu
./sync-skills.ps1 verify
./sync-skills.ps1 status
```

### Requirements

- Codex CLI with `js_repl`, `memories`, and `multi_agent` enabled
- Python 3 for memory-report tooling and sync helpers, available as `python`, `python3`, or `py -3`
- Git Bash on Windows for the Bash runner; `sync-skills.ps1` locates it for you

## Setup Reference

### Interactive Manager

Use the same script in interactive mode when you want install, sync, update, remove, verify, and status in one menu:

```bash
./sync-skills.sh menu
```

On Windows PowerShell:

```powershell
./sync-skills.ps1 menu
```

The interactive manager now handles all of the following in one place:

- install the full repo-managed skill pack
- force-sync the skill pack
- detect drift with MD5 and apply only the required repo-managed changes
- remove one installed skill or the full repo-managed pack
- verify copied files with MD5 checksums
- detect repo and installed versions
- detect stale or old installed files before refresh
- prune repo-managed skills that were removed from the source repository

## Directory Structure

```text
codex_skills/
├── AGENTS.md
├── 00-skill-routing-and-escalation.md
├── README.md
├── VALIDATION_REPORT.md
├── sync-skills.ps1
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

### Use the UI Design-Intelligence Generator

After sync, you can generate a local design packet directly from the skill pack:

```bash
python3 ~/.codex/skills/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "fintech banking dashboard with secure transfers"
```

Make the recommendation match your real stack and component system:

```bash
python3 ~/.codex/skills/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py \
  "AI workspace for research copilots" \
  --stack nextjs \
  --component-library shadcn \
  --format json
```

Persist a reusable design system safely:

```bash
python3 ~/.codex/skills/ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py \
  "ecommerce checkout optimization" \
  --persist \
  --project-name "Storefront Revamp" \
  --page "Checkout Flow"
```

The sync does all of the following:

- copies root skills into `~/.codex/skills/`
- copies `AGENTS.md` and `00-skill-routing-and-escalation.md` into `~/.codex/`
- refreshes `~/.codex/agents/*.toml` from each root `agents/openai.yaml`
- keeps repo-managed skill agents inheriting the workspace model and reasoning baseline instead of pinning per-skill model overrides
- keeps `~/.codex/config.toml` wired for `memory-status-reporter`
- writes install metadata with the current repo version
- tracks the repo-managed installed skill set for update and uninstall safety
- compares source and installed files with MD5 checksums after sync
- verifies the managed install surface only: `SKILL.md`, `references/`, `scripts/`, `data/`, `agents/`, `templates/`, `examples/`, and `assets/`
- applies delta updates by refreshing changed repo-managed skills, updating changed root guidance files, and pruning repo-managed skills that disappeared from the source tree
- injects shared execution-policy lines for working briefs, context efficiency, modular structure, surgical patches, compact learning snapshots, and freshness-aware research reuse

### macOS and Linux

Codex home: `~/.codex`

### Windows

The sync script detects Windows shells and maps Codex home to `%USERPROFILE%\\.codex`. In Git Bash this usually appears as `/c/Users/<user>/.codex`.

For interactive Windows use outside Codex runtime, prefer the PowerShell wrapper:

```powershell
./sync-skills.ps1 install
./sync-skills.ps1 update
./sync-skills.ps1 uninstall
```

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
- persist reusable research findings in a freshness-aware cache so future tasks can skip redundant research when prior findings are still valid

## Memory Growth Reporting

The memory workflow is intentionally human-style, but still evidence-bound.

### Memory Layers

- **Working memory** — the current working brief, active files, and validation target
- **Episodic memory** — rollout summaries and recent task evidence
- **Durable memory** — indexed learnings and recurring user preferences in `~/.codex/memories/MEMORY.md` and `~/.codex/memories/memory_summary.md`
- **Research cache** — reusable source-backed findings with freshness notes so future work can research only what is new
- **Reinforcement memory** — rewarded patterns that worked and penalty patterns that future work should avoid or refresh

### Reward, Penalty, and Research Reuse

Use the memory system like a compact engineering learning loop:

- promote validated wins into rewarded patterns when an approach worked and was verified
- promote repeated mistakes, disproven assumptions, or stale findings into penalty patterns
- save research findings when they answer a reusable question with enough confidence and source evidence
- refresh only the findings that are date-sensitive, version-sensitive, or disproven by newer evidence

This keeps the system from re-researching the same solved question on every task while still forcing a loop back to live research when cached knowledge is stale or uncertain.

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
./sync-skills.sh update
./sync-skills.sh verify
./sync-skills.sh status
```

The update command is a repo-managed delta update. It refreshes only changed skills and root files, then removes repo-managed skills that disappeared from the source tree.

### Uninstall Skills

```bash
./sync-skills.sh uninstall
```

To remove one installed skill only:

```bash
./sync-skills.sh uninstall reviewer
```

On Windows PowerShell, use:

```powershell
./sync-skills.ps1 uninstall
./sync-skills.ps1 uninstall reviewer
```

If you want to test against a temporary Codex home without touching your real `~/.codex`, use:

```bash
CODEX_TARGET_OVERRIDE=/tmp/test-codex-home ./sync-skills.sh install
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
- source-vs-installed MD5 parity for the copied managed skill files after sync or install
- stale repo-managed installed skills that should be pruned by update or uninstall

## Troubleshooting

### Sync says config is partial

Run:

```bash
./sync-skills.sh codex
./sync-skills.sh status
```

Then verify `~/.codex/config.toml` contains the `memory-status-reporter` route line, the `memory-status-reporter` agent block, and the injected execution-policy lines for working briefs, context retrieval, surgical patching, modular structure, and learning snapshots.

Also verify `./sync-skills.sh status` reports full agent inheritance unless you intentionally added your own local overrides. In the current repo policy, repo-managed skill agents inherit the workspace model and reasoning baseline, while built-in runtime roles such as `explorer`, `reviewer`, `worker`, and `architect` still depend on runtime model-selection support.

### Windows install fails looking for `python3`

The installer now probes `python3`, `python`, and `py -3` before editing Codex home. If install still fails, verify at least one of these commands launches Python 3 successfully from the same shell session.

### Memory footer looks thin

That usually means the current memory window is quiet or the rollout summaries did not capture reusable learnings or mistakes. The system should say that directly instead of fabricating certainty.

## Related Docs

- `docs/context-efficiency-playbook.md`
- `AGENTS.md`
- `00-skill-routing-and-escalation.md`
- `VALIDATION_REPORT.md`

## License

These skills are intended for personal or team use with Codex CLI.
