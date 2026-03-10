# Real-World Benchmarking and Authenticity

## Goal

Produce UI that feels product-native and trustworthy, not generic template output.

## Benchmarking Protocol

For each major UI direction:

1. Select 3 relevant real-world references:
   - One domain competitor or analogous product
   - One mature design system reference
   - One accessibility-forward reference
2. Extract only transferable principles:
   - Information hierarchy
   - Interaction patterns
   - Content density
   - Responsive behavior
3. Do not replicate branding, layouts, or visual signatures directly.
4. Record why each extracted principle is relevant to the current user story.

## Authenticity Rules

- Match UI style to product domain and user expectations.
- Prefer restrained visual design over trend-heavy decoration by default.
- Use gradients, glows, and glass effects only with explicit brand/product rationale.
- Keep primary differentiation in problem fit, content clarity, and interaction quality.
- Avoid “template sameness”: if style choices could fit any app equally, refine with domain-specific hierarchy/content cues.

## Familiarity Rule

- Keep high-frequency patterns familiar to reduce user relearning cost.
- Introduce novelty only when it measurably improves usability or brand expression.
- Favor proven navigation and form patterns unless evidence shows the baseline fails target users.

## Named Product-Family Rule

- When the prompt names an existing product family, benchmark that family explicitly instead of substituting a generic product template.
- Extract the familiar interaction spine first: navigation model, thread or panel structure, composer or action placement, status semantics, and recovery cues.
- For messaging products, keep message content and conversation continuity visually dominant; supporting chrome, wallpapers, cards, and animations should remain subordinate.

## Anti-Pattern Checklist

Treat these as warning signals:

1. Overly decorative hero gradients on data/task-heavy screens.
2. Excessive card nesting, shadows, or blur that reduces information clarity.
3. Inconsistent spacing/typography rhythm across pages.
4. Shared components modified with one-off style overrides.
5. Novel interaction gestures that lack affordance or accessibility fallback.

## Review Checklist

1. Does the UI align with user/task context?
2. Is the design system applied consistently across screens?
3. Is style coherent with product brand and tone?
4. Are any decorative effects justified by purpose?
5. Does the solution avoid one-off pattern drift?
