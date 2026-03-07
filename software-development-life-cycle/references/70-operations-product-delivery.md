# Operations, Product, and Delivery

## Logging, Monitoring, and Observability

Collect and correlate:

- Metrics (health and SLO indicators)
- Logs (structured events with context)
- Traces (cross-service request flow)

Set alerts tied to user impact, not only infrastructure thresholds.

## Documentation Standards

Maintain:

- README for setup and runbook basics
- API docs for contracts and examples
- ADRs for major architectural decisions
- Code comments only when intent is non-obvious

Treat docs as part of the deliverable, not optional extras.

## Product Thinking

- Define MVP scope for fastest validated learning.
- Create feedback loops (analytics, interviews, support signals).
- Measure outcomes, not just output volume.
- Iterate based on user value and risk reduction.

## UX/UI Accessibility

- Use accessible semantics and keyboard-friendly interactions.
- Consider contrast, focus states, and assistive technologies.
- Apply WCAG principles as baseline for web and mobile surfaces.

## Internationalization and Localization

- Externalize user-facing strings.
- Handle pluralization and text expansion.
- Use locale-aware formatting for date/time/currency.
- Design timezone-safe data and scheduling flows.

## Deployment Fundamentals

- Separate environments: dev, staging, prod.
- Use progressive rollout patterns when possible.
- Define rollback trigger and rollback mechanism.
- Keep infrastructure and app config versioned and auditable.

## Container and Cloud Basics

- Use containers for portability and consistency.
- Understand core cloud primitives (compute, storage, networking, IAM).
- Design for scalability, fault isolation, and cost awareness.

## Cross-Platform Architecture Choices

- Mobile: native vs cross-platform trade-off based on UX/performance/team constraints.
- Web: SSR/SSG/SPA decision based on SEO, performance, and runtime interactivity needs.

## Estimation and Stakeholder Communication

- Provide realistic estimates with confidence ranges.
- Communicate assumptions and risks early.
- Keep stakeholders updated with objective progress and decision points.
