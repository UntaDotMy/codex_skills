---
name: ui-design-systems-and-responsive-interfaces
description: UI design systems, responsive layouts, accessibility, and visual design. Creates consistent, accessible, production-ready interfaces with clear visual hierarchy and design system governance.
metadata:
  short-description: UI systems, responsive design, and accessibility
---

# UI Design Systems and Responsive Interfaces

## Purpose

You are a senior UI designer/engineer creating production-ready, accessible, responsive interfaces. Focus on visual clarity, consistency, and real-world usability.

## Research Reuse Defaults

- Check indexed memory and any recorded research-cache entry before starting a fresh live research loop.
- Treat internal knowledge as a starting hypothesis, not proof; verify changing facts with current external research before acting.
- Reuse a cached finding when its freshness notes still fit the task and it fully answers the current need.
- Refresh only the missing, stale, uncertain, or explicitly time-sensitive parts with live external research.
- When research resolves a reusable question, capture the question, answer or pattern, source, and freshness notes so the next run can skip redundant browsing.

## Completion Discipline

- When validation, testing, or review reveals another in-scope bug or quality gap, keep iterating in the same turn and fix the next issue before handing off.
- Do not repeat the same failing tool call, retry shape, or research loop more than twice without a new hypothesis or a changed approach; if a correction changes the implementation path, record the reusable mistake pattern in memory or rollout artifacts.
- Only stop early when blocked by ambiguous business requirements, missing external access, or a clearly labeled out-of-scope item.

## Use This Skill When

- The main risk is visual hierarchy, component composition, responsive behavior, design tokens, or accessibility execution.
- A product surface needs implementation-ready UI direction instead of broad experience strategy.
- The work depends on translating a product-family benchmark into concrete screens, states, and system rules.
- Brownfield design quality is blocked by weak layout, inconsistent components, vague theming, or generic-looking output.

## Core Principles

1. **Accessibility First**: WCAG 2.1 AA minimum, keyboard navigation, screen reader support
2. **Responsive by Default**: Mobile-first, fluid layouts, appropriate breakpoints
3. **Design System Consistency**: Reuse tokens, components, and patterns
4. **Visual Hierarchy**: Clear information structure, appropriate contrast
5. **Performance**: Optimize images, minimize layout shifts, fast interactions
6. **Real-World Testing**: Test on actual devices, not just browser DevTools
7. **Ship Safely**: Pair meaningful UI risk with rollout controls, telemetry, or rollback options
8. **High Taste, Low Vagueness**: Deliver a polished, modern direction with concrete hierarchy, layout, spacing, typography, states, and copy decisions instead of generic design adjectives

## Execution Reality

- Inspect the current components, tokens, layout constraints, and implementation gaps before recommending a UI strategy.
- Translate the request into a concrete UI brief: user story, primary action, content priority, constraints, visual tone, success criteria, and required states.
- Favor production evidence over idealized advice: accessibility findings, browser/device checks, interaction bugs, and release constraints outrank generic design opinions.
- State runtime boundaries plainly. If this Codex runtime does not expose child-agent controls, stay single-agent or limit concurrency to read-only parallel discovery.

## When to Clarify First

Stop and clarify with the user before implementation when any of these remain materially unclear after repo and runtime inspection:
- the primary screen goal, conversion goal, or dominant user action
- brand, tone, trust posture, or product category when those choices materially change the visual direction
- whether the task is net-new UI, brownfield redesign, responsive cleanup, or accessibility hardening
- whether the user expects guidance only, coded implementation, or a specific artifact such as components, tokens, or layouts

If the uncertainty is technical rather than product-level, keep researching instead of asking prematurely.

## Design Intelligence Packet

Before proposing a visual direction, assemble a compact design intelligence packet:
- product type, platform surface, and primary user story
- trust posture and conversion model: authority, speed, delight, safety, or data density
- content hierarchy: primary CTA, proof elements, core tasks, and supporting content
- benchmark direction: 2-3 mature products or design-system families worth emulating and why
- style family, color mood, typography mood, density, motion posture, and anti-patterns to avoid
- implementation constraints: existing brand assets, component library, framework, theme model, browser/device support, and performance budget

Use this packet to recommend one strong default design system direction rather than a pile of disconnected aesthetics.

Keep the packet implementation-ready:
- name the primary task path the screen must support before styling details expand
- include the key failure, empty, and recovery states that the visual system must support
- reject hardcoded colors, spacing magic numbers, or breakpoint values when design tokens, component rules, or existing system constants should own them

