# UI/UX Consistency and System-Impact Review

## Objective

Ensure UI/UX changes are responsive, coherent, and safe across the whole system, not only the touched screen.

## UI Consistency Checks

1. Responsive behavior across target viewport/device matrix.
2. Theme/token consistency (colors, typography, spacing, elevation, motion).
3. Theme-mode parity and visibility (light/dark):
   - body text, headings, metadata, and helper text remain legible
   - button/CTA states (default/hover/focus/disabled/loading) remain distinguishable
   - icon-only and low-emphasis controls remain visible and understandable
   - alerts/success/warning/error semantics remain consistent in both modes
4. CTA hierarchy and clarity:
   - primary CTA is obvious
   - secondary/destructive actions are distinct
   - CTA labels clearly communicate outcome
   - CTA color semantics match action priority/risk
   - CTA positioning is predictable across related screens and breakpoints
5. Component reuse integrity:
   - Existing components reused where semantics match.
   - New variant/specialized component introduced when behavior diverges.
   - No one-off hacks in shared primitives.
6. Visual authenticity:
   - Style aligns with brand/product context.
   - Avoid trend-heavy decorative defaults without clear rationale.

## UX Continuity Checks

1. Journey continuity across pages and states.
2. Consistent terminology and interaction behavior.
3. Predictable navigation and recovery flows.
4. Accessibility and inclusive behavior consistency in critical paths.
5. CTA predictability across journey steps (users understand next action at each step).
6. Noise and decision-load control:
   - avoid action overload in a single step
   - remove redundant copy/UI clutter that reduces task clarity
7. Theme-switch continuity:
   - switching between dark/light does not break orientation, hierarchy, or action confidence

## Cross-System Impact Sweep

For each major finding, check upstream/downstream impacts:

- Shared components affected?
- Adjacent workflows/regression risk?
- Design-system or token updates needed?
- Documentation/tests/monitoring updates missing?

## Reporting Expectations

When gaps are found, include:

1. Current task impact
2. System-wide impact
3. Minimal safe patch path
4. Follow-up tasks to prevent recurrence
