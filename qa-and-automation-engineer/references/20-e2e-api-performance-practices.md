# E2E, API, and Performance Practices

Use this reference when the work involves runtime behavior, external boundaries, or release-significant automation.

## End-to-End Practices

### Test the Right Journeys
Prioritize:
- authentication and session continuity
- payments, checkout, or other irreversible actions
- create, update, delete, and recovery flows
- permission boundaries and role changes
- feature-flag paths and degraded-mode behavior

### Prefer Stable Signals
- Use accessibility roles, labels, or explicit test identifiers instead of brittle styling hooks.
- Wait for meaningful application state, not arbitrary time.
- Capture traces, screenshots, and network activity for failures by default when the framework supports it.
- Control or seed data so that failures are explainable and repeatable.
- Keep end-to-end tests independent enough that a prior failure does not poison the next case.

### Real-World UI Failure Patterns
Be ready for:
- optimistic UI that rolls back after the server rejects the action
- background refresh or websocket updates that race assertions
- browser permission dialogs, download flows, and popup handling
- session expiration during long-running flows
- cross-tab or resume-from-sleep behavior

## API and Contract Practices

### Validate More Than Happy Paths
Cover:
- required and optional fields
- authorization boundaries
- malformed input and type mismatches
- pagination, filtering, and sorting edge cases
- idempotency and replay safety
- partial failure and retry behavior
- backward-compatible and forward-compatible contract expectations

### Contract Discipline
- Use the documented API contract as a living gate, not a stale attachment.
- Fail fast on renamed fields, missing fields, enum drift, and incompatible status-code changes.
- Separate consumer assumptions from provider guarantees so ownership is clear.
- Prefer provider verification or equivalent runtime validation before release.

## Performance Practices

### Define the Workload Before Running the Tool
State:
- target environment
- concurrency model and arrival pattern
- success thresholds for latency, error rate, and throughput
- warm-up versus steady-state expectations
- abort conditions and what constitutes a blocked release

### Measure the System, Not Just the Script
Collect:
- application logs
- database and queue saturation indicators
- infrastructure metrics
- dependency error rates
- percentile latency, not only averages
- evidence of backpressure, retries, or cascading failure

### Performance Failure Scenarios to Model
- cold starts after deploy
- connection pool exhaustion
- cache miss storms
- third-party rate limiting
- burst traffic on a business-sensitive workflow
- long-tail latency that breaks user timeouts even when averages look fine

## Runtime Boundaries

Do not claim confidence when:
- the performance test uses unrealistic data volume
- the environment lacks representative dependencies or concurrency
- the contract test validates only schema shape but not semantic behavior
- the end-to-end suite proves only the sunny day path
- a passing run depends on hidden state from prior tests

## Exit Criteria

This category is ready when:
- the critical journey is covered by at least one realistic automated path
- important API boundary cases are exercised with evidence
- explicit performance thresholds exist for meaningful release decisions
- failure artifacts are sufficient for another engineer to investigate without starting over