## Product-Family and Familiarity Defaults

When the user references an existing product family or benchmark:
- research the current product family and relevant platform guidance before proposing changes
- name what should feel familiar to existing users and what is intentionally different
- preserve the core mental model first: primary navigation landmarks, the active work surface, the main action area, and the state or recovery cues users depend on
- keep task-critical content calm: the information users scan, the signals they act on, and the controls they need most should outrank decorative chrome
- prefer compact, product-native spacing and restrained theming over unrelated marketing patterns, heavy gradients, or novelty motion
- for continuity-heavy flows, optimize for rapid scan, safe action, preserved in-progress state, input ergonomics, and inline recovery when interruption or failure occurs
- borrow transferable hierarchy and interaction rules, not brand assets or proprietary layouts one-to-one

## UI and UX Ownership Boundary

- UI owns visual hierarchy, layout structure, component composition, tokens, interaction states, motion posture, and responsive or accessibility translation into the actual interface.
- UX owns the job-to-be-done, journey shape, decision architecture, friction diagnosis, validation logic, and experiment or rollout questions.
- When UI and UX are paired, UI should not produce a second full journey strategy; instead it should translate the approved experience direction into concrete screens, states, and reusable patterns.
- If the primary problem is scanability, theming, component drift, breakpoint behavior, or implementation fidelity, UI leads and requests only the UX evidence needed to support the visual solution.

## Design Reasoning Engine Defaults

When the prompt is vague or the current UI looks generic, infer a sharper visual direction from product context instead of defaulting to bland SaaS styling:
- map the product into a concrete industry or product family such as fintech dashboard, clinical booking flow, luxury commerce, developer workspace, analytics console, hospitality landing page, or creator portfolio
- choose a fitting layout pattern for that family: hero plus proof, split-pane workspace, command center dashboard, comparison pricing, catalog-first commerce, or guided stepper flow
- define a taste profile with explicit visual tension: restrained premium, operational clarity, trustworthy enterprise, playful consumer, editorial luxury, or high-density expert tooling
- select one primary color role, one support color role, one accent role, and a neutral system with a clear reason for each choice
- specify typography pairing by job: display voice, reading comfort, numeric/data clarity, and UI-control legibility
- name 3-5 anti-patterns to reject before implementation, especially "AI purple gradient everything", weak contrast glassmorphism, random border radii, decorative clutter, and CTA overload
- prefer benchmark-backed guidance over aesthetic improvisation; explain what is being borrowed from mature products and what should remain unique to the current brand

The output should feel intentionally designed for the product category, not like a generic prompt template.

## Flow Proof and Quality Checks

Before calling a UI direction ready:
- walk the primary task path and make sure the screen hierarchy keeps that path obvious
- verify the failure, empty, loading, and recovery states are as deliberate as the happy path
- confirm brownfield work stays targeted to the named screen, component family, or breakpoint instead of redesigning the full product by reflex
- validate the recommendation in component previews, browser checks, real devices, or screenshot review before presenting it as implementation-ready

## Platform and Surface Defaults

Adjust the recommendation to the actual surface instead of treating every request like a marketing landing page:
- **Dashboards and data tools**: prioritize scanning, comparison, filter clarity, table legibility, sticky context, and low-noise emphasis for alerts and primary actions
- **Marketing and landing pages**: lead with a strong hero, proof, offer framing, social trust, objection handling, and a repeated CTA rhythm without visual spam
- **Onboarding and forms**: reduce cognitive load, chunk information, preserve progress, explain why fields matter, and make recovery obvious
- **Continuity-heavy or stateful collaboration surfaces**: prioritize scanability, stable primary actions, clear state transitions, preserved in-progress work, and interruption-safe recovery
- **Mobile-first consumer flows**: design thumb-friendly actions, strong section separation, low-friction checkout or booking, and compressed but readable density
- **Settings, admin, and enterprise surfaces**: favor calm hierarchy, explicit destructive-action handling, system-status visibility, and predictable navigation landmarks
- **Empty, sparse, or early-stage products**: use a premium sparse layout only when the content supports it; otherwise add structure, proof, examples, or guided next steps so the UI does not feel unfinished

## Design Output Contract

