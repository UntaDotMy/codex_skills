# Flake Triage and Release Gates

Use this reference when the test signal is noisy, release confidence is disputed, or a team needs explicit quality stop rules.

## Flake Taxonomy

Classify the flake before choosing the remedy:

- Product race: the system behaves inconsistently because state transitions race or visibility is delayed.
- Automation race: the test asserts before the product reaches a stable state.
- Test-data instability: shared fixtures, reused identities, ordering assumptions, or leaked state.
- Environment drift: browser version, clock skew, feature flags, infrastructure differences, or regional dependencies.
- External dependency instability: third-party failures, sandboxes, emails, queues, or webhooks.
- Observability gap: the failure exists but the current logs and artifacts do not explain it.

## Triage Workflow

1. Preserve evidence from the first failing run.
2. Check whether the failure is new, recently growing, or historically noisy.
3. Re-run in a controlled way:
   - same commit and same environment
   - same commit and different environment
   - different commit and same environment when useful
4. Compare timing, selectors, payloads, logs, and state transitions.
5. Determine whether the root cause is in product code, test code, data, environment, or dependency behavior.
6. Add the smallest durable fix:
   - product race fix
   - stronger state-based assertion
   - isolated fixture or seeded data
   - environment normalization
   - observability upgrade
7. Re-run targeted and adjacent tests.
8. Decide ship, block, or quarantine.

## Quarantine Policy

Quarantine is a temporary containment tool, not resolution.

Only quarantine when all of the following are true:
- the owner is named
- the failure has evidence and a root-cause hypothesis
- the affected business risk is understood
- the test is removed from release gating intentionally, not silently
- follow-up work is scheduled and visible

Do not quarantine tests covering payments, authentication, data integrity, destructive actions, or compliance-critical flows without an explicit release decision from responsible owners.

## Release Gates

### Hard Blocks
Block release when any of the following is true:
- a critical-path journey is red or unexplained
- a known serious flake still affects a critical release gate
- a contract or schema change is unverified
- performance thresholds are materially missed
- the evidence packet is too weak to explain repeated failures
- rollback or containment is unclear for a high-severity defect

### Conditional Release
A release may be conditional only when:
- the issue is low or moderate severity
- blast radius is understood
- monitoring or mitigation is already in place
- owner, next action, and rollback are explicit
- the exception is documented, time-bounded, and intentionally accepted

### Ready to Ship
Recommend release only when:
- critical tests are green for understood reasons
- flakes are either fixed or clearly non-blocking with owner and plan
- representative runtime evidence supports the decision
- known residual risks are named rather than hidden

## Remediation Acceptance Criteria

A flake or release issue is not truly resolved until:
- the root cause category is identified
- the fix removes the unstable condition rather than masking it
- the test remains readable and maintainable
- regression coverage exists at the correct layer
- reporting and artifacts are good enough to shorten the next investigation

## Evidence Pack Checklist

For non-trivial issues, include:
- failing test or scenario name
- first observed date and frequency
- environment, build, commit, and flags
- screenshots, traces, logs, and request identifiers
- owner and disposition
- release recommendation and residual risk
