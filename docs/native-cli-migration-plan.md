# Native CLI Migration Plan

## Purpose

This document defines the concrete native command contract for replacing the current shell-plus-Python operational surface with one Go binary that users can run directly on Windows, Linux, and macOS without installing Python or Go locally.

## User Story

Users should be able to run the codex skill-pack manager and memory tooling directly:

- without installing Python
- without installing Go
- without learning different command shapes per platform
- with a stable command surface that Codex can reference deterministically
- with thin Windows and Unix wrappers that only bootstrap or delegate to the native binary

## Desired Outcome

The repo ships one canonical CLI surface:

- codex-skills

The binary owns:

- install, update, status, validate, verify, and uninstall flows
- bootstrap temp handling and cleanup
- repo-managed file sync and verification
- memory tooling currently implemented in Python scripts
- design-intelligence generation
- contract-test runner orchestration

The wrappers remain:

- sync-skills.ps1
- sync-skills.sh

but they become thin launchers that resolve and execute the native binary instead of owning business logic.

## Non-Goals

- Rewriting every skill payload or prompt in the first migration pass
- Preserving Python as a runtime prerequisite for end users
- Compiling Go source on the user machine during ordinary install unless the user explicitly chooses a developer build path

## Constraints

- Windows, Linux, and macOS must stay supported
- The current repo-managed install lifecycle must remain recognizable:
  - install when missing
  - refresh when installed
  - update with manager restart semantics when the manager changes
  - status, validate, verify, and uninstall remain available
- Current scoped-memory semantics must survive the rewrite
- Temp bootstrap directories must still be deleted on normal success and failure paths
- Wrappers must stay simple enough that parser or shell drift does not become the new bottleneck

## Canonical Binary

The canonical executable should be named:

- codex-skills

Optional compatibility alias:

- codex-skill-manager

Rationale:

- codex-skills matches the broader scope better than sync-skills
- it covers pack management plus memory and design utilities
- Codex can use one exact command name across platforms

## Public Command Contract

### Top-Level Commands

These are the only commands Codex should need to know by default:

    codex-skills install
    codex-skills all
    codex-skills update
    codex-skills status
    codex-skills validate
    codex-skills verify
    codex-skills verify <skill>
    codex-skills uninstall
    codex-skills uninstall <skill>
    codex-skills menu
    codex-skills version

### Native Utility Groups

These replace the current Python helper CLIs:

    codex-skills memory scope resolve
    codex-skills memory report
    codex-skills memory maintenance write-session-state
    codex-skills memory maintenance append-working-buffer
    codex-skills memory maintenance trim
    codex-skills memory maintenance recalibrate
    codex-skills memory research-cache lookup
    codex-skills memory research-cache record
    codex-skills memory research-cache mark-stale
    codex-skills memory research-cache reward
    codex-skills memory research-cache archive-stale
    codex-skills memory completion-gate record-requirement
    codex-skills memory completion-gate check
    codex-skills memory completion-gate list
    codex-skills memory agent-registry register
    codex-skills memory agent-registry lookup
    codex-skills memory agent-registry list
    codex-skills memory agent-registry set-status
    codex-skills memory agent-registry mark-unhealthy
    codex-skills memory agent-packets build-handoff
    codex-skills memory agent-packets build-feedback
    codex-skills memory agent-packets build-readiness-check
    codex-skills memory loop-guard check
    codex-skills memory loop-guard record-failure
    codex-skills memory loop-guard resolve
    codex-skills design-intelligence recommend
    codex-skills contracts run
    codex-skills contracts list-targets

### Compatibility Aliases

To reduce migration churn, the native CLI should accept these aliases:

- codex-skills remove as an alias for codex-skills uninstall
- codex-skills sync and codex-skills codex as aliases for codex-skills install
- codex-skills all as an alias for validate then install
- codex-skills github-update, codex-skills gu, and codex-skills upgrade as aliases for codex-skills update
- codex-skills memory completion-gate record as an alias for codex-skills memory completion-gate record-requirement
- codex-skills memory agent-packets handoff as an alias for codex-skills memory agent-packets build-handoff
- codex-skills memory agent-packets feedback as an alias for codex-skills memory agent-packets build-feedback
- codex-skills memory agent-packets readiness-check as an alias for codex-skills memory agent-packets build-readiness-check
- codex-skills memory loop-guard record as an alias for codex-skills memory loop-guard record-failure

## Wrapper Contract

### Windows

sync-skills.ps1 should only do this:

1. detect platform and architecture
2. preserve the one-file bootstrap behavior when the repo layout is not complete
3. honor CODEX_SKILLS_REPOSITORY_PATH, CODEX_SKILLS_REPOSITORY_URL, and CODEX_SKILLS_REPOSITORY_BRANCH when the user wants a repo-sourced run
4. refresh a stale standalone launcher from a staged source when newer launcher content is available
5. resolve the cached or bundled codex-skills.exe for the release-managed path
6. download the correct release asset if the binary is missing in release-managed mode
7. launch codex-skills.exe with the same arguments
8. keep the simple interactive menu when no explicit arguments are supplied
9. clean up bootstrap staging artifacts on normal success and failure paths