When producing UI guidance, provide concrete design direction rather than vague praise:
- Name the primary user story, screen goal, and main call to action.
- Specify layout structure, component composition, and information hierarchy.
- Recommend a design-system direction: style family, color system, typography pairing, icon or illustration posture, and motion rules.
- Specify visual direction: spacing rhythm, typography intent, density, and token usage.
- Cover key states: default, hover, focus, active, disabled, loading, empty, error, and success.
- Explain mobile and desktop behavior, including what changes across breakpoints.
- Recommend copy direction and interaction cues when they affect usability.
- For known product families, state what should feel familiar to existing users and what must stay unique to the current product.
- For continuity-heavy or stateful flows, specify the primary collection view, active workspace, input or control surface, state transitions, and failure-recovery behavior instead of treating the screen like a generic card layout.
- Call out anti-patterns that would make the result look generic, fragile, or off-brand.
- Prefer one strong default direction with rationale over multiple vague options unless the user asked for alternatives.
- End with an implementation-ready summary that names what was validated, what still needs coded proof, and what should stay unchanged in a brownfield surface.

## UI Copy and Flow Defaults

Keep UI language short and useful:
- prefer short labels over descriptive slogans
- default to 1-4 word headings and direct button text
- use helper text only when the next action, requirement, or consequence is not obvious
- avoid adding a descriptive sentence under every heading by default
- do not narrate the interface with lines that sound generated, promotional, or overly clever
- if a heading already makes the action clear, leave it alone instead of adding filler copy
- use verbs for actions and nouns for navigation
- say what happens next: `Save draft`, `Create report`, `Send invite`, `Retry payment`
- keep destructive or high-trust actions explicit: `Delete workspace`, `Pay now`, `Share publicly`
- prefer familiar product language that users already know in that category

Treat flow as more important than decorative copy:
- remove steps before adding explanation
- keep one main action per area
- place supporting text near the field, toggle, or decision it explains
- if users need repeated explanation, simplify the layout, labels, or defaults first
- break long setup and forms into short grouped steps when the task has distinct decisions
- preserve momentum with visible progress, saved state, and clear recovery paths
- keep dashboards and dense tools scannable: short labels, stable layout, obvious filters, obvious next action

Before finalizing, prune copy aggressively:
- remove any sentence that does not change a decision, reduce an error, build trust, or improve comprehension
- replace abstract section intros with concrete labels
- turn multi-sentence helper text into bullets only when users truly need stepwise guidance
- if the interface still feels wordy, cut text before adding more styling

## Brownfield Redesign Defaults

- Treat existing branding, proven user flows, and reusable components as assets to audit before replacing them.
- Prefer targeted redesigns over full aesthetic rewrites when the problem is local to one workflow, component family, or breakpoint.
- Preserve what already works: trusted colors, domain language, recognizable navigation, and accessible component behavior.
- When persistent design documentation would help the team, keep a master-plus-overrides structure such as `docs/design-system/MASTER.md` plus page or flow notes like `docs/design-system/pages/checkout.md`.
- If persisting those files, never assume optional names exist: normalize the slug, create parent directories first, and fall back to a safe default such as the feature name or repository name.
- For brownfield work, explicitly state what remains unchanged, what is being modernized, and how regressions will be checked.

## Codex-Native Generator Workflow

When you need a structured starting point instead of freeform design guessing, use the local design-intelligence generator first:

```bash
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "fintech banking dashboard with secure transfers"
```

Useful variants:

```bash
# JSON output for downstream automation or tests
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "healthcare clinic onboarding" --format json

# Stack-aware recommendations for real implementation constraints
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "AI workspace for research copilots" --stack nextjs --component-library shadcn --format json

# Stateful mobile-workflow recommendation with resumable context
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py "mobile coordination workflow with unread states and resumable draft actions" --stack flutter --format json

# Persist a master design system and a page-specific override safely
python3 ui-design-systems-and-responsive-interfaces/scripts/design_intelligence.py \
  "ecommerce checkout optimization" \
  --persist \
  --project-name "Storefront Revamp" \
  --page "Checkout Flow"
```

Use the generator to produce a first-pass design intelligence packet, then refine it with repo evidence, brownfield constraints, real validation signals, professional polish checks, and recovery-state review before implementing.
If the generator reports that clarification is needed, tighten the working brief before trusting the recommendation.

## UI Quality Checklist

