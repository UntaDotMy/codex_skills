# Mobile Lifecycle and Platform Architecture

## Coverage

This file covers topics 42 and 52 (mobile part), and applies core SDLC topics to mobile.

## Platform Lifecycle Fundamentals

### Android

- Understand activity/fragment lifecycle transitions.
- Handle process death and state restoration explicitly.
- Respect background execution limits and work scheduling policies.

### iOS

- Understand app lifecycle states and scene/session transitions.
- Handle lifecycle callbacks for foreground/background transitions.
- Design for suspension and limited background execution windows.

## Architecture Baseline for Mobile

- Use layered boundaries (presentation, domain, data, platform adapters).
- Keep business logic testable and independent from UI frameworks.
- Encapsulate platform-specific services behind interfaces.
- Reuse core modules across platforms where behavior is shared.

## Native vs Cross-Platform Decision Lens

Evaluate by:

- UX fidelity and native interaction depth
- Runtime performance and startup budget
- Access to platform APIs and update cadence
- Team skill composition and long-term maintainability

## Mobile-Specific Failure Modes

- Lifecycle-related state loss
- Background task cancellation
- OS-driven process termination
- Fragmented device/network conditions

Mitigate with defensive state persistence, idempotent workflows, and robust retry design.
