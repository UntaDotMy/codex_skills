# Test Strategy and Risk Modeling

Use this reference to turn feature scope or incident scope into a production-grade test plan.

## Start With Risk, Not Tools

Ask these questions before naming a framework:
- What customer or operator outcome can fail?
- What data can be lost, corrupted, duplicated, or exposed?
- What path would block revenue, onboarding, recovery, or compliance?
- What dependency or runtime condition makes the issue more likely?
- What is the cheapest test layer that can detect the defect reliably?

## Coverage by Risk

| Risk Type | Typical Consequence | Minimum Evidence Expectation | Preferred Test Layers |
|---|---|---|---|
| Pure business logic defect | incorrect calculations or validation | deterministic failing assertion | unit plus focused integration when persistence or serialization matters |
| Cross-service contract drift | broken requests, null fields, version mismatch | request and response evidence, schema mismatch, provider expectation | contract plus provider integration |
| Critical user journey regression | customer-visible outage or failure to complete task | reproducible path with screenshots, traces, network logs | focused end-to-end plus supporting integration tests |
| Data integrity or duplication | double charge, missing record, replay, partial write | before and after state, idempotency evidence, retry evidence | integration plus queue or persistence testing, optional end-to-end confirmation |
| Performance or scalability issue | timeout, latency, saturation, cascading failure | thresholds, representative load profile, runtime metrics | performance, soak, and targeted end-to-end smoke |
| Intermittent failure | release uncertainty and confidence erosion | repeated runs, timing evidence, environment comparison | focused reproduction harness plus the lowest deterministic layer you can add |

## Layer Selection Rules

- Unit tests protect logic that can be isolated without losing meaning.
- Integration tests protect boundaries where persistence, serialization, queues, or network semantics matter.
- Contract tests protect service compatibility and should fail before consumer or provider drift reaches staging.
- End-to-end tests protect only the journeys that prove the system is wired correctly.
- Performance tests protect service-level objectives, concurrency assumptions, and degradation behavior.

Do not push everything upward into end-to-end tests. Do not keep everything so low-level that user-critical wiring never gets exercised.

## Real-World Planning Checks

Before finalizing a strategy, explicitly consider:
- feature flags and partial rollout states
- retry and idempotency behavior
- empty states, partial data, and null fields
- rate limits, timeouts, and slow dependencies
- background jobs, queues, eventual consistency, and out-of-order delivery
- locale, timezone, currency, and daylight-saving behavior
- browser, device, and network variability when UI is involved

## Quality Bar for a Serious Bug Fix

A serious bug is not considered covered unless:
- the original failure or exploit path is reproduced, or there is equivalent hard evidence
- one targeted regression test fails before the fix and passes after the fix when feasible
- the fix is guarded at the lowest effective layer
- one realistic integration or end-to-end confirmation exists when the bug crossed boundaries
- the release note or handoff names any remaining environment assumptions

## Anti-Patterns

Reject these shortcuts:
- adding more retries instead of understanding the failure
- using end-to-end tests to compensate for missing contract or integration coverage
- declaring performance healthy without thresholds and representative workload assumptions
- reusing brittle fixtures that hide ordering, timing, or uniqueness problems
- treating all red tests as product bugs or all flakes as test bugs
