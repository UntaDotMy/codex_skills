# Code Integrity Anti-Pattern Review

## Objective

Catch hidden quality debt that often ships bugs: duplicate logic, weak type discipline, unsafe boundary handling, unnecessary fallbacks, and incomplete delivery claims.

## Mandatory Anti-Pattern Checklist

Always check and report these patterns when code is in scope:

### Readability Anti-Patterns (BLOCKER)
1. **Shortform Variable Names** - Using `usr`, `btn`, `tmp`, `data`, `res`, `req`, `arr`, `obj`, `fn`, `cb`, `idx`, `len`, `str`, `num` instead of full descriptive names.
2. **Single-Letter Variables** - Using `x`, `y`, `z`, `a`, `b`, `c` (except i, j, k in simple loops).
3. **Cryptic Abbreviations** - Using `calc`, `proc`, `mgr`, `svc`, `repo`, `util` without clear context.
4. **Generic Function Names** - Using `handleData`, `processInfo`, `doStuff` instead of specific verb+noun.

### Scope Creep Anti-Patterns (BLOCKER)
5. **Unrequested Features** - Adding features not in requirements.
6. **Unnecessary Refactoring** - Refactoring code not related to the task.
7. **Unwanted Backward Compatibility** - Adding compatibility layers when just updating.
8. **Dead Code Retention** - Keeping old code "just in case" instead of deleting.
9. **Speculative Error Handling** - Adding error handling for scenarios that can't happen.
10. **Unrequested Validation** - Adding validation not in requirements.
11. **Unrequested Configuration** - Adding config options not requested.
12. **Comments on Unchanged Code** - Adding comments to code you didn't change.

### Original Anti-Patterns (MAJOR)
13. Refusing to Use Type Definitions.
14. Type Casting.
15. Incomplete Objects.
16. Fallback to Nonsense.
17. Duplicated Yet Incomplete Functionality.
18. Overlapping Functionality.
19. Passing Partial Objects.
20. Renaming Variables.
21. Inline Types.
22. Screwing with Imports.
23. Doing Part of the Work then Cal Done.
24. Hardcoded Business or Runtime Values.
25. Unnecessary Fallback Logic Without Requirement.
26. Conditional or Dynamic Hook Invocation in Hook-Based UI Components.

### Shortcut Anti-Patterns (MAJOR)
27. **Disabled Linting/Type Errors** (using `// eslint-disable` or `@ts-ignore` without justification).
28. **Test Skipping** (using `.skip()` or commenting out failing tests).
29. **Force Flags** (using `--force`, `--no-verify`, or similar without understanding).
30. **Any Type Abuse** (using `any` type in TypeScript instead of proper typing).
31. **Validation Skipping** (removing validation "temporarily" or only on client-side).
32. **Performance Shortcuts** (removing optimization because "it's too complex").

### Accessibility Anti-Patterns (MAJOR)
33. **Removing Focus Outlines** (without accessible replacement).
34. **Missing Alt Text** (on meaningful images).
35. **Inaccessible Modals** (no focus trap, no escape handling).
36. **Low Contrast Text** (below WCAG requirements).
37. **Missing ARIA Labels** (on interactive elements without visible labels).

## What Good Looks Like

1. **Full Descriptive Names**: `user`, `button`, `temporaryValue`, `userData`, `response`, `request`, `userArray`, `currentIndex`, `arrayLength`, `userName`, `itemCount`
2. **Verb+Noun Functions**: `getUserData`, `calculateTotal`, `validateEmail`, `fetchUserProfile`, `processPayment`
3. **Reuse-first**: existing helpers/services/components are reused when behavior already matches.
4. **Single-source-of-truth**: shared logic lives in one canonical module.
5. **Modular boundaries**: API/domain/data layers stay separate and traceable.
6. **Type integrity**: shared contracts are reused, not shadowed.
7. **Simple over clever**: no extra abstraction without measurable need.
8. **Requirement-backed behavior**: defaults/fallbacks exist only when explicitly needed.
9. **Scope discipline**: Only implement what was requested, nothing more.
10. **Clean updates**: When updating, delete old code completely - no backward compatibility unless requested.

## Detection Heuristics

### Readability Issues (BLOCKER)
- Shortform variable names: `usr`, `btn`, `tmp`, `data`, `res`, `req`, `arr`, `obj`, `fn`, `cb`, `idx`, `len`, `str`, `num`
- Single-letter variables: `x`, `y`, `z`, `a`, `b`, `c` (except i, j, k in loops)
- Cryptic abbreviations: `calc`, `proc`, `mgr`, `svc`, `repo`, `util`
- Generic function names: `handleData`, `processInfo`, `doStuff`

### Scope Creep Issues (BLOCKER)
- Features not in requirements
- Refactoring unrelated code
- Backward compatibility added without request
- Old code kept instead of deleted
- Error handling for impossible scenarios
- Validation not requested
- Configuration not requested
- Comments on unchanged code

### Duplicate or Overlapping Behavior
- Similar logic appears in multiple files with tiny changes.
- New function name differs but runtime behavior is same.
- New utility is called once with no extension value.

### Type and Object Integrity Risks
- New inline/ad-hoc types replace established shared types.
- Unsafe casts (for example any-like casting chains) are used to bypass compiler checks.
- Partial objects cross boundaries where full contract is required.

### Import and Boundary Risks
- Imports bypass official integration layers.
- Modules pull in internals from unrelated domains.
- Refactor changes import graph without documenting boundary intent.

### Hardcoded and Fallback Risks
- Magic constants/URLs/keys/thresholds should come from shared config/constants/contracts.
- Fallback/default logic hides errors or masks invalid state.
- Behavior differs across modules due to local hardcoded overrides.

### Hook Safety Risks
- Hook calls appear inside conditionals/logical operators/ternaries.
- Hook calls appear inside loops/callbacks/nested functions.
- Hook call order changes across render paths.
- Transformed or minified patching bypasses source-level hook safety checks.

### Incomplete Delivery Risks
- Acceptance criteria only partially implemented but marked complete.
- Tests cover happy path only while failure/edge paths are omitted.
- Review claim says done but release-risk evidence is missing.

## Severity Guidance

- Blocker: boundary/security breakage, secret hardcoding, nonsense fallback in critical flow, deterministic hook-order violation causing renderer failure, or release-critical work marked complete while incomplete.
- Major: duplicated logic, unsafe casts, partial-object leakage, hardcoded runtime values, fallback logic without requirement, hook-safety gate evidence missing in hook-based UI scope, or unjustified architecture/style drift.
- Minor: local readability/type-shape issues with low blast radius.
- Nit: polish-level naming/style improvements with no material risk.

## Remediation Pattern

For each finding provide:

1. Existing reusable target to adopt.
2. Minimal safe refactor path.
3. Requirement and runtime risk addressed.
4. Validation evidence needed (tests/checks/logs/output).
5. Regression watchpoints in adjacent modules.

## Cross-Reference Load

Pair this file with:

- 21-function-reuse-and-simplicity-review.md
- 25-api-layer-and-contract-review.md
- 27-architecture-modularity-and-maintainability-review.md
- 28-database-query-performance-and-scaling-review.md
- 29-style-formatting-and-readability-review.md
- 40-testing-release-production-readiness-review.md
