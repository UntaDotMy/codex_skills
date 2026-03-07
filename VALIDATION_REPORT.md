# Skills Validation Report

**Date**: 2026-03-07  
**Scope**: Codex-first audit of skill inventory, sync logic, repo guidance, and Claude mirror boundaries  
**Status**: ✅ PASS AFTER REMEDIATION

## Executive Summary

The live repository is structurally sound for Codex CLI. The first remediation pass fixed stale top-level documentation and non-Codex tool/profile names in `AGENTS.md`. The second pass deepened the expert skill pack itself: all 11 root Codex skills now ship supporting `references/` material, stronger production-focused prompts, and more explicit runtime, rollout, and real-world scenario guidance. The final cleanup pass removed leaked Codex-only `js_repl` runtime guidance from Claude mirror files, aligned the root Windows usage examples with Git Bash or `js_repl`-routed execution instead of PowerShell-wrapped quoting, and restored validator-backed parity between root skill docs and root agent prompts. The validator now protects that higher bar before future syncs.

## Live Inventory Snapshot

### Root Codex Skills (11)
1. `reviewer`
2. `software-development-life-cycle`
3. `web-development-life-cycle`
4. `mobile-development-life-cycle`
5. `backend-and-data-architecture`
6. `cloud-and-devops-expert`
7. `qa-and-automation-engineer`
8. `security-and-compliance-auditor`
9. `ui-design-systems-and-responsive-interfaces`
10. `ux-research-and-experience-strategy`
11. `git-expert`

### Claude Skills (8)
1. `reviewer`
2. `software-development-life-cycle`
3. `web-development-life-cycle`
4. `mobile-development-life-cycle`
5. `ui-design-systems-and-responsive-interfaces`
6. `ux-research-and-experience-strategy`
7. `git-expert`
8. `claude-api`

### Relationship Summary
- Shared skill names: `7`
- Codex-only skill names: `4`
- Claude-only skill names: `1`
- Total `SKILL.md` files in repo: `19`
- Total unique skill names in repo: `12`

## What Was Verified

### Codex Wiring
- All `11` root Codex skill directories contain `SKILL.md`
- All `11` root Codex skill directories contain `agents/openai.yaml`
- All `11` root Codex skill directories now contain `references/`
- Root Codex skills remain free of Claude-only `allowed-tools` metadata
- The root routing document already reflects the live `11`-skill inventory

### Claude Separation
- Claude skills live only under `claude/`
- Claude skills do not carry `agents/` directories
- Claude keeps the `claude-api` specialization isolated from the root Codex tree
- Claude mirrors are a deliberate subset, not a broken sync

### Sync Logic
- `sync-skills.sh` is count-agnostic for both trees
- Validation loops enumerate root skills dynamically and skip only `claude/`
- Status output computes counts dynamically instead of hardcoding them
- Existing sync logic already supports the live `11` Codex / `8` Claude inventory

## Gaps Found In This Audit

### Corrected
- `AGENTS.md` used legacy non-Codex runtime names that were removed during remediation
- `README.md` described the repo too broadly while omitting the four Codex-only specialist skills
- `claude/README.md` did not clearly explain that the Claude tree is only a subset of the root Codex inventory
- The previous `VALIDATION_REPORT.md` still described the obsolete `7`-skill Codex snapshot

### Hardening Added
- `sync-skills.sh` now validates repo-level Codex guidance files in addition to skill directories
- Codex guidance validation now rejects non-Codex tool/profile names before sync
- Codex skill validation now rejects those same invalid runtime references inside root `SKILL.md` files
- Codex skill validation now requires expert skills to ship supporting `references/` material
- The thin specialist skills were expanded into evidence-first playbooks with real-world scenarios, release blockers, runtime boundaries, and stronger agent prompts
- Claude mirror validation now catches leaked Codex-only runtime guidance before sync
- Root Windows usage docs now prefer Git Bash directly or `js_repl` + `codex.tool("exec_command", ...)` instead of PowerShell-wrapped examples
- Root Codex `SKILL.md` files now mirror the `js_repl` + `codex.tool(...)` runtime rule carried by their paired agent prompts
- Codex agent validation now requires same-role sub-agent reuse guidance plus `fork_context` default-off wording
- Root Codex `SKILL.md` files now mirror required sub-agent completion, no-early-close, spawned-agent tracking, and robust delegation-packet guidance
- Codex guidance validation now uses a safer legacy-runtime matcher, and root skill validation now checks sub-agent lifecycle policy in both docs and prompts

## Validation Commands

Run from `D:\Nasri\Project\codex_skills`:

```bash
./sync-skills.sh validate
./sync-skills.sh status
```

Optional Codex sync:

```bash
./sync-skills.sh codex
```

## Current Conclusion

- Codex inventory: accurate and complete at `11` skills
- Claude inventory: accurate and isolated at `8` skills
- Shared/mirrored skill split: intentional, not accidental
- Primary risk area before remediation: stale repo guidance, not missing skill wiring
- Current repo state: aligned for Codex-first usage and safe to validate/sync