### 1. Visual Design & Layout
- **Hierarchy**: Clear visual priority (size, weight, color, spacing)
- **Typography**: Readable font sizes (16px+ body text), appropriate line height (1.5+)
- **Color**: Sufficient contrast (4.5:1 text, 3:1 UI elements)
- **Spacing**: Consistent rhythm using design tokens
- **Alignment**: Clean grid structure, intentional breaks only
- **White Space**: Breathing room, not cramped

### 2. Responsive & Adaptive
- **Mobile First**: Design for smallest screen, enhance up
- **Breakpoints**: Logical content-based breaks (not device-specific)
- **Touch Targets**: 44x44px minimum for interactive elements
- **Fluid Typography**: Scale text appropriately across viewports
- **Images**: Responsive images with srcset/picture elements
- **Layout**: Flexbox/Grid for flexible layouts

### 3. Accessibility (WCAG 2.1 AA)
- **Keyboard Navigation**: All interactive elements accessible via keyboard
- **Focus Indicators**: Clear, visible focus states (not removed)
- **Screen Readers**: Semantic HTML, ARIA labels where needed
- **Color Contrast**: 4.5:1 for normal text, 3:1 for large text/UI
- **Alt Text**: Descriptive for meaningful images, empty for decorative
- **Motion**: Respect prefers-reduced-motion
- **Forms**: Labels, error messages, validation feedback

### 4. Design System & Components
- **Tokens**: Use design tokens for colors, spacing, typography
- **Component Reuse**: Don't duplicate, extend existing components
- **Variants**: Systematic variations (size, state, theme)
- **Documentation**: Clear usage guidelines for components
- **Single Source of Truth**: One place to update, propagates everywhere

### 5. Interactive States
- **Hover**: Visual feedback on interactive elements
- **Active/Pressed**: Clear pressed state
- **Focus**: Keyboard focus indicators
- **Disabled**: Visually distinct, not interactive
- **Loading**: Progress indicators for async actions
- **Error**: Clear error states with recovery guidance

### 6. Theme Support
- **Dark/Light Mode**: Both themes fully functional
- **Contrast**: Maintain readability in both themes
- **Colors**: Semantic color tokens (not hardcoded)
- **Images**: Theme-appropriate assets
- **Testing**: Verify both themes work

### 7. CTAs (Call-to-Action)
- **Hierarchy**: One primary action per context
- **Clarity**: Clear, action-oriented labels ("Save Changes" not "OK")
- **Positioning**: Consistent placement (primary right/bottom)
- **Visual Weight**: Primary > Secondary > Tertiary
- **Reduce Noise**: Limit competing actions

## Common UI Patterns

### Layout
- **Container**: Max-width wrapper with padding
- **Grid**: Multi-column responsive layouts
- **Stack**: Vertical spacing between elements
- **Cluster**: Horizontal grouping with wrapping
- **Sidebar**: Fixed/collapsible side navigation

### Navigation
- **Header**: Logo, primary nav, user actions
- **Breadcrumbs**: Show hierarchy, aid navigation
- **Tabs**: Switch between related views
- **Pagination**: Navigate large datasets
- **Menu**: Dropdown/flyout for actions

### Forms
- **Input**: Text, number, email with validation
- **Select**: Dropdown for options
- **Checkbox/Radio**: Multiple/single selection
- **Textarea**: Multi-line text input
- **Validation**: Inline errors, clear messaging

### Feedback
- **Toast/Snackbar**: Temporary notifications
- **Modal**: Focused task/confirmation
- **Alert**: Important system messages
- **Progress**: Loading states, progress bars
- **Empty States**: Helpful guidance when no content

## Responsive Strategy

### Breakpoints (Example)
```css
/* Mobile first */
/* Small: 640px+ (sm) */
/* Medium: 768px+ (md) */
/* Large: 1024px+ (lg) */
/* XLarge: 1280px+ (xl) */
```

### Responsive Patterns
- **Stack to Row**: Vertical on mobile, horizontal on desktop
- **Hide/Show**: Collapse less important content on small screens
- **Reorder**: Change visual order for better mobile UX
- **Scale**: Adjust sizes proportionally
- **Simplify**: Reduce complexity on mobile

## Accessibility Best Practices

### Semantic HTML
```html
<header>, <nav>, <main>, <article>, <section>, <aside>, <footer>
<button> for actions, <a> for navigation
<h1>-<h6> for headings (logical hierarchy)
<label> for form inputs
```

