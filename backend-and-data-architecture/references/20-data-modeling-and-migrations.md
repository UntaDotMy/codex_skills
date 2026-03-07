# Data Modeling and Migrations

## Modeling Priorities
- Start from query patterns and integrity requirements.
- Choose one source of truth per critical business fact.
- Make eventual-consistency tradeoffs explicit.

## Migration Rules
- Prefer expand-and-contract for incompatible schema changes.
- Separate schema deploy, dual-write or backfill, read-path switch, and cleanup.
- Measure backfill duration, lock risk, and rollback boundaries before production.
- Never assume cache, replica, or search copies update atomically with the primary store.

## Verification
- Use representative data volumes where possible.
- Confirm read and write compatibility across old and new versions.
- Add metrics for backfill progress, error rate, and data drift.
