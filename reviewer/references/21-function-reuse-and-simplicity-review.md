# Function Reuse and Simplicity Review

## Objective

Detect avoidable duplication and overengineering so the codebase stays maintainable.

## Reuse-First Review Checks

For each new or changed function/module:

1. Search for existing equivalent behavior in the same codebase.
2. Compare semantics, side effects, and error behavior before adding new implementation.
3. Reuse existing function/component/service when behavior already matches.
4. If behavior differs slightly, prefer:
   - extending via parameters/options, or
   - adding a scoped variant/wrapper
   over copy-paste duplication.
5. If a new function is required, document why reuse is unsafe or insufficient.

## Duplicate Logic Signals

- Similar branching logic appears in multiple modules.
- Repeated query builders or payload mappers with minor edits.
- Multiple helper functions with same input/output behavior.
- New abstraction created but called from only one place without clear near-term need.

## Simplicity and Overengineering Checks

Flag as overengineering when:

- Abstraction depth exceeds problem complexity.
- Premature optimizations increase cognitive load without measured need.
- Generic frameworks are introduced for one-off use cases.
- Existing simple path is replaced with complex orchestration without risk/value justification.

## Review Output Expectations

For each reuse/simplicity finding include:

1. Existing reusable target (file/function/component).
2. Why duplication or complexity is risky.
3. Minimal simpler alternative.
4. Verification step to confirm behavior parity.
