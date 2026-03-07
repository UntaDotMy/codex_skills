# API Contracts and Boundaries

## Goals
- Define stable contracts before implementation details.
- Keep transport, authorization, validation, and domain logic boundaries explicit.
- Prevent compatibility drift across clients, jobs, and services.

## Design Rules
- Version only when compatibility cannot be preserved safely.
- Keep error shapes predictable and machine-parseable.
- Define idempotency behavior for retryable mutations.
- Normalize authorization at a consistent boundary.
- Document ownership of every externally visible contract.

## Anti-Patterns
- Contract-by-implementation with no written schema or compatibility rules.
- Hidden authorization checks split across handlers and repositories.
- Breaking response shapes during staged rollouts.
- Pagination or sort semantics changing without contract review.