It should not:

- own the main install logic
- reimplement sync behavior
- depend on Git Bash once the native CLI is live

### Linux and macOS

sync-skills.sh should only do this:

1. detect platform and architecture
2. preserve the one-file bootstrap behavior when the repo layout is not complete
3. honor CODEX_SKILLS_REPOSITORY_PATH, CODEX_SKILLS_REPOSITORY_URL, and CODEX_SKILLS_REPOSITORY_BRANCH for repo-sourced runs
4. refresh a stale standalone launcher from a staged source when newer launcher content is available
5. resolve the cached or bundled codex-skills binary for the release-managed path
6. download the correct release asset if the binary is missing in release-managed mode
7. execute the binary with the original arguments
8. keep the current menu behavior when launched with no arguments
9. clean up bootstrap staging artifacts on normal success and failure paths

It should not:

- own the main install logic
- call Python helpers directly
- retain heavy file-sync logic after the migration is complete

## Distribution Model

End users should not be expected to install Go.

The distribution model should be:

1. CI builds native binaries for supported targets
2. release assets are published per OS and architecture
3. wrappers fetch the matching asset on first run if it is not already cached in release-managed mode
4. the binary is cached under the user Codex home
5. local checkout mode remains available for developers and fork-based installs
6. later runs execute the cached binary directly in release-managed mode or the repo-selected binary in local-checkout mode

Recommended cache layout:

    ~/.codex/.codex-skill-manager/bin/<version>/<platform>-<arch>/codex-skills[.exe]

Recommended release targets:

- windows-amd64
- windows-arm64
- linux-amd64
- linux-arm64
- darwin-amd64
- darwin-arm64

Optional:

- a macOS universal binary

## Direct-Use Command for Codex

Codex should treat codex-skills as the canonical public command.

Examples:

    codex-skills install
    codex-skills update
    codex-skills status
    codex-skills validate
    codex-skills verify
    codex-skills memory report --workspace-root <path>
    codex-skills memory completion-gate check --workspace-root <path> --workstream-key <key>
    codex-skills design-intelligence recommend "<query>"

During transition, wrappers remain valid:

- ./sync-skills.sh install
- powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 install

but Codex-facing docs should gradually move to codex-skills.

## Update Modes

The native contract needs two explicit update modes so the current repo-driven workflow is not lost.

### Release-Managed Mode

Default behavior when no repo source is specified:

- wrapper resolves or downloads the correct release binary
- codex-skills update updates the installed pack from release-managed assets
- binary self-update may replace the cached version before continuing

### Local-Checkout Mode

Used when the user wants the current local repo or fork to remain the source of truth.

The native CLI should support:

- --repo-root <path>
- CODEX_SKILLS_REPOSITORY_PATH
- CODEX_SKILLS_REPOSITORY_URL
- CODEX_SKILLS_REPOSITORY_BRANCH

Behavior in local-checkout mode should preserve today's semantics:

- use the selected repo as the sync source
- fast-forward the tracked remote when configured and safe to do so
- restart into the refreshed manager binary when the manager changed during that fetch or pull
- keep syncing the current local repo state when the repo is ahead, dirty, diverged, or missing remote metadata

Codex should prefer local-checkout mode automatically when the command is launched from a full codex_skills repo or when the repo path override is already set.

## Mapping From Current Surfaces

### Current Shell Manager to Native CLI

| Current Surface | Native Replacement |
|---|---|
| sync-skills.sh install | codex-skills install |
| sync-skills.sh all | codex-skills all |
| sync-skills.sh update | codex-skills update |
| sync-skills.sh status | codex-skills status |
| sync-skills.sh validate | codex-skills validate |
| sync-skills.sh verify | codex-skills verify |
| sync-skills.sh verify <skill> | codex-skills verify <skill> |
| sync-skills.sh remove or uninstall | codex-skills uninstall |
| sync-skills.sh remove <skill> or uninstall <skill> | codex-skills uninstall <skill> |
| sync-skills.sh menu | codex-skills menu |
| sync-skills.ps1 same commands | same native commands through the PowerShell wrapper |

### Current Python Scripts to Native CLI

