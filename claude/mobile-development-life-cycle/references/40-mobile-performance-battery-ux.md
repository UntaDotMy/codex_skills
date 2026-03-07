# Mobile Performance, Battery, UX, and Accessibility

## Coverage

This file covers topic 46 and applies core topics 26, 35, 36.

## Performance Fundamentals for Mobile

- Set explicit startup and interaction latency budgets.
- Avoid main-thread blocking work.
- Batch and defer non-critical work.
- Profile CPU, memory, and rendering before optimization.

## Battery Efficiency

- Prefer OS-managed schedulers for deferred background work.
- Minimize wakeups and unnecessary polling.
- Reduce radio usage with request batching and caching.
- Avoid aggressive retry loops on poor networks.

## Network Efficiency

- Use compression and compact payloads.
- Cache immutable or rarely changed data.
- Avoid overfetching.
- Use resilient sync with backoff and bounded retries.

## Mobile UX and Accessibility

- Support screen readers and accessible labels.
- Preserve sufficient color contrast and touch target sizes.
- Keep flows simple, predictable, and forgiving.
- Account for localization, text expansion, and right-to-left layouts where required.

## Acceptance Checklist

1. Meets startup/interaction targets on representative devices.
2. Meets battery/network budget expectations.
3. Passes core accessibility checks.
4. Handles offline and degraded connectivity gracefully.
