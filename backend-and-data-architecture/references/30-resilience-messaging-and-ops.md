# Resilience, Messaging, and Operations

## Resilience Checklist
- Timeout budgets are explicit.
- Retry ownership is explicit.
- Idempotency or deduplication keys exist where side effects matter.
- Dead-letter handling is defined.
- Partial-failure behavior is observable.

## Messaging Guidance
- Document ordering guarantees and when they do not hold.
- Model poison messages and replay behavior before production.
- Use outbox or equivalent patterns when event publication must follow persistence reliably.

## Operational Readiness
- Logs identify contract boundary, actor, and failure reason.
- Metrics expose queue depth, retry rate, slow queries, and dependency failures.
- Alerts fire on actionable symptoms, not noisy infrastructure trivia.
