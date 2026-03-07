# Application Threat Modeling

Use this reference to turn a code change, architecture slice, or incident into a concrete attacker-centered review.

## Threat Modeling Inputs

Always identify:
- assets: secrets, money movement, customer records, admin capabilities, audit data
- actors: anonymous users, authenticated users, admins, internal services, support staff, CI systems
- trust boundaries: browser to server, service to service, public internet to private network, cluster to cloud control plane
- privileged actions: create, update, delete, export, impersonate, approve, refund, rotate, administer
- abuse opportunities: replay, enumeration, scraping, privilege escalation, injection, SSRF, unsafe deserialization, business-flow abuse

## Questions That Matter

- Can an attacker reach the input directly?
- Is authorization enforced at the server boundary or only implied by the client?
- Can identifiers be guessed, enumerated, or replayed across tenants?
- Do error messages, timing, or metadata leak useful information?
- Can one compromised token, role, or secret widen access laterally?
- Would retries, queues, caches, or eventual consistency create unsafe windows?
- Is there enough logging to detect and explain abuse?

## Common Real-World Attack Paths

Prioritize these before exotic findings:
- broken object or function authorization
- weak session invalidation and stale token reuse
- server-side request forgery through integrations or file fetchers
- insecure use of third-party APIs or webhook trust
- mass assignment or unsafe property binding
- hidden admin routes or inconsistent role checks
- sensitive business flow abuse such as coupon farming, account farming, or inventory hoarding

## Investigation Workflow

1. Define the sensitive action and required trust boundary.
2. Trace data and authorization from input to storage or side effect.
3. Identify the missing control or overly broad assumption.
4. Prove reachability with the smallest safe reproduction.
5. Assess how far the attacker can pivot.
6. Recommend control changes plus verification steps.

## Severity and Blast Radius Heuristics

Raise severity when more of these are true:
- exposure is internet-reachable
- no special privileges are required
- sensitive data or privileged action is involved
- exploitation can be automated at scale
- tenant boundaries or admin boundaries can be crossed
- detection is weak or post-event reconstruction is difficult
- rollback or revocation is hard

Lower severity only when constraints are verified, not assumed.

## Remediation Expectations

A complete application-security remediation should:
- enforce authorization and validation at the server boundary
- reduce dangerous defaults and implicit trust
- add tests or validation paths for the exact weakness class
- improve audit signal for future detection and response
- consider adjacent variants of the same issue family
