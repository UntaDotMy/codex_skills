# API Layer and Contract Review

## Objective

Ensure API boundaries are stable, secure, maintainable, and production-ready.

## API Contract Review

Check:

1. Request/response schema consistency and versioning clarity.
2. HTTP method/status code correctness.
3. Error response shape consistency and actionable error semantics.
4. Pagination/filter/sort behavior for list endpoints.
5. Idempotency expectations for retried operations.

## API Layer Architecture Checks

- Controllers/handlers remain thin and orchestration-focused.
- Business rules stay in service/domain layers.
- Persistence concerns remain in repository/data layers.
- Validation and authorization happen at explicit boundaries.

## Security and Reliability Checks

- Authentication and authorization coverage for protected endpoints.
- Input validation and output encoding where relevant.
- Timeout/retry strategy for downstream dependencies.
- Rate limiting/abuse controls where required.

## Evidence and Standards

Validate against:

- OpenAPI specification patterns
- HTTP semantics (RFC 9110)
- OWASP API Security Top 10 guidance

Do not finalize high-confidence findings without current source confirmation.
