# Web State, Security, and Networking

## Coverage

This file covers topics 49 and 31 (web-relevant networking details), and applies core topics 27, 28, 29, 30, 39.

## Web State and Storage

- Cookies: useful for server-managed sessions and browser-mediated auth flows.
- `localStorage`/`sessionStorage`: useful for non-sensitive state with strict XSS controls.
- Avoid storing high-risk secrets in web storage.

## Authentication and Session Patterns

- Prefer secure, HttpOnly, SameSite cookie strategies for browser sessions where possible.
- If token-based flows are used, constrain scope/lifetime and protect refresh flows.
- Separate identity from authorization policies.

## Browser Security Baseline

- Validate and sanitize all untrusted input.
- Encode output for context (HTML/URL/JS/CSS as appropriate).
- Set restrictive content security and transport policies where supported.
- Harden CORS configuration to known origins and methods.

## Networking and API Calls

- Use HTTPS/TLS everywhere.
- Apply explicit timeout and retry behavior in clients.
- Handle partial failures gracefully and communicate state to users.
- Use pagination and incremental fetching for large datasets.
