# Web Fundamentals and Architecture

## Coverage

This file covers topics 47 and 52 (web part), and applies shared SDLC architecture principles.

## Web Fundamentals Baseline

- HTML for semantic structure and accessible meaning.
- CSS for presentation, layout, and responsive behavior.
- JavaScript for interactivity and application logic.
- DOM understanding for rendering and dynamic updates.

## Responsive and Adaptive Design

- Design for mobile-first constraints.
- Use flexible layouts and media queries.
- Validate usability across viewport classes and input modes.

## Architecture Choices: SSR vs SPA vs Hybrid

Evaluate with explicit criteria:

- SEO and initial content discoverability
- Time-to-content and runtime interactivity needs
- Backend coupling and deployment model
- Team expertise and operational complexity

### Typical Guidance

- SSR/SSG/hybrid for SEO-sensitive public pages.
- SPA patterns for highly interactive authenticated app surfaces.
- Hybrid approaches for mixed content and app-like routes.

## Module Boundaries

- Separate presentation, state orchestration, and domain logic.
- Keep API contracts explicit and version-aware.
- Avoid tight coupling between routing, data fetching, and domain rules.
