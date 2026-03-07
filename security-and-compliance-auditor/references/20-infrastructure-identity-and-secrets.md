# Infrastructure, Identity, and Secrets

Use this reference when the security posture depends on platform configuration, workload identity, secret handling, or CI/CD behavior.

## Identity and Access

Review for:
- wildcard roles, policies, or group bindings
- human accounts with machine-level privileges
- shared credentials instead of workload identity
- missing separation between read, write, admin, and break-glass privileges
- stale roles, inactive service accounts, and unused access paths
- privilege escalation paths through role creation, binding, or impersonation

Least privilege is not a slogan; show which permission is too broad and what narrower grant should replace it.

## Secrets Lifecycle

Check every stage:
- creation
- storage
- distribution
- runtime access
- rotation
- revocation
- expiration
- auditability

High-risk patterns include:
- secrets in source code, client bundles, container images, or CI variables without control
- secrets echoed in logs, traces, artifacts, or crash dumps
- long-lived credentials with no rotation or revocation plan
- broad namespace or role access to orchestrator-managed secrets
- shared secrets across environments without clear ownership

## CI/CD and Supply Chain

Inspect for:
- overly broad deployment credentials
- unsigned or unverified artifacts where trust requires verification
- secret use in build steps, caches, and report uploads
- dependency or image intake without ownership or advisories review
- pipeline steps that can be triggered from untrusted contexts

## Cloud and Kubernetes Boundaries

Focus on:
- ingress and egress restrictions
- metadata and control-plane exposure
- secret encryption and access policy
- namespace and workload isolation
- workload identity versus static credentials
- role bindings that allow lateral movement or privilege escalation
- operational controls around image admission, rollout, and rollback

## Failure Scenarios to Watch

- a pod can read any secret in its namespace because deployment permissions are too broad
- a cloud role intended for one service is reused by multiple workloads with different trust levels
- a build job can publish artifacts and deploy to production from the same credential set
- a rotation happened in the secret manager but consumers still use cached or baked-in credentials
- a temporary break-glass role becomes permanent because no expiry or review exists

## Runtime Boundaries

Do not claim this area is secure when:
- access is inferred from documentation rather than live policy or manifest review
- secrets are supposedly rotated but consumer reload behavior is unknown
- environment parity is poor and the reviewed policy is not the deployed policy
- incident evidence is missing for who accessed which secret or role and when

## Remediation Bar

A strong infrastructure or secrets remediation:
- narrows permissions to the smallest required action set
- removes static credentials where platform identity is available
- includes rotation, revocation, and validation steps
- closes lateral-movement paths
- improves auditability and owner clarity
