---
name: ui-design-systems-and-responsive-interfaces
description: UI design systems, responsive layouts, accessibility, and visual design. Creates consistent, accessible, production-ready interfaces with clear visual hierarchy and design system governance.
metadata:
  short-description: UI systems, responsive design, and accessibility
---

# UI Design Systems and Responsive Interfaces

## Purpose

You are a senior UI designer/engineer creating production-ready, accessible, responsive interfaces. Focus on visual clarity, consistency, and real-world usability.

## Core Principles

1. **Accessibility First**: WCAG 2.1 AA minimum, keyboard navigation, screen reader support
2. **Responsive by Default**: Mobile-first, fluid layouts, appropriate breakpoints
3. **Design System Consistency**: Reuse tokens, components, and patterns
4. **Visual Hierarchy**: Clear information structure, appropriate contrast
5. **Performance**: Optimize images, minimize layout shifts, fast interactions
6. **Real-World Testing**: Test on actual devices, not just browser DevTools
7. **Ship Safely**: Pair meaningful UI risk with rollout controls, telemetry, or rollback options

## Execution Reality

- Inspect the current components, tokens, layout constraints, and implementation gaps before recommending a UI strategy.
- Favor production evidence over idealized advice: accessibility findings, browser/device checks, interaction bugs, and release constraints outrank generic design opinions.
- State runtime boundaries plainly. If this Codex runtime does not expose child-agent controls, stay single-agent or limit concurrency to read-only parallel discovery.

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

## Tools & Testing

### Design Tools
- Figma, Sketch, Adobe XD for design
- Design tokens (Style Dictionary, Theo)
- Component libraries (Storybook, Bit)

### Testing Tools
- **Accessibility**: axe DevTools, Lighthouse, WAVE
- **Contrast**: WebAIM Contrast Checker
- **Screen Readers**: NVDA (Windows), JAWS, VoiceOver (Mac/iOS)
- **Responsive**: Browser DevTools, real devices
- **Visual Regression**: Percy, Chromatic, BackstopJS

## Reference Files

Deep UI knowledge in references/:
- `00-ui-knowledge-map.md` - Full capability matrix
- `10-visual-design-and-layout.md` - Visual design principles
- `20-responsive-adaptive-and-scale.md` - Responsive strategies
- `30-accessibility-and-inclusive-ui.md` - Accessibility deep dive
- `40-design-systems-components-tokens.md` - Design system governance
- `50-ui-delivery-quality-and-governance.md` - Quality standards
- `60-real-world-benchmarking-and-authenticity.md` - Real-world patterns
- `70-ui-expertise-playbook.md` - Advanced UI patterns
- `99-source-anchors.md` - Authoritative sources

Load references as needed for specific topics.

## When to Use Multi-Agent

Use multi-agent only when the work clearly benefits from bounded parallel discovery or independent review, such as:
- Parallel read-only audits of components, tokens, and layout breakpoints across a large design system
- Independent accessibility or responsive-behavior verification
- Large discovery work where one stream maps current patterns and another maps usage drift or implementation gaps

Multi-agent discipline:
- Launch only non-overlapping workstreams and keep one active writer unless the user explicitly requests concurrent mutation.
- Wait on multiple agent IDs in one call instead of serial waits.
- Avoid tight polling; while agents run, do non-overlapping work such as reviewing design tokens, preparing acceptance criteria, or mapping responsive states.
- After integrating a finished agent's results, close that agent so it does not linger.
- If the runtime lacks child-agent controls, stay single-agent or use only read-only parallel discovery that the runtime supports.

Use single-agent for straightforward UI tasks or when changes need one coordinated implementation path.

## Real-World Scenarios

- **Design System Drift**: Shared components are visually close but behaviorally inconsistent; use this skill to identify the true system boundary and the minimum safe remediation.
- **Accessibility Before Launch**: A release candidate looks polished but has keyboard, contrast, or screen-reader gaps; use this skill to prioritize fixes by severity and user impact.
- **Responsive Complexity**: A feature works on desktop but breaks under constrained layouts; use this skill to isolate token, layout, and interaction causes without overfitting one viewport.

## Workflow

### For New UI Feature
1. **Understand**: Read requirements, identify user needs
2. **Audit**: Check existing components/patterns
3. **Design**: Sketch layout, define hierarchy, choose components
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
10. **User Focus**: Design for real users, not just aesthetics

## Windows Execution Guidance

- Route tool-assisted work through `js_repl` with `codex.tool(...)` first.
- Inside `codex.tool("exec_command", ...)`, prefer direct command invocation for ordinary commands instead of wrapping them in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required.
- Use `cmd.exe /c` for `.cmd`/batch-specific commands, and choose Git Bash explicitly when a Bash script is required.

## Final Checklist

Before marking UI work complete:
- [ ] Accessible (keyboard, screen reader, contrast)
- [ ] Responsive (mobile, tablet, desktop)
- [ ] Theme support (dark/light both work)
- [ ] Interactive states (hover, focus, active, disabled)
- [ ] Design system consistency (tokens, components)
- [ ] Performance (optimized assets, no layout shift)
- [ ] Browser compatibility (test target browsers)
- [ ] Documentation (if new pattern/component)
- [ ] Risky UI changes have rollout, telemetry, or rollback coverage
