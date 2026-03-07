# Issue, Branch, and PR Flow

## Objective

Support optional structured collaboration flow when the user explicitly requests it.

## Flow (Optional, User-Requested)

1. Create or confirm issue context.
2. Create branch from agreed base branch.
3. Implement change in small, reviewable commits.
4. Open PR with clear rationale and validation evidence.
5. Address feedback and update PR.
6. Request human review.

## Issue and Branch Guidance

- Keep issue scoped to a clear user problem and acceptance criteria.
- Branch naming should be traceable:
  - `feat/<issue-id>-<short-topic>`
  - `fix/<issue-id>-<short-topic>`
  - `chore/<short-topic>`

## PR Guidance

PR description should include:

- Problem statement
- Solution summary
- Risk and rollback notes
- Validation evidence (tests/lint/build/manual checks)
- Linked issue references (for example closing keywords when appropriate)

## Review Loop Guidance

- Address reviewer comments in focused follow-up commits.
- Re-run relevant checks after each fix cycle.
- Summarize what changed since last review round.
