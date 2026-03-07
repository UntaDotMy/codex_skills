# Compliance Response and Remediation

Use this reference when the task needs control evidence, security release gates, or post-incident remediation quality bars.

## Compliance Scope Framing

First determine which regime actually matters:
- SOC 2 for service-organization control evidence
- GDPR when personal data of people in scope is processed
- HIPAA when protected health information and covered obligations are in scope
- internal security policies or contractual commitments that may be stricter than external frameworks

Do not inflate compliance claims beyond the actual product, customer, or geographic scope.

## Evidence Expectations

Compliance-relevant answers should identify:
- the control objective
- the current control or missing control
- the evidence source
- the owner
- the remediation due date or release decision
- the residual risk if the gap remains open

Examples of usable evidence:
- access reviews
- role and policy diffs
- secret rotation records
- audit logs with actor identity
- test or scan results tied to the affected control
- ticketed remediation with verification proof

## Incident and Remediation Workflow

1. Classify the issue: exposure, access control, secret leak, logging gap, or availability/security overlap.
2. Confirm affected systems, data classes, and time window.
3. Contain if needed: revoke, rotate, disable, block, or roll back.
4. Determine whether notification, legal, or compliance escalation is required.
5. Fix the root cause and any adjacent control weakness.
6. Verify closure with technical evidence.
7. Update the control narrative, runbook, and owner record.

## Release Gates

Recommend a compliance or security release block when:
- evidence for a required control is missing
- a material secret exposure lacks completed rotation or revocation
- privileged access changes are unreviewed or unaudited
- logging is insufficient for a sensitive or regulated workflow
- the fix exists but verification evidence is incomplete
- the product would ship with a known high-risk gap and no accepted exception

## Exception Handling

A temporary exception is only acceptable when:
- the business owner and security owner are explicit
- blast radius is understood
- compensating controls are live now
- duration is time-bounded
- follow-up verification is scheduled
- the exception is documented for future review

## Remediation Quality Bar

A remediation is production-grade when:
- the control gap is clearly explained
- containment and permanent fix are distinguished
- required operational follow-through is named
- verification evidence proves closure
- monitoring or auditability improved if that was part of the failure
- lessons learned are specific enough to prevent recurrence

## Common Pitfalls

Reject these patterns:
- saying a policy exists without showing the live control
- saying a secret was revoked without proving where it was used
- calling a scanner clean bill of health a compliance verdict
- treating documentation updates as a substitute for technical closure
