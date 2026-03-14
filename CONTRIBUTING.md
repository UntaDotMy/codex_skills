# Contributing

## Purpose

This repository is a managed Codex skill pack, not a loose prompt collection. Contributions should preserve the same production-readiness standard across code, docs, tests, generated home wiring, and validation behavior.

## Contribution Workflow

1. Start from a concrete working brief.
2. Preserve one top-level plan item per explicit user task.
3. Keep the first implementation pass anchored to the named scope.
4. Prefer small validated batches over large rewrites.
5. Patch the source doctrine, validator, and contract coverage together when a rule is meant to fail closed.
6. Update README or supporting docs when user-facing behavior changes.
7. Run the proving loop before asking for review.

## Required Validation

Run this default loop from the repository root against a temporary Codex home target:

```bash
temporary_codex_home="$(mktemp -d)"
CODEX_TARGET_OVERRIDE="$temporary_codex_home" ./sync-skills.sh validate
CODEX_TARGET_OVERRIDE="$temporary_codex_home" ./sync-skills.sh install
CODEX_TARGET_OVERRIDE="$temporary_codex_home" ./sync-skills.sh verify
CODEX_TARGET_OVERRIDE="$temporary_codex_home" ./sync-skills.sh status
```

Windows PowerShell contributors should run the equivalent wrapper flow:

```powershell
$temporaryCodexHome = Join-Path $env:TEMP "codex-skills-test-home"
New-Item -ItemType Directory -Force -Path $temporaryCodexHome | Out-Null
$env:CODEX_TARGET_OVERRIDE = $temporaryCodexHome
./sync-skills.ps1 validate
./sync-skills.ps1 install
./sync-skills.ps1 verify
./sync-skills.ps1 status
```

Use the live `~/.codex` target only as an intentional final check when the change specifically needs that real-home proof.

When the change touches a narrower surface, also run the smallest direct proof that covers the edited area, such as a targeted `python3 -m unittest ...` command.

## Scope Rules

- Do not add parallel install or update entrypoints when the managed ones can absorb the change.
- Do not add new helper functions when existing code already owns the behavior cleanly.
- Do not present partial implementation as complete.
- Do not weaken runtime-safe clarification, live-research-first behavior, completion discipline, or memory-safety rules.

## Documentation Rules

- Keep committed comments and docs professional, concise, and neutral.
- Use README for end-user setup, architecture, and operational workflow.
- Use AGENTS.md and skill docs for agent doctrine, not marketing copy.
- Keep SECURITY.md current when the reporting path or validated security posture changes.

## Review Expectations

- Findings-first review for bugs, regressions, missing validation, or misleading docs
- Honest status labels for what is verified, inferred, skipped, or blocked
- Root-cause fixes over workaround-only patches

## Cross-Platform Expectations

- macOS, Linux, and Windows behavior should stay aligned
- `sync-skills.ps1` remains a supported wrapper path
- repo-managed Python helpers must stay portable across the three supported operating systems