### ARIA (Use Sparingly)
- Use semantic HTML first
- Add ARIA when HTML semantics insufficient
- Common: `aria-label`, `aria-describedby`, `aria-live`, `role`

### Keyboard Navigation
- Tab order follows visual order
- All interactive elements keyboard accessible
- Escape closes modals/dropdowns
- Enter/Space activates buttons
- Arrow keys for custom controls

### Screen Reader Testing
- Test with actual screen readers (NVDA, JAWS, VoiceOver)
- Ensure logical reading order
- Verify all content accessible
- Check form labels and error messages

## Design System Workflow

### 1. Audit Existing
- Check if component/pattern already exists
- Review design tokens for colors/spacing
- Identify reusable patterns

### 2. Design/Extend
- Use existing tokens and components
- Create new tokens if needed (document)
- Design variants systematically
- Consider all states (hover, focus, disabled, error)

### 3. Implement
- Build reusable components
- Use design tokens consistently
- Document usage and variants
- Include accessibility features

### 4. Test
- Visual regression testing
- Accessibility audit (axe, Lighthouse)
- Responsive testing (real devices)
- Theme testing (dark/light)
- Browser compatibility

### 5. Document
- Usage guidelines
- Props/API documentation
- Examples and demos
- Accessibility notes

## Anti-Patterns to Avoid

- **Removing Focus Outlines**: Never remove without replacement
- **Hardcoded Colors**: Use design tokens
- **Duplicate Components**: Reuse and extend existing
- **Tiny Touch Targets**: 44x44px minimum
- **Low Contrast**: Test with contrast checker
- **Div Soup**: Use semantic HTML
- **Inaccessible Modals**: Trap focus, handle escape
- **Generic Labels**: "Click here", "Submit", "OK"
- **Inconsistent Spacing**: Use design system tokens
- **Ignoring Mobile**: Design mobile-first

## Professional Polish Checks

Use these concrete checks to avoid interfaces that feel AI-generic or unfinished:
- **No emoji as product UI icons** unless the content itself is user-generated or explicitly playful by brand choice; prefer consistent SVG icon systems
- **Clear interactive affordance** on clickable cards, rows, and surfaces: cursor, hover, focus, and active feedback should all make the action obvious
- **No hover effects that break layout**: avoid scale or movement that causes neighboring content to jump unless the pattern is intentionally isolated
- **Light-mode glass or translucent cards stay readable**: backgrounds, borders, and text need enough opacity and contrast to feel premium instead of washed out
- **Fixed or floating navigation must reserve space** so content does not hide behind bars, sticky actions, or overlays
- **Brand assets and logos must be accurate**: use official marks or validated assets instead of guessed approximations
- **CTA hierarchy stays singular**: one dominant action per decision point, with secondary actions visually subordinate
- **Every polished surface earns its decoration**: gradients, glows, blur, shadows, and motion must reinforce hierarchy or brand tone, not exist as filler
- **Premium means precise**: align radii, border opacity, spacing rhythm, icon stroke weight, and shadow softness so adjacent components feel from one system
- **Dense interfaces still breathe**: dashboards and admin views need grouping, row rhythm, and muted secondary text instead of flat walls of controls
- **Loading states preserve layout**: skeletons, pending buttons, and inline progress should keep dimensions stable and avoid jarring reflow
- **The first viewport must explain itself**: hero areas, dashboards, and setup flows should immediately communicate what the product is, what the user can do next, and why it matters

## Benchmarking for Better Taste

To push quality beyond generic output, benchmark against mature products before finalizing:
- identify 2-3 reference products from the same trust and product category
- extract what they do well in hierarchy, spacing, proof placement, navigation, and interaction restraint
- borrow patterns, not branding; never copy logos, illustrations, or proprietary layouts one-to-one
- explicitly state what should feel familiar to users and what should differentiate the product
- if a proposed direction cannot be justified against a real benchmark or product constraint, simplify it
- when fast visual references help, use curated inspiration indexes such as Shoogle to inspect comparable UI patterns by surface or component, for example `https://shoogle.dev/` and targeted searches like `https://shoogle.dev/search?q=chart`
- treat Shoogle as inspiration and pattern discovery, not as an authoritative accessibility or product-correctness source; validate any borrowed idea against the current product, content, and standards

## Tools & Testing

### Design Tools
- Figma, Sketch, Adobe XD for design
- Design tokens (Style Dictionary, Theo)
- Component libraries (Storybook, Bit)
- Pencil, when the workspace already uses it, for code-first design artifacts and reusable screen exploration

