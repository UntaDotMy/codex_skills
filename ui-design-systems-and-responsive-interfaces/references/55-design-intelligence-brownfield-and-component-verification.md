# Design Intelligence, Brownfield Redesign, and Component Verification

Use this reference when the request is more than "make it look nicer" and needs a concrete visual-system decision, a safe redesign path, or component-level verification.

## Design Intelligence Packet

Before recommending visuals, capture:

1. Product type and platform surface
2. Primary user story and main CTA
3. Trust posture: authority, clarity, speed, delight, safety, or premium feel
4. Information hierarchy and proof elements
5. Style family and motion posture
6. Color mood and typography mood
7. Implementation constraints: framework, component library, dark mode, performance budget, supported devices
8. Anti-patterns that would make the result feel off-brand, low-trust, or generic

If the request references a familiar product family, also capture:

9. The named benchmark product family and the specific behaviors that should remain familiar
10. The core surface model to preserve, such as list to thread to composer for messaging
11. Theme, safe-area, keyboard, and interruption constraints that materially affect the surface

## Brownfield Redesign Rules

- Preserve proven brand assets and familiar navigation unless evidence says they are the problem.
- Prefer targeted redesigns for one journey, component family, or breakpoint over global churn.
- State what stays stable, what changes, and how regression risk will be checked.
- Use a persistent design-system record only when it materially improves team alignment.

Suggested structure:

- `docs/design-system/MASTER.md` for the shared visual-system source of truth
- `docs/design-system/pages/<slug>.md` for page- or flow-specific deviations

Persistence safeguards:

- normalize any optional project or page name to a safe fallback slug
- create parent directories before writing
- do not assume optional names or paths are present
- fail with a clear explanation instead of crashing on missing metadata

## Component Verification Loop

When the workspace already supports it, prefer isolated component verification before trusting whole pages:

- Storybook
- Ladle
- Histoire

Use isolated stories or demos to verify:

- default, hover, focus, active, disabled, loading, empty, error, and success states
- dark and light themes
- responsive behavior for the component itself
- visual regressions and accessible naming

## Design-Tool Integration

If the team already works with design artifacts:

- use Pencil or similar code-first design tools when they improve exploration and version control
- use Figma or screenshots as reference input, not as unquestioned truth
- avoid re-creating a mature component library when the correct move is to align with it
