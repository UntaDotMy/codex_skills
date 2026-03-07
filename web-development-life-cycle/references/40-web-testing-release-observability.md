# Web Testing, Release, and Observability

## Coverage

This file applies core topics 21, 22, 23, 32, 40 to web delivery.

## Web Testing Strategy

- Unit tests for pure functions, state reducers, and utilities.
- Component/integration tests for UI behavior and API interactions.
- End-to-end tests for critical journeys (auth, checkout, key workflows).
- Accessibility checks integrated in CI for critical pages/components.

## CI/CD for Web

- Build and type checks
- Unit/component tests
- Security and dependency scanning
- End-to-end smoke tests against staging preview
- Controlled promotion to production with rollback support

## Release Controls

- Use environment-specific configuration with strict secret handling.
- Verify database/API compatibility before rollout.
- Use feature flags for high-risk features.
- Run post-deploy validation checks for core user paths.

## Observability and Runtime Feedback

- Monitor error rates, latency, throughput, and Web Vital trends.
- Correlate frontend issues with backend traces where possible.
- Alert on user-impacting thresholds.
- Feed incident learnings into backlog and architectural improvements.
