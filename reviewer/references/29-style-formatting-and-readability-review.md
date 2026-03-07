# Style, Formatting, and Readability Review

## Objective

Keep code readable and consistent with stack-native tooling and project conventions.

## Formatter and Lint Review

1. Detect project formatter/linter configuration first (`prettier`, `eslint`, language-native tools).
2. If Prettier is configured, enforce project config rather than personal preferences.
3. If no formatter is configured, do not impose arbitrary formatting standards.
4. Ensure lint rules and formatting rules do not conflict in CI.

## Readability Checks

- Function/class/module names communicate intent clearly.
- Files are organized by responsibility.
- Functions stay focused and manageable in size/complexity.
- Control flow is straightforward and avoids unnecessary indirection.

## Stack-Aware Guidance

- Use conventions that fit the active stack, framework, and repository standards.
- Verify best-practice claims with current web sources for the specific stack.
- Prefer incremental refactors over broad style churn in production branches.

## Reporting Expectations

For readability/style findings, include:

1. Why readability/maintainability is harmed.
2. Minimal change to improve clarity.
3. Whether change is blocking or non-blocking for release.
