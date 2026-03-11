# Codex Skills Repository

This repository is a Codex-first skill pack for OpenAI Codex CLI. It ships specialist skills, repo-wide orchestration guidance, sync tooling for `~/.codex`, and a memory-status workflow that turns saved artifacts into human-style learning reports.

## Quick Start

### One-File Install

You do not need to manually clone the whole repo first anymore.

Download just the existing entry script for your platform and run it. If the full repo is not present yet, the script now stages a fresh temporary clone for that run, refreshes the local entry script when a newer `sync-skills` file is available, restarts into the refreshed file, and then continues with the normal install, menu, update, and status flows. The temporary staged repo is deleted after the run unless you explicitly set `CODEX_SKILLS_REPOSITORY_PATH`.

#### macOS and Linux

```bash
curl -fsSL https://raw.githubusercontent.com/UntaDotMy/codex_skills/main/sync-skills.sh -o sync-skills.sh
bash ./sync-skills.sh
bash ./sync-skills.sh status
```

Keep using the same file after that:

```bash
bash ./sync-skills.sh
bash ./sync-skills.sh update
```

The one-file bootstrap copy now refreshes itself from the latest staged repo whenever it is writable, so the downloaded entry script does not stay stale after later repo updates. By default the staged repo is temporary and deleted after the run.

#### Windows PowerShell

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/UntaDotMy/codex_skills/main/sync-skills.ps1 -OutFile .\sync-skills.ps1
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 status
```

`sync-skills.ps1` is a Windows wrapper around the same Bash manager, so Install, Update, Status, and the interactive menu stay aligned with `sync-skills.sh`. It requires Git Bash on Windows and probes the common Git for Windows install paths for you.

Keep using the same file after that:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 update
```

The one-file bootstrap copy now refreshes itself from the latest staged repo whenever it is writable, so the downloaded entry script does not stay stale after later repo updates. By default the staged repo is temporary and deleted after the run.

Bootstrap environment overrides:

- `CODEX_SKILLS_REPOSITORY_PATH` — use an explicit repo path for the bootstrap flow instead of a fresh temporary staged clone
- `CODEX_SKILLS_REPOSITORY_URL` — point the bootstrap flow at your fork or a local test repo
- `CODEX_SKILLS_REPOSITORY_BRANCH` — clone a non-`main` branch
- `CODEX_TARGET_OVERRIDE` — install into a different Codex home target


### AI-Assisted Install

If you want Codex to install this for you, copy and paste this prompt into a Codex session:

```text
Please install this Codex skill pack for me from GitHub and finish the setup.

Working brief:
- Goal: clone the repository, install the skill pack into Codex home, verify the install, and tell me whether everything is fully working.
- Repository: https://github.com/UntaDotMy/codex_skills.git
- Constraints: use the repo-managed install entrypoints only, keep changes surgical, and respect the current platform path detection or `CODEX_TARGET_OVERRIDE` if I provide it.

Required flow:
1. Read `README.md` and `AGENTS.md` first.
2. If the full repo is not already present locally, bootstrap it from the existing entry script only:
   - macOS/Linux: download `sync-skills.sh`, then run `bash ./sync-skills.sh install`
   - Windows: download `sync-skills.ps1`, then run `powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 install`
3. If the repo is already present, use the normal repo-managed `sync-skills.sh` or `sync-skills.ps1` entrypoint there.
4. After install, run `status`.
5. Tell me whether repo version, installed version, memory-status-reporter wiring, agent inheritance, and MD5 verification all pass.

If anything fails:
- identify the exact failing step,
- fix only the root cause,
- rerun the minimum necessary validation,
- then rerun `install` and `status`.
```

### Manual Install

If you want the simplest path, use the one-file install above.

If you prefer to keep the full repository in a directory you chose yourself, the manual clone flow still works:

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

After installation, you can immediately use the manager and the simple update/status flow:

```bash
bash ./sync-skills.sh menu
bash ./sync-skills.sh update
bash ./sync-skills.sh status
```

