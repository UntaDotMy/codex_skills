# Responsive, Adaptive, and Scale Strategy

## Responsive vs Adaptive

- Responsive: fluid layouts that adapt continuously to viewport changes.
- Adaptive: discrete layout variants optimized for specific size classes/context.
- Combine both where appropriate: responsive base with adaptive overrides.

## Breakpoint and Container Strategy

- Define breakpoints from content/layout behavior, not device brand assumptions.
- Use container-aware design where component context matters more than global viewport.
- Specify behavior per breakpoint: layout, navigation, density, and interaction model.
- Prefer component-level responsiveness for reusable blocks (cards, nav, forms, tables).
- Keep a documented viewport matrix for validation and regression checks.

## Fluid Sizing Strategy

- Use fluid sizing for typography/spacing where it improves continuity between breakpoints.
- Bound fluid behavior with sensible minimum/maximum values.
- Guard against overflow and truncation when localization or user-generated content expands.

## Multi-Device and Orientation

- Validate portrait and landscape behavior for critical workflows.
- Handle touch, pointer, and keyboard interaction differences.
- Define fallback behavior for constrained devices and low-bandwidth contexts.
- Validate touch target size and spacing for mobile ergonomics.

## Responsive CTA Placement

- Keep primary CTA position consistent per flow across breakpoints.
- Ensure primary CTA remains discoverable without excessive scrolling on critical steps.
- For mobile-heavy flows, use sticky/fixed CTA patterns only when they do not hide content or controls.
- Separate destructive CTAs from primary/safe CTAs with clear spacing and visual distinction.

## UI at Product Scale

- Standardize layout primitives and spacing tokens.
- Avoid one-off components unless proven reusable.
- Monitor design drift and divergence with regular audits.
- Use adoption/version policy for component library changes.
- Prefer feature-level composition over page-level one-off custom blocks.

## Performance-Aware UI

- Treat performance budgets as part of UX quality.
- Control asset weight, render cost, and layout shift risk.
- Define rendering priorities for critical content and interactions.
- Treat layout shift, input delay, and rendering stability as release-gating signals.
