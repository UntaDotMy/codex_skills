# Code Quality, Security, and Performance Review

## Correctness and Maintainability

Check for:

- Logic correctness and edge-case handling
- Clear module boundaries and low coupling
- DRY/KISS/SOLID consistency
- Defensive error handling and resilience patterns
- Readable naming and maintainable structure
- Duplicate behavior hotspots (use `21-function-reuse-and-simplicity-review.md`)

## Security Review

Minimum checks:

- Input validation and output encoding where relevant
- Authentication and authorization correctness
- Secret handling and sensitive data exposure
- Dependency vulnerability posture
- Secure defaults for network/storage/session behavior

Use OWASP and project threat model expectations as baseline.

## Performance and Reliability Review

Check:

- Hot-path complexity and resource usage
- Timeouts/retries/circuit-breaking for remote dependencies
- Latency/throughput trade-offs documented
- Degradation and failure behavior under stress
- Simpler alternatives considered before complex patterns (avoid accidental overengineering)

## Severity Guidance

- Blocker: vulnerability, data loss risk, or deterministic production failure path.
- Major: high probability of runtime error/performance regression.
- Minor: maintainability/efficiency issues with limited immediate risk.
- Nit: low-impact preference-level improvements.
