# Security Audit Status

## Purpose

This file is the honest security-status artifact for the current governance pass. It separates what the repo truly proves today from claims that would require a formal audit bundle.

## Verified On 2026-03-11

The current workspace evidence for this repo includes:

- Contract coverage passed with `python -m unittest tests.test_skill_pack_contracts`.
- Bash manager validation passed with `bash ./sync-skills.sh validate`.
- Windows wrapper validation is expected to pass through `powershell -ExecutionPolicy Bypass -File .\sync-skills.ps1 validate` when Git Bash is available on the host.
- Static grep found no current uses of `shell=True`, `os.system(...)`, `Invoke-Expression`, or pipe-to-shell patterns such as `curl | sh` in the repo-managed code.

## What Is Implemented

- Prompt-injection and external-content-as-data guardrails are documented in `AGENTS.md`, `README.md`, and `docs/runtime-guardrails-and-memory-protocols.md`.
- Cross-platform launcher handling exists in Python helpers plus the Bash and PowerShell entrypoints.
- The PowerShell wrapper probes common absolute Git Bash install paths instead of relying on a single PATH lookup.
- The repo includes contract tests that enforce the presence of WAL, anti-loop, scoped memory, research-cache reuse, bounded handoffs, and cross-platform guidance.

## What Is Not Yet Proven

- The repo does **not** currently ship a source-backed penetration-test artifact that proves a public score such as `94/100` or `97 after fixes`.
- The repo does **not** currently ship an archived machine-readable audit report that names the scanner, version, date, findings, and closure evidence.
- The specific historical findings "Python heredoc variable interpolation", "TOCTOU race condition in backup creation", and "PATH-dependent binary resolution" are not all present today as a preserved audit narrative with linked fixes and regression tests, so they should not be claimed as completed evidence unless that artifact is added.

## Release Bar For Future Security Claims

Before publishing a numeric score or a named findings list, add a durable audit bundle that includes:

- tool or agent name and version
- audit date and target revision
- exact finding list with severity
- linked remediation commits or file references
- regression validation that proves each fix stayed closed

Until that bundle exists, treat security posture as **partially implemented but not fully proven**.
