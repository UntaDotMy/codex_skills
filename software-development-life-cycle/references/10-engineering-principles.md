# Engineering Principles Playbook

## Core Engineering Foundations

Apply these principles in design, implementation, and review:

- Modularity: split systems into cohesive, independent, reusable modules.
- Abstraction: expose stable interfaces and hide implementation details.
- Encapsulation: protect invariants and data through controlled access.
- DRY: remove duplicated logic and duplicated knowledge.
- KISS: prefer simpler designs with lower cognitive load.
- YAGNI: avoid speculative complexity and unused features.
- SOLID: design classes/modules for maintainability, extension, and testability.

## Clean Code and Maintainability Standards

- Use descriptive naming and clear boundaries.
- Keep functions focused and short.
- Handle failures explicitly.
- Maintain consistency with project conventions.
- Prefer composition over deep inheritance.

## Reuse-First Policy

1. Search for existing implementation before creating new code.
2. Reuse shared components/utilities where behavior matches.
3. Extract shared behavior when duplication appears across modules.
4. Record reuse decisions in ADRs or PR notes for traceability.

## Clarification-First Policy

For high-impact ambiguity, ask before implementation:

- Unclear acceptance criteria
- Conflicting requirements
- Underspecified constraints (security, compliance, performance)
- Ambiguous ownership or lifecycle responsibilities

## TDD and Testability Guidance

Use test-driven or test-first workflows where practical:

1. Define expected behavior (acceptance criteria).
2. Write failing unit test for smallest behavior increment.
3. Implement minimal code to pass.
4. Refactor while preserving test green state.
5. Extend with integration/system tests for interfaces and workflows.

## Software Crisis Context

Use the historical software crisis lens to justify disciplined engineering:

- Frequent schedule overruns
- Cost blowouts
- Defect-heavy releases
- Low maintainability of growing codebases

Treat process rigor, measurement, and architecture hygiene as risk controls, not bureaucracy.
