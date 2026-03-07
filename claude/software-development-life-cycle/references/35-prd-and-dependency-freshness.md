# PRD and Dependency Freshness

## Purpose

Use this reference when creating PRDs so they remain clear, current, and implementation-safe.

## PRD Quality Checklist (Production-Oriented)

A PRD is complete when all items below are explicit:

1. Problem statement and target users/personas.
2. In-scope and out-of-scope boundaries.
3. User stories mapped to acceptance criteria.
4. Functional requirements and non-functional requirements.
5. Architecture and integration impact summary.
6. Dependency list with verified versions and compatibility notes.
7. Test strategy (unit, integration, system, regression, UAT).
8. Rollout, rollback, observability, and incident-readiness notes.
9. Risks, mitigations, and open questions.

## Requirement-to-Test Traceability Rule

For each user story:

- Define acceptance criteria in measurable terms.
- Define at least one validation path (test or manual verification step).
- Mark release gate criteria and failure handling.

If a user story and request scope conflict, do one of:

1. Ask concise clarifying questions.
2. Perform focused web research to validate current domain constraints and then proceed with explicit assumptions.

## Dependency Freshness and Accuracy Gate

Never write dependency versions from memory for PRDs.  
Use web-first verification and include verification date.

For each dependency:

1. Verify latest stable release from official source.
2. Verify compatibility with target runtime/framework.
3. Check maintenance signal (recent releases/changelog activity).
4. Check known vulnerabilities/advisories.
5. Prefer pinned or bounded versions with rationale.

## Dependency Verification Examples

- npm: `npm outdated`, `npm view <pkg> version`, official package changelog.
- Python: `pip index versions <pkg>`, `pip-audit`.
- Rust: `cargo audit`, crates.io release page.
- Go: `go list -m -u all`, module release tags/changelog.

Use ecosystem-native tooling available in the target project.

## “No Harm” Delivery Standard

Do not claim zero bugs.  
Use risk-minimizing controls:

- Explicit assumptions and constraints
- Incremental rollout with rollback path
- Coverage of critical user journeys
- Security and dependency checks in CI
- Observability and alerting for key failure modes

## PRD Output Pattern

Structure PRD responses with:

1. Context and goals
2. User stories and acceptance criteria
3. Requirements (functional + non-functional)
4. Dependency table (version, source, verification date, compatibility note)
5. Implementation and testing strategy
6. Release/readiness gates
7. Risks and unresolved questions
