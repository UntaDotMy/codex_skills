# Database Query Performance and Scaling Review

## Objective

Identify database-layer risks early and recommend scalable, evidence-based improvements.

## Query and Index Review

Check:

1. Query plans for hot paths (`EXPLAIN` / query planner tools).
2. Index presence and selectivity for critical predicates and joins.
3. N+1 patterns and redundant round trips.
4. Full-table scans on large datasets without justification.
5. Unbounded result sets without pagination/limits.

## Data Access and Transaction Review

- Correct transaction boundaries and isolation assumptions.
- Locking/contention risk awareness.
- Read/write path separation where needed.
- Cache usage strategy and invalidation correctness.

## Growth and Scale Readiness

When dataset size increases, review:

- Partitioning strategy (where appropriate)
- Read replicas and read scaling approach
- Sharding/distribution strategy (if scale requires it)
- Connection pooling and resource limits

## Evidence Standards

Require at least one of:

- Query plan evidence
- Measured latency/throughput data
- Authoritative database guidance for selected technique

Do not recommend major DB changes without evidence-backed trade-offs.
