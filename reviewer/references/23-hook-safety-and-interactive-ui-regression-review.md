# Hook Safety and Interactive UI Regression Review

## Objective

Prevent runtime crashes and hidden regressions in hook-based UI code, especially when patches touch transformed/minified bundle output.

## When This Gate Applies

Apply this gate when:

1. Changed code uses hook-based UI frameworks.
2. UI behavior relies on repeated state transitions (toggles, panels, tabs, mode switches).
3. Patching occurs in generated/transformed/minified bundle outputs.

## Mandatory Hook Placement Safety

For hook-based frameworks, enforce:

1. Hook calls only at top level of component/custom-hook bodies.
2. No hook calls inside:
   - conditions (if, logical and/or, ternaries)
   - loops
   - callbacks or nested functions
   - async branches
3. No hook calls after conditional early returns.
4. No dynamic hook call indirection that changes call order between renders.

## Static Guard Requirements

Require static checks before pass verdict:

1. Enable framework-native hook linting (for example rules-of-hooks style checks).
2. For transformed/minified bundle patching:
   - add/extend project patch-lint guards (AST/syntax checks) that fail on conditional/dynamic hook invocation patterns
   - do not rely on one hardcoded script path; integrate with the project’s existing patch/lint pipeline
3. If static guard cannot run, record blocking risk and required owner follow-up.

## Interactive Runtime Regression Requirements

Require interaction-driven validation for affected UI flows:

1. Identify impacted state transitions (toggle, open/close, expand/collapse, tab/sheet switch, mode switch).
2. Exercise transitions repeatedly in interactive or e2e checks.
3. Capture runtime console/error logs and error-boundary events.
4. Treat startup-only smoke validation as insufficient evidence.
5. Fail gate on:
   - renderer crashes
   - error-boundary activation
   - unhandled runtime exceptions
   - hook-order/rules warnings in runtime output

## Evidence Requirements

Review output must include:

1. Static hook-lint output (or explicit blocker).
2. Interactive validation evidence (test run, trace, or reproducible log).
3. Runtime error/log summary for affected flows.
4. Fix-loop evidence if issues were found and remediated.

## Severity Guidance

- Blocker: runtime crash, error-boundary trigger, or deterministic hook-order violation.
- Major: missing mandatory static or interactive gate evidence in release-impacting UI scope.
- Minor: non-critical hook-safety smell with bounded blast radius.

## Primary References

- React Rules of Hooks overview: https://react.dev/reference/rules/rules-of-hooks
- React invalid hook call warning: https://react.dev/warnings/invalid-hook-call-warning
- ESLint plugin react hooks lints: https://react.dev/reference/eslint-plugin-react-hooks/lints
- ESLint no-restricted-syntax: https://eslint.org/docs/latest/rules/no-restricted-syntax
- Playwright test API (interactive UI automation): https://playwright.dev/docs/api/class-test