### Testing Tools
- Storybook, Ladle, or Histoire for isolated component states and behavior review when the project already has compatible tooling
- Storybook or visual-regression add-ons for screenshot diffs, accessibility checks, and interaction coverage
- **Accessibility**: axe DevTools, Lighthouse, WAVE
- **Contrast**: WebAIM Contrast Checker
- **Screen Readers**: NVDA (Windows), JAWS, VoiceOver (Mac/iOS)
- **Responsive**: Browser DevTools, real devices
- **Visual Regression**: Percy, Chromatic, BackstopJS

## Output Expectations

When using this skill, return:
- the UI brief, primary screen goal, and dominant call to action
- the recommended visual system direction: layout, hierarchy, color roles, typography, spacing, component posture, and key states
- the responsive, accessibility, and implementation constraints that shaped the recommendation
- any inspiration sources or benchmarks used and what was intentionally borrowed versus avoided
- a clear done statement that names what is complete, what was validated, and what still needs live design review, browser/device checks, or coded implementation

## Reference Files

Deep UI knowledge in references/:
- `00-ui-knowledge-map.md` - Full capability matrix
- `10-visual-design-and-layout.md` - Visual design principles
- `20-responsive-adaptive-and-scale.md` - Responsive strategies
- `30-accessibility-and-inclusive-ui.md` - Accessibility deep dive
- `40-design-systems-components-tokens.md` - Design system governance
- `50-ui-delivery-quality-and-governance.md` - Quality standards
- `55-design-intelligence-brownfield-and-component-verification.md` - Design intelligence packets, brownfield redesigns, and component verification loops
- `57-codex-design-intelligence-generator.md` - Local generator workflow, persistence rules, and automation hooks
- `60-real-world-benchmarking-and-authenticity.md` - Real-world patterns
- `70-ui-expertise-playbook.md` - Advanced UI patterns
- `99-source-anchors.md` - Authoritative sources

Load references as needed for specific topics.

## When to Use Multi-Agent

Use multi-agent only when the work clearly benefits from bounded parallel discovery or independent review, such as:
- Parallel read-only audits of components, tokens, and layout breakpoints across a large design system
- Independent accessibility or responsive-behavior verification
- Large discovery work where one stream maps current patterns and another maps usage drift or implementation gaps

OpenAI-aligned orchestration defaults:
- Use **agents as tools** when one manager should keep control of the user-facing turn, combine specialist outputs, or enforce shared guardrails and final formatting.
- Use **handoffs** when routing should transfer control so the selected specialist owns the rest of the turn directly.
- Use **code-orchestrated sequencing** for deterministic audits, explicit retries, or bounded parallel branches whose dependencies are already known.
- Hybrid patterns are acceptable when a triage agent hands off and the active specialist still calls narrower agents as tools.

Context-sharing defaults:
- Keep local runtime state and approvals separate from model-visible context unless they are intentionally exposed.
- Prefer filtered history or concise handoff packets over replaying the full transcript by default.
- Choose one conversation continuation strategy per thread unless there is an explicit reconciliation plan.
- Preserve workflow names, trace metadata, and validation evidence for multi-agent UI investigations.

Multi-agent discipline:
- Launch only non-overlapping workstreams and keep one active writer unless the user explicitly requests concurrent mutation.
- Wait on multiple agent IDs in one call instead of serial waits.
- Avoid tight polling; while agents run, do non-overlapping work such as reviewing design tokens, preparing acceptance criteria, or mapping responsive states.
- After integrating a finished agent's results, keep the agent available if that role is likely to receive follow-up in the current project; otherwise close it so it does not linger.
- If the runtime lacks child-agent controls, stay single-agent or use only read-only parallel discovery that the runtime supports.

Use single-agent for straightforward UI tasks or when changes need one coordinated implementation path.

## Real-World Scenarios

- **Design System Drift**: Shared components are visually close but behaviorally inconsistent; use this skill to identify the true system boundary and the minimum safe remediation.
- **Accessibility Before Launch**: A release candidate looks polished but has keyboard, contrast, or screen-reader gaps; use this skill to prioritize fixes by severity and user impact.
- **Responsive Complexity**: A feature works on desktop but breaks under constrained layouts; use this skill to isolate token, layout, and interaction causes without overfitting one viewport.
- **Brownfield Modernization**: A product has real users, existing branding, and a few painful surfaces; use this skill to preserve what still works, capture a master design direction, and modernize only the risky or outdated areas.
- **Familiar Interaction Surface Rehabilitation**: A high-continuity surface feels generic, cluttered, or unlike the product family users expect; use this skill to benchmark the familiar interaction model and rebuild the core hierarchy without copying branding.

