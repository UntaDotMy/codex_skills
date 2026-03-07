# Security, Data, API, and Networking

## Security Fundamentals

Use the CIA triad as baseline:

- Confidentiality
- Integrity
- Availability

Apply secure-by-default habits:

- Least privilege
- Secure secret handling
- Input validation and output encoding
- Dependency hygiene and patching
- Security testing integrated in CI/CD

Use OWASP Top 10 concepts for web-exposed systems.

## Authentication vs Authorization

- Authentication: verify identity.
- Authorization: verify allowed actions.

Common mechanisms:

- Session cookies for browser sessions
- Tokens (JWT or opaque) for API access
- OAuth2 for delegated authorization
- OpenID Connect for identity layer on top of OAuth2

## Data Fundamentals

### Relational vs NoSQL

- Relational: strict schema and strong transactional support.
- NoSQL: flexible models for scale and workload-specific needs.

### Data Modeling Essentials

- Normalize where consistency is critical.
- Denormalize selectively for query performance.
- Design indexes based on real query patterns.
- Define transaction boundaries intentionally.
- Preserve ACID needs for critical business invariants.

## API Design Fundamentals

### REST Basics

- Resource-oriented URLs
- Correct HTTP methods
- Consistent status code semantics
- Pagination/filter/sort for list endpoints
- Versioning strategy (URI, header, or media type policy)

### GraphQL Basics

- Single endpoint with typed schema
- Client-specified shape
- Use when flexible read aggregation is valuable
- Control complexity/cost with query limits and caching strategy

## Networking Fundamentals

- DNS resolves names to addresses.
- TCP/IP provides reliable transport and routing.
- TLS/HTTPS secures transport confidentiality/integrity.
- CORS controls browser cross-origin request behavior.

## Dependency, Licensing, and Compliance

- Use package manager lockfiles and reproducible builds.
- Follow semantic versioning and upgrade policies.
- Scan for vulnerabilities and outdated components.
- Track third-party licenses and attribution obligations.

## Privacy and Data Protection

- Minimize PII collection.
- Define lawful basis/consent model.
- Apply retention and deletion policies.
- Protect data in transit and at rest.
- Document data flows and access controls.
