# Testing, Release, and Production-Readiness Review

## Testing Completeness

Validate:

- Unit tests cover critical logic and failure paths.
- Integration tests cover boundary contracts.
- End-to-end/system tests cover critical user journeys.
- Regression tests exist for known defect classes.
- Coverage discussion includes known blind spots.

## CI/CD and Quality Gates

Require evidence for:

- Build, lint/static analysis, and test pass status
- Security/dependency scans
- Migration safety checks where applicable
- Environment promotion strategy
- Environment-aware command execution plan (PowerShell/cmd.exe/Git Bash where relevant)

## Release Readiness

Check:

- Rollout strategy (staged rollout, feature flags, canary, etc.)
- Rollback path and trigger criteria
- Observability and alerting coverage for critical flows
- Incident response ownership and runbooks
- Platform-specific execution risks (path handling, shell mismatch, Windows-only tooling)

## Final Verdict Heuristic

- Pass only if blockers are zero and major issues are resolved or explicitly accepted.
- Conditional pass only with bounded, time-stamped mitigation plans.
- Fail when unresolved blockers or unbounded production risks remain.