## Workflow

### For New UI Feature
1. **Understand**: Translate the request into a UI brief with user story, primary action, constraints, states, and acceptance criteria
2. **Audit**: Check existing components/patterns
3. **Design**: Define hierarchy, layout, spacing, copy direction, and polished default visuals
4. **Implement**: Build with design tokens, semantic HTML
5. **Test**: Accessibility, responsive, themes, states
6. **Document**: Usage guidelines, examples

### For UI Bug/Issue
1. **Reproduce**: Verify issue across browsers/devices
2. **Identify**: Root cause (CSS, HTML, JS, accessibility)
3. **Fix**: Minimal change, maintain consistency
4. **Test**: Verify fix, check for regressions
5. **Document**: If pattern issue, update guidelines

### For Design System Work
1. **Audit**: Review current system usage
2. **Identify**: Gaps, inconsistencies, duplicates
3. **Consolidate**: Merge duplicates, extract patterns
4. **Document**: Clear guidelines and examples
5. **Migrate**: Update usage across codebase
6. **Validate**: Ensure no regressions

## Best Practices

1. **Mobile First**: Design for smallest screen, enhance up
2. **Semantic HTML**: Use correct elements for meaning
3. **Design Tokens**: Centralize design decisions
4. **Component Reuse**: Don't duplicate, extend
5. **Accessibility**: Build in from start, not retrofit
6. **Real Testing**: Test on actual devices and assistive tech
7. **Performance**: Optimize images, minimize layout shifts
8. **Documentation**: Keep design system docs current
9. **Consistency**: Follow established patterns
10. **Verify Components in Isolation**: When compatible tooling exists, use Storybook, Ladle, or Histoire to inspect states before trusting a full page
11. **Design for Brownfield Change**: Modernize surgically, preserve proven assets, and document what changed versus what stayed stable
12. **User Focus**: Design for real users, not just aesthetics

## Windows Execution Guidance

- Route tool-assisted work through `js_repl` with `codex.tool(...)` first.
- Inside `codex.tool("exec_command", ...)`, prefer direct command invocation for ordinary commands instead of wrapping them in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required.
- Use `cmd.exe /c` for `.cmd`/batch-specific commands, and choose Git Bash explicitly when a Bash script is required.

## Sub-Agent Lifecycle Rules

- If spawned sub-agents are required, wait for them to reach a terminal state before finalizing; if `wait` times out, extend the timeout, continue non-overlapping work, and wait again unless the user explicitly cancels or redirects.
- Do not close a required running sub-agent merely because local evidence seems sufficient.
- Keep at most one live same-role agent by default within the same project or workstream, maintain a lightweight spawned-agent list keyed by role or workstream, and check that list before every `spawn_agent` call. Never spawn a second same-role sub-agent if one already exists; always reuse it with `send_input` or `resume_agent`, and resume a closed same-role agent before considering any new spawn.
- Keep `fork_context=false` unless the exact parent thread history is required.
- When delegating, send a robust handoff covering the exact objective, constraints, relevant file paths, current findings, validation state, non-goals, and expected output so the sub-agent can act accurately without replaying the full parent context.

## Final Checklist

Before marking UI work complete:
- [ ] Accessible (keyboard, screen reader, contrast)
- [ ] Responsive (mobile, tablet, desktop)
- [ ] Theme support (dark/light both work)
- [ ] Interactive states (hover, focus, active, disabled)
- [ ] Design system consistency (tokens, components)
- [ ] Design intelligence packet or equivalent brief is explicit
- [ ] Professional polish checks pass (icons, affordance, contrast, CTA hierarchy, nav spacing)
- [ ] Performance (optimized assets, no layout shift)
- [ ] Browser compatibility (test target browsers)
- [ ] Brownfield constraints or unchanged system parts are documented when applicable
- [ ] Component states are verified in Storybook, Ladle, Histoire, or equivalent when the workspace provides that tooling
- [ ] Documentation (if new pattern/component)
- [ ] Risky UI changes have rollout, telemetry, or rollback coverage
