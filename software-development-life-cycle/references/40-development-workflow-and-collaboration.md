# Development Workflow and Collaboration

## Git and Branching Strategy

Adopt one explicit branching model and document it:

- Trunk-based development for fast integration and small changes.
- GitFlow-style release/hotfix branches for structured release trains.

Baseline rules:

- Keep branches short-lived.
- Rebase or merge frequently to reduce integration drift.
- Protect main branch with required checks.

## Pull Requests and Conflict Resolution

- Require scoped PRs with clear intent and test evidence.
- Keep PR size reviewable; split large refactors into sequenced PRs.
- Resolve conflicts by reconciling intent, not line-level compromise.
- Re-run tests after conflict resolution.

## Code Review Practices

Review for:

- Correctness and edge cases
- Architecture and maintainability
- Security/privacy risks
- Performance implications
- Readability and documentation quality

Favor constructive, evidence-based feedback and quick follow-ups.

## CI/CD Fundamentals

Minimum CI gates:

1. Build and dependency integrity checks
2. Unit tests
3. Static analysis and security scanning
4. Integration tests for changed surfaces

CD basics:

- Promote through dev/stage/prod environments.
- Use versioned artifacts and immutable deployment units.
- Support one-click rollback or traffic-based rollback.

## Debugging and Root-Cause Analysis

Apply a repeatable loop:

1. Reproduce reliably.
2. Instrument and collect logs/traces/metrics.
3. Isolate minimal failing path.
4. Identify root cause (not symptom).
5. Validate fix with targeted regression tests.
6. Record lessons learned and prevention guardrails.

## Error Handling and Resilience

For distributed dependencies:

- Set explicit timeouts.
- Use bounded retries with jitter.
- Use circuit breakers/bulkheads where needed.
- Design graceful degradation paths.
- Ensure idempotency for retried operations.

## Performance Fundamentals

- Distinguish latency, throughput, and concurrency.
- Profile before optimizing.
- Optimize highest-impact bottlenecks first.
- Document trade-offs (speed vs cost vs complexity).

## Estimation and Communication

- Use story points or relative sizing for planning.
- Track cycle time and flow efficiency.
- Include risk buffer for unknowns.
- Provide concise status updates with risks, blockers, and decisions needed.
