# Experience Briefs, Brownfield Redesign, and Validation Loops

Use this reference when a UX task needs sharper framing, safer redesign boundaries, or stronger connection between journey-level research and component-level validation.

## Experience Brief

Capture these fields before recommending changes:

1. Target user and job-to-be-done
2. Trigger and context of use
3. Primary journey and critical decision points
4. Known friction, confusion, abandonment, or trust risks
5. Current evidence: analytics, support tickets, session review, usability findings, stakeholder constraints
6. Success metrics and failure signals
7. Brownfield constraints: established brand rules, regulatory limits, technical dependencies, release sensitivity

## Brownfield Redesign Rules

- Preserve mental models users already rely on unless evidence shows they are harmful.
- Change the smallest part of the journey that can plausibly solve the problem.
- Name what stays stable versus what changes.
- Pair the redesign with a validation plan before rollout.

Useful persistent artifacts:

- `docs/design-system/MASTER.md` for product-wide experience and UI rules
- `docs/design-system/pages/<slug>.md` for local journey or page overrides
- `docs/research/<topic>.md` for evidence summaries and next-step decisions

Write-safety rules:

- derive a safe fallback slug when optional names are missing
- create directories before writing
- avoid implicit crashes or silent failures when metadata is absent

## Validation Loops

Use the lightest effective validation:

- usability check for comprehension and task success
- experiment or metric guard for production impact
- Storybook, Ladle, Histoire, or equivalent if component behavior is part of the UX risk
- design artifacts such as Pencil or Figma as supporting inputs, not the only evidence source

Tie every validation step back to a real outcome:

- completion rate
- confidence and trust
- recovery from errors
- decision speed
- accessibility and comprehension
