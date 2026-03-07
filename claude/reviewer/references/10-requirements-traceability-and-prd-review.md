# Requirements Traceability and PRD Review

## Review Goals

- Ensure requested output aligns with user stories and acceptance criteria.
- Detect scope drift, ambiguity, and missing constraints before production.

## PRD Review Checklist

1. Problem statement is explicit and user-centric.
2. Target user/persona and context are clear.
3. In-scope and out-of-scope boundaries are explicit.
4. User stories are testable and linked to acceptance criteria.
5. Non-functional requirements are measurable.
6. Rollout and rollback strategy is present.
7. Dependencies and version constraints are verified and current.
8. Risks and open questions are explicit.

## Traceability Checks

For each user story, verify:

- Requirement exists
- Implementation path exists
- Test/verification path exists
- Release gate exists

Flag missing links as Blocker or Major based on risk.

## Mismatch Handling

If user story and solution mismatch:

1. Ask concise clarifying questions when ambiguity blocks correctness.
2. Perform web research on domain/platform constraints when time-sensitive.
3. Do not finalize a “production-ready” verdict until mismatch is resolved.
