# Mobile Testing, Release, and Observability

## Coverage

This file covers topic 45 and applies core topics 21, 22, 23, 32, 40.

## Mobile Testing Layers

- Unit tests for domain and state reducers/view models/controllers.
- Integration tests for data layer, storage, and API boundaries.
- UI/instrumentation tests for critical flows.
- Device matrix testing across OS versions, form factors, and network conditions.

Include lifecycle transition tests:

- Background/foreground transitions
- Process death and restoration
- Permission acceptance/denial paths

## Release Management

- Define build variants/flavors and environment mapping.
- Manage signing keys/profiles/provisioning securely.
- Use staged rollout/release tracks.
- Gate production release on crash-free and performance thresholds.

## Store Compliance Basics

- Verify policy compliance for data collection, permissions, and disclosures.
- Keep privacy policy and metadata accurate.
- Track review feedback and policy changes each release cycle.

## Observability and Runtime Quality

- Capture crash and ANR diagnostics.
- Track startup time, rendering smoothness, and network error rates.
- Alert on user-impacting regressions.
- Correlate releases with runtime quality changes.
