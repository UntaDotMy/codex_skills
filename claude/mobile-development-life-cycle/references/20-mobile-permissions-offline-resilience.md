# Mobile Permissions, Offline Sync, and Resilience

## Coverage

This file covers topics 43 and 44, with links to core topics 25, 27, 39.

## Permissions and Device Capabilities

Follow least-privilege policy:

- Request only permissions required for visible user value.
- Request at runtime in context, not all upfront.
- Provide clear rationale before prompting.
- Handle denial gracefully with fallback paths.

Common sensitive capabilities:

- Camera/microphone
- Location
- Bluetooth and nearby device access
- Notifications

## User Trust and Consent UX

- Explain why data/capability is needed.
- Keep copy concise and action-oriented.
- Avoid dark patterns and repeated coercive prompts.
- Provide privacy controls in settings.

## Offline-First and Sync Strategy

- Persist critical user actions locally first.
- Use conflict-aware sync (versioning/timestamps/merge rules).
- Use retry with backoff and jitter.
- Preserve idempotency for duplicate submissions.

## Conflict Resolution Patterns

- Last-write-wins for low-risk fields.
- Semantic merge for composite objects.
- User-assisted merge for high-value conflicts.

Document chosen policy clearly and test edge cases.

## Mobile Resilience Controls

- Timeouts on network calls
- Bounded retry budgets
- Circuit-breaker style suppression for failing dependencies
- Graceful degradation for partial feature availability
