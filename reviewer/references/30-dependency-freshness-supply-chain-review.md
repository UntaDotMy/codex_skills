# Dependency Freshness and Supply-Chain Review

## Objective

Prevent stale or risky dependencies from entering PRDs or production plans.

## Review Checklist

For each dependency referenced in code or PRD:

1. Version is verified from current official source (not memory).
2. Compatibility with runtime/framework version is confirmed.
3. Maintenance activity and release recency are acceptable.
4. Known security advisories are checked.
5. Versioning strategy (pin/range) is justified.

## Web-First Verification Rule

Always verify with current sources:

- Official package registry/docs
- Official release notes/changelogs
- Security advisory databases

If verification evidence is missing, mark as Major by default.

## Typical Ecosystem Checks

- npm: `npm outdated`, `npm audit`, registry package page.
- Python: `pip index versions`, `pip-audit`, PyPI package page.
- Go: `go list -m -u all`, module tags and release notes.
- Rust: `cargo audit`, crates.io metadata and advisories.
- .NET/NuGet: vulnerability audit in `dotnet package list --vulnerable` and NuGet advisories.
- Java ecosystem: OWASP Dependency-Check (Maven/Gradle) or equivalent SCA tooling.

## High/Critical Vulnerability Remediation Flow

1. Confirm vulnerable package is in active runtime path (not only dev/test transitive where truly non-shipping).
2. Apply safest compatible update first (patch/minor and lockfile refresh).
3. Re-run advisory scan and full tests.
4. If unresolved:
   - evaluate direct dependency replacement or upgrade path
   - document migration impact
5. Only use forceful upgrade modes when necessary (for example `npm audit fix --force`):
   - review SemVer-major changes
   - run full regression/integration tests
   - report risk and rollback plan
6. If no safe fix is currently available, require explicit risk acceptance and compensating controls.

## Reporting Format

For each high-risk dependency finding, include:

- Current used version
- Recommended version/range
- Compatibility note
- Source/evidence URL
- Migration risk and validation steps