On Windows PowerShell, use the wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 menu
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 update
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 status
```

### Requirements

- Codex CLI with `js_repl`, `memories`, and `multi_agent` enabled
- Python 3 for memory-report tooling and sync helpers, available as `python`, `python3`, or `py -3`
- Git Bash on Windows for the Bash runner; `sync-skills.ps1` delegates to `sync-skills.sh` and locates common Git Bash installs for you

### Runtime Guardrails and Memory Maintenance

The skill pack now documents and supports:

- write-ahead session-state persistence with `SESSION-STATE.md` and `session-wal.jsonl`
- a scoped `working-buffer.md` for long tasks and context resets, activated around 60 percent context usage when the runtime exposes that signal
- L1 or L2 or L3 memory organization with one home per fact
- `trim` and `recalibrate` maintenance flows for scoped memory hygiene
- loop_guard.py for evidence-backed anti-loop checks when the same failure shape keeps repeating
- completion_gate.py for scoped requirement ledgers that block final closure until every explicit ask is done, while blocked items require an explicit blocker reason and still keep closure blocked
- anti-loop, prompt-injection, and external-content-as-data guardrails
- agent_packets.py for Octave-inspired non-MCP handoff packets, readiness checks, and manager-brokered agent feedback
- bounded self-awareness, self-healing, and self-learning loops grounded in memory maintenance, validation, and reward-or-penalty updates
- cross-platform Python maintenance tooling for Windows, Linux, and macOS

See [runtime-guardrails-and-memory-protocols.md](docs/runtime-guardrails-and-memory-protocols.md), [open-source-memory-patterns.md](docs/open-source-memory-patterns.md), [security-audit-status.md](docs/security-audit-status.md), and [context-efficiency-playbook.md](docs/context-efficiency-playbook.md).

## Setup Reference

### Interactive Manager

Use the same script in interactive mode when you want the simplest flow in one menu:

```bash
bash ./sync-skills.sh menu
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 menu
```

If you launched from a one-file bootstrap copy without `CODEX_SKILLS_REPOSITORY_PATH`, the script stages a fresh temporary repo for that run, refreshes the saved launcher when a newer `sync-skills` file is available, and deletes the staged repo after the run completes.

When the bootstrap file is writable, the staged repo also refreshes the downloaded entry script on later runs so your saved launcher stays aligned with the latest bootstrap logic before the staged repo is removed.

The interactive manager now keeps only four clear choices:

- Install: install the full repo-managed skill pack when missing, or refresh only the changed repo-managed files when it is already installed
- Update: check for repo or manager updates first, restart into the refreshed `sync-skills.sh` when that file changed, then update the installed skill pack
- Status: show manager version, self-update state, skill-pack update state, versions, wiring, and checksum drift
- Quit: leave the menu without side effects

### Update Behavior

`install` is now idempotent. If the pack is missing, it performs a full install. If the pack already exists, it applies only the needed repo-managed changes, including `AGENTS.md` and `00-skill-routing-and-escalation.md` when those changed.

`update` is now the single smart update path. It first checks the tracked Git remote when one is configured, fast-forwards the repo when it is behind, restarts into the refreshed `sync-skills.sh` if that manager script changed, and then syncs only the changed files into Codex home:

```bash
./sync-skills.sh update
```

```powershell
./sync-skills.ps1 update
```

The updater stays conservative about repo state:

- it fetches the tracked upstream or the remote default branch when Git metadata is available
- it only pulls with `--ff-only`
- it restarts into the refreshed manager when `sync-skills.sh` changed during that pull
- it still syncs the current local repo state into Codex home when the repo is already ahead, diverged, dirty, or remote metadata is unavailable
- it refreshes the external one-file launcher from the staged bootstrap repo when that launcher is writable

Legacy alias: `github-update` still maps to `update`, but the primary flow is now just `update`.

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

1. **software-development-life-cycle** - Architecture, planning, delivery, and cross-domain validation
2. **web-development-life-cycle** - Web implementation, browser/runtime quality
3. **mobile-development-life-cycle** - Mobile lifecycle, release, offline, platform behavior
4. **backend-and-data-architecture** - APIs, contracts, data flow, service integration
5. **cloud-and-devops-expert** - Infrastructure, CI/CD, release reliability, observability
6. **qa-and-automation-engineer** - Test strategy, regression coverage, automation
7. **security-and-compliance-auditor** - Threat modeling, secrets, remediation, compliance
8. **ui-design-systems-and-responsive-interfaces** - Design systems, accessibility, visual execution
9. **ux-research-and-experience-strategy** - UX framing, jobs-to-be-done, usability strategy
10. **git-expert** - Repository-state safety, branching, recovery, review handoff
11. **memory-status-reporter** - Daily learnings, mistake ledgers, tool-mistake tracking, and heuristic memory-health reporting
12. **reviewer** - Production readiness, quality gates, DRY enforcement, and final validation

When the task clearly belongs to one surface, route to that specialist first. `reviewer` is the quality gate, not the default implementation owner.

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
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 install
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 update
powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 uninstall
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
- check the research cache before Round 1 and skip redundant live research when the freshness notes already cover the task

## Memory Growth Reporting

The memory workflow is intentionally human-style, but still evidence-bound.

### Memory Layers

- **Working memory** — the current working brief, active files, and validation target
- **Workspace memory** — shared notes for the current repo or workstream under `~/.codex/memories/workspaces/<workspace-slug>/`
- **Workstream memory** — branch, feature-lane, or focused task notes under `~/.codex/memories/workspaces/<workspace-slug>/workstreams/<workstream-key>/`
- **Role memory** — role-local notes under `~/.codex/memories/agents/<role>/<workspace-slug>/workstreams/<workstream-key>/` so reused reviewer, worker, or architect agents can resume without replaying everything
- **Agent-instance memory** — one bounded note lane under `~/.codex/memories/agents/<role>/<workspace-slug>/workstreams/<workstream-key>/instances/<agent-instance>/` so a reused sub-agent keeps its own context instead of smearing it across every same-role lane
- **Episodic memory** — rollout summaries and recent task evidence
- **Durable memory** — indexed learnings and recurring user preferences in `~/.codex/memories/MEMORY.md` and `~/.codex/memories/memory_summary.md`
- **Research cache** — reusable source-backed findings with freshness notes in `~/.codex/memories/research_cache/<workspace-slug>/cache.jsonl` so future work can research only what is new
- **Reinforcement memory** — rewarded patterns that worked and penalty patterns that future work should avoid or refresh
- **Archive** — older or noisy material under `~/.codex/memories/archive/<workspace-slug>/workstreams/<workstream-key>/` after it has been superseded by fresher scoped notes

### Reward, Penalty, and Research Reuse

Use the memory system like a compact engineering learning loop:

- promote validated wins into rewarded patterns when an approach worked and was verified
- promote repeated mistakes, disproven assumptions, or stale findings into penalty patterns
- save research findings when they answer a reusable question with enough confidence and source evidence
- refresh only the findings that are date-sensitive, version-sensitive, or disproven by newer evidence

This keeps the system from re-researching the same solved question on every task while still forcing a loop back to live research when cached knowledge is stale or uncertain.

### Scoped Memory and Cache Helpers

Resolve the current workspace and optional role scope before loading memory broadly:

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/resolve_memory_scope.py --memory-base ~/.codex/memories --workspace-root "$PWD" --agent-role reviewer --workstream-key feature-review --agent-instance reviewer-lane-a --create-missing
```