| Current Script | Current Shape | Native Replacement |
|---|---|---|
| memory-status-reporter/scripts/resolve_memory_scope.py | direct CLI with flags | codex-skills memory scope resolve |
| memory-status-reporter/scripts/memory_status_report.py | direct CLI with flags | codex-skills memory report |
| memory-status-reporter/scripts/memory_maintenance.py | write-session-state, append-working-buffer, trim, recalibrate | codex-skills memory maintenance <subcommand> |
| memory-status-reporter/scripts/research_cache.py | lookup, record, mark-stale, reward, archive-stale | codex-skills memory research-cache <subcommand> |
| memory-status-reporter/scripts/completion_gate.py | record-requirement, check, list | codex-skills memory completion-gate <subcommand> |
| memory-status-reporter/scripts/agent_registry.py | register, lookup, list, set-status, mark-unhealthy | codex-skills memory agent-registry <subcommand> |
| memory-status-reporter/scripts/agent_packets.py | build-handoff, build-feedback, build-readiness-check | codex-skills memory agent-packets <subcommand> |
| memory-status-reporter/scripts/loop_guard.py | check, record-failure, resolve | codex-skills memory loop-guard <subcommand> |
| ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py | direct CLI with query plus flags | codex-skills design-intelligence recommend |
| tests/parallel_contract_test_runner.py | run or --list-targets | codex-skills contracts run or codex-skills contracts list-targets |

## Flag Preservation Rule

The first native pass should preserve the current flag names wherever practical.

Examples:

- --memory-base
- --workspace-root
- --workstream-key
- --agent-instance
- --format
- --query
- --question
- --answer
- --freshness
- --requirement-id
- --status
- --evidence
- --workflow-name
- --objective
- --constraint
- --relevant-file

This reduces migration churn in:

- docs
- tests
- AGENTS and skill prompts
- Codex-facing examples

## Bootstrap and Temp Cleanup

The native binary should own temp lifecycle for:

- bootstrap clone or release extraction directories
- update staging directories
- verification scratch files

Rules:

- use OS-native temp directories
- delete temp artifacts on normal success
- delete temp artifacts on normal failure
- only keep persistent files when the user explicitly chose a persistent repo or cache location

The wrappers should only clean up their own tiny launcher scratch files if they create any. The binary should clean up the operational temp directories it owns.

## Verification Strategy

The native binary should keep the current split:

- fast install or update verification
- full deep verification when explicitly requested

Fast verification should remain:

- direct file compare for root guidance
- direct file compare for generated agent profiles
- directory diff for managed skill drift
- inventory verification
- memory wiring verification
- runtime hygiene verification

Full verification may still keep deeper content auditing if needed, but it should not be the default on the user install path.

## Suggested Go Package Layout

    cmd/
      codex-skills/
        main.go
    internal/
      app/
      bootstrap/
      platform/
      releaseassets/
      manager/
      syncengine/
      verification/
      inventory/
      memory/
        scope/
        report/
        maintenance/
        researchcache/
        completiongate/
        agentregistry/
        agentpackets/
        loopguard/
      designintelligence/
      contracts/

## Suggested Migration Phases

### Phase 1: Native Manager Core

Deliver:

- install
- all
- update
- status
- validate
- verify
- verify <skill>
- uninstall
- uninstall <skill>
- native bootstrap and release-asset resolution

Also preserve:

- launcher self-refresh from staged source
- repo path, repo URL, and repo branch bootstrap overrides
- release-managed and local-checkout update modes

Keep Python and shell helper docs temporarily, but stop using Python in the main install path.

### Phase 2: Memory Tooling

Replace:

- resolve_memory_scope.py
- memory_status_report.py
- memory_maintenance.py
- research_cache.py
- completion_gate.py
- agent_registry.py
- agent_packets.py
- loop_guard.py

At this point, end-user runtime should no longer depend on Python for pack operations or memory workflows.

### Phase 3: Design and Contract Utilities

Replace:

- design_intelligence.py
- parallel_contract_test_runner.py

### Phase 4: Wrapper Simplification

Reduce sync-skills.ps1 and sync-skills.sh to:

- preserve bootstrap override handling and stale-launcher recovery
- choose release-managed or local-checkout mode explicitly
- resolve cached binary or selected repo binary
- fetch release asset if missing in release-managed mode
- exec the native CLI

## Acceptance Criteria

The migration is complete when:

- users can run the manager and memory tools without Python
- users do not need Go installed because release binaries are shipped
- Codex can rely on codex-skills as the canonical command name
- wrappers remain cross-platform and thin
- install and update stay faster than the current shell-plus-Python path
- temp bootstrap and staging artifacts are cleaned on normal success and failure paths
- docs and tests point at the native command contract rather than the old Python commands

## External References

These official sources support the distribution model:

- Go go build and go install: https://go.dev/doc/tutorial/compile-install
- Go installation guidance: https://go.dev/doc/install
- Go source-install note that most users should use precompiled binaries: https://go.dev/doc/install/source
- Go cross-compiling guidance: https://go.dev/wiki/WindowsCrossCompiling
- GoReleaser Go builds: https://goreleaser.com/customization/builds/go/
- GoReleaser macOS universal binaries: https://goreleaser.com/customization/universalbinaries/
