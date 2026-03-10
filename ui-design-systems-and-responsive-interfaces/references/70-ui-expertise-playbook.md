# UI Expertise Playbook for Vague Prompts

Use this playbook when user intent is broad (for example “improve this UI”) and there are no blocking constraints.

## Scope-Safe Default Output

Deliver this baseline package without adding unrelated product scope:

1. Screen goal framing (target user task + success signal).
2. Layout hierarchy proposal (desktop/tablet/mobile intent).
3. Reuse-first component map (reuse/variant/new component decisions).
4. Accessibility baseline (keyboard/focus/contrast/labels/target size).
5. CTA map (primary action, secondary actions, destructive/safe actions).
6. Responsive behavior rules (breakpoint or container behavior).
7. Consistency impact notes (token/system changes needed across pages).

## Responsive and Scalable Baseline

- Define responsive behavior from content constraints first, then validate viewport classes.
- Apply component-level responsiveness for shared modules.
- Use bounded fluid scaling for text and spacing when it improves continuity.
- Validate task-critical flows on smallest and largest supported viewports.
- Include orientation checks for mobile-heavy flows.

## Reuse and Maintainability Baseline

- Reuse existing components when semantics and behavior match.
- Create variants for scoped style/context differences.
- Create new components only when behavior diverges materially.
- Keep tokens semantic and prevent one-off overrides in shared primitives.

## CTA Baseline

- Keep CTA placement predictable across related screens.
- Ensure CTA labels are specific and outcome-oriented.
- Avoid ambiguous CTA pairs (for example “Continue” vs “Proceed”) when outcome differs.
- Validate CTA prominence and spacing across mobile and desktop layouts.

## Noise Prevention Baseline

- Remove non-functional decorative UI that competes with core tasks.
- Avoid duplicate helper text, repeated labels, and stacked status messages.
- Reduce action overload by limiting simultaneous CTA emphasis.
- Keep screen focus on key decision path and supporting information only.

## Authenticity Baseline (Avoid Generic AI-Look)

- Default to clean, restrained visual language when brand guidance is absent.
- Prioritize hierarchy, readability, and interaction clarity over decoration.
- Justify any bold stylistic treatment with product or brand intent.
- Benchmark mature products/design systems for principles, not direct imitation.

## Named Product-Family Baseline

- If the request references an existing product family, research the live product family before proposing a direction.
- Preserve the familiar mental model first, then state the minimum product-specific differentiation worth introducing.
- For chat or messaging surfaces, center the design on list scanability, thread rhythm, composer stability, and delivery-state clarity rather than hero-style presentation.
- Reject directions that feel like a generic SaaS dashboard, AI workspace, or marketing landing page when the surface is really a conversation product.

## Default Clarifying Questions (Only if Blocking)

Ask only when missing details would invalidate decisions:

1. Which platforms/viewports must be supported?
2. What accessibility conformance level is required?
3. Are there existing design tokens/components we must preserve?
4. Are there strict brand constraints that limit visual direction?