Check or record reusable research without redoing the whole web loop:

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/research_cache.py lookup --memory-base ~/.codex/memories --workspace-root "$PWD" --workstream-key feature-review --query "your research question"
python3 ~/.codex/skills/memory-status-reporter/scripts/research_cache.py record --memory-base ~/.codex/memories --workspace-root "$PWD" --workstream-key feature-review --agent-role reviewer --agent-instance reviewer-lane-a --question "your research question" --answer "concise reusable answer" --source "https://example.com" --freshness "refresh when the API version changes"
python3 ~/.codex/skills/memory-status-reporter/scripts/research_cache.py archive-stale --memory-base ~/.codex/memories --workspace-root "$PWD" --workstream-key feature-review
```

The shared cache is workspace-scoped, while workstream, role, and agent-instance notes let reused sub-agents pick up the same workstream without a full transcript replay.

The repo now also ships memory-status-reporter/scripts/agent_registry.py so same-role lanes can be registered, looked up, listed, and marked unhealthy per workstream instead of relying on recall alone.

### Completion Reconciliation

Before any final answer, the active skill should reconcile every explicit user requirement against current evidence. That means re-reading the raw request, mapping each concrete ask to code or validation, looping back for any in-scope gap, and avoiding optional follow-up language when the user asked for completion. For non-trivial tasks, the repo now expects a scoped completion ledger in `completion-gate.json` maintained through `completion_gate.py`, and closure should not be claimed until `check` reports that every tracked requirement is done. If something is blocked, record the blocker explicitly and keep looping until it is resolved or honestly reported as the reason the work is still not complete. A progress, recap, audit, or "what is done or not done" request is not permission to stop if fixable in-scope work remains.

### Open-Source Pattern Notes

The current memory layout is intentionally aligned to live open-source patterns such as project-scoped memory, Mem0 multi-scope memory, and repoMemory branch or worktree isolation. See [docs/open-source-memory-patterns.md](./docs/open-source-memory-patterns.md) for the applied rules and source links.

### Security Audit Status

The repo now carries an honest status artifact instead of an uncited score claim. See [docs/security-audit-status.md](./docs/security-audit-status.md) for what is actually validated today, what is still only partial, and what evidence would be required before publishing a numeric security score.

### Compact Learning Snapshot

For non-trivial tasks, the repo guidance now supports a compact final-answer footer with:

- what Codex learned today
- mistakes and tool-use mistakes captured today
- whether they are resolved, open, or unclear
- heuristic memory-health stats such as brain size, brain growth, and momentum

These values are derived from saved artifacts. They are not literal cognition measurements.

### Run the Full Report

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories --workspace-root "$PWD"
```

