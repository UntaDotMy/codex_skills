# Security Knowledge Map

Use this map to load the minimum security reference set required for the task.

## Capability Matrix

| Need | Primary Reference |
|---|---|
| Threat-model setup and application attack paths | 10-application-threat-modeling.md |
| Identity, secrets, infrastructure, CI/CD, and workload hardening | 20-infrastructure-identity-and-secrets.md |
| Compliance evidence, remediation quality, and release readiness | 30-compliance-response-and-remediation.md |
| Authoritative security standards and official guidance | 99-source-anchors.md |

## Default Security Sequence

1. Identify assets, data classes, and trust boundaries.
2. Build or validate the attack path with concrete evidence.
3. Assess exploitability, blast radius, and containment difficulty.
4. Recommend the root-cause remediation and any temporary compensating controls.
5. Re-verify closure, adjacent variants, and monitoring coverage.
6. Apply release and compliance gates.

## Escalation Triggers

Escalate from a quick checklist into a full playbook response when:
- a secret, credential, or token may be exposed
- the issue touches authn, authz, tenancy, or privileged workflows
- infrastructure permissions or workload identity are involved
- the vulnerability is production-facing or compliance-significant
- the current evidence is too weak to support severity or release decisions