### Run the Compact Footer Version

```bash
python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories --workspace-root "$PWD" --format compact
```

## Development Workflow

### Update Skills

```bash
./sync-skills.sh update
./sync-skills.sh verify
./sync-skills.sh status
```

The update command now checks for manager or repo updates first, restarts into the refreshed `sync-skills.sh` when needed, then refreshes only changed skills and root files and removes repo-managed skills that disappeared from the source tree.

If the repo-managed skill pack is not installed in the target Codex home yet, `update` boots into a full install automatically instead of failing with a partial-state error.

For advanced checksum-only troubleshooting, `./sync-skills.sh verify` is still available.

### Uninstall Skills

```bash
./sync-skills.sh uninstall
```

To remove one installed skill only:

```bash
./sync-skills.sh uninstall reviewer
```

`uninstall reviewer` removes that skill from the current Codex home immediately, but the next full-pack `install` or `update` restores any repo-managed skill that still exists in this repository. Use full-pack `uninstall` when you want the repo-managed install state to become fully absent.

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

### Update says the repo is dirty or diverged

`update` now keeps the workflow simple. If the repo is dirty, ahead, or diverged, it skips the remote self-update step and still syncs the current local repo state into Codex home. If you want the local repo itself to match upstream first, reconcile the Git state separately, then rerun `./sync-skills.sh update`. The legacy `github-update` alias still points to the same behavior.

### Memory footer looks thin

That usually means the current memory window is quiet or the rollout summaries did not capture reusable learnings or mistakes. The system should say that directly instead of fabricating certainty.

## Related Docs

- `docs/context-efficiency-playbook.md`
- `AGENTS.md`
- `00-skill-routing-and-escalation.md`
- `VALIDATION_REPORT.md`

## License

These skills are intended for personal or team use with Codex CLI.
