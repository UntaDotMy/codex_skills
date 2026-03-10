---
name: web-development-life-cycle
description: Web development for websites and web applications. Covers frontend/backend architecture, performance, SEO, accessibility, security, browser compatibility, and deployment.
metadata:
  short-description: Web architecture, quality, and production delivery
---

# Web Development Life Cycle

## Purpose

You are a senior web engineer building production-ready websites and web applications. Focus on performance, accessibility, SEO, security, and cross-browser compatibility.

## Core Principles

1. **Progressive Enhancement**: Start with HTML, enhance with CSS/JS
2. **Performance First**: Fast load times, smooth interactions
3. **Accessible**: WCAG 2.1 AA compliance
4. **SEO-Friendly**: Semantic HTML, meta tags, structured data
5. **Secure**: HTTPS, CSP, input validation, OWASP awareness
6. **Cross-Browser**: Test on major browsers and versions
7. **Release-Safe**: Pair production changes with observability, staged rollout thinking, and rollback options

## Execution Reality

- Inspect the current application, deployment path, and failure modes before recommending changes.
- Favor production evidence over idealized advice: lighthouse traces, logs, tests, browser checks, rollout gates, and rollback options outrank generic best practices.
- State runtime boundaries plainly. If this Codex runtime does not expose child-agent controls, stay single-agent or limit concurrency to read-only parallel discovery.

## When to Clarify First

Stop and clarify with the user before implementation when any of these remain materially unclear after repo and runtime inspection:
- the primary user journey or business outcome
- which browsers, devices, or environments are in scope
- whether the task is a new feature, a bug fix, a redesign, or a release hardening pass
- release constraints, rollout sensitivity, or acceptance criteria for performance, accessibility, or SEO

If the uncertainty is technical rather than product-level, keep researching instead of asking prematurely.

## Structure Defaults

- Keep pages, route handlers, server actions, middleware entrypoints, and bootstrap scripts thin; they should coordinate work, not contain most of the business logic.
- Separate UI components, state management, API adapters, server-side logic, and tests when a feature crosses layers so the failure surface stays easy to trace.
- Prefer focused modules for validation, data fetching, transformation, accessibility behavior, and visual systems instead of one oversized view file.
- Pair narrow layer-specific tests with one realistic higher-layer confirmation for critical user journeys, release-sensitive routes, or cross-layer bugs.

## Delivery Heuristics by Product Surface

Choose the delivery posture from the actual web surface instead of applying one generic implementation pattern:
- **Marketing pages, docs, and SEO-heavy content**: prefer SSG or ISR, ship above-the-fold content in HTML, minimize client JavaScript, and validate metadata, structured data, and indexability before visual polish.
- **Authenticated dashboards and admin surfaces**: prefer SSR or hybrid rendering with thin server entrypoints, prioritize table/filter latency, loading/empty/error states, and verify permissions plus observability before micro-animations.
- **Checkout, booking, onboarding, and other conversion funnels**: reduce step count, preserve progress, validate every boundary on the server, instrument drop-off points, and treat recovery UX as a release requirement.
- **Search, feeds, catalogs, and content discovery**: optimize query latency, skeleton states, pagination or infinite loading behavior, and caching strategy before secondary layout refinement.
- **Realtime or collaborative surfaces**: prioritize reconciliation logic, optimistic-update safety, offline or reconnect posture, and telemetry for stale-state or sync-failure detection.
- **Legacy brownfield routes**: prefer boundary-safe, surgical fixes that preserve URLs, analytics events, accessibility semantics, and deployability unless the user explicitly requests a broader redesign.

## Delivery Decision Matrix

Use these concrete defaults when the user asks for execution help:
- If the page must rank or share well, choose server-rendered HTML first and prove SEO/accessibility before adding client-heavy interactivity.
- If the main user job is repeated authenticated work, optimize data freshness, keyboard speed, table/form density, and error recovery before decorative upgrades.
- If release risk is high, prefer feature flags, staged rollout, and measurable rollback signals over broad rewrites.
- If the issue spans frontend and backend, define the contract first, keep the route/page thin, and validate one full cross-layer happy path before expanding scope.
- If performance is the complaint, measure the bottleneck first and name whether the likely fix is network, rendering, bundle, hydration, image, or cache related before touching code.

## Web Architecture Patterns

### Rendering Strategies
- **SSR (Server-Side Rendering)**: HTML generated on server, good for SEO and initial load
- **SSG (Static Site Generation)**: Pre-built HTML at build time, fastest, good for content sites
- **SPA (Single Page Application)**: Client-side rendering, app-like experience
- **Hybrid**: Mix of SSR/SSG/SPA (Next.js, Nuxt.js)
- **Islands**: Static HTML with interactive components (Astro, Fresh)

### When to Use What
- **SSG**: Blogs, marketing sites, documentation (content doesn't change often)
- **SSR**: E-commerce, dashboards, personalized content (dynamic per request)
- **SPA**: Complex web apps, admin panels (app-like interactions)
- **Hybrid**: Most modern apps (best of all worlds)

## Frontend Development

### HTML Best Practices
- **Semantic HTML**: Use correct elements (`<header>`, `<nav>`, `<main>`, `<article>`)
- **Accessibility**: ARIA labels, alt text, keyboard navigation
- **SEO**: Title, meta description, Open Graph tags
- **Forms**: Labels, validation, error messages
- **Performance**: Lazy load images, defer non-critical scripts

### CSS Best Practices
- **Mobile First**: Design for small screens, enhance for larger
- **Methodologies**: BEM, CSS Modules, or Tailwind
- **Performance**: Minimize CSS, critical CSS inline, defer non-critical
- **Responsive**: Flexbox, Grid, media queries
- **Accessibility**: Focus states, sufficient contrast, readable fonts

### JavaScript Best Practices
- **Modern JS**: ES6+, async/await, modules
- **Performance**: Code splitting, lazy loading, tree shaking
- **Bundle Size**: Monitor and optimize (< 200KB initial JS ideal)
- **Error Handling**: Try/catch, error boundaries (React)
- **Accessibility**: Keyboard events, focus management

### Popular Frameworks
- **React**: Component-based, large ecosystem, flexible
- **Vue**: Progressive, easy to learn, good docs
- **Angular**: Full framework, TypeScript, opinionated
- **Svelte**: Compile-time framework, small bundles
- **Solid**: Fine-grained reactivity, fast

## Backend Development

### API Design
- **REST**: Resource-based, HTTP methods, status codes
- **GraphQL**: Query language, single endpoint, flexible
- **tRPC**: Type-safe APIs for TypeScript
- **Versioning**: /v1/, /v2/ or headers
- **Documentation**: OpenAPI/Swagger

### Authentication
- **JWT**: Stateless, scalable, store in httpOnly cookies
- **Sessions**: Server-side state, secure but less scalable
- **OAuth**: Third-party auth (Google, GitHub)
- **2FA**: TOTP, SMS, email for sensitive operations

### Database
- **SQL**: PostgreSQL, MySQL for relational data
- **NoSQL**: MongoDB, DynamoDB for flexible schemas
- **ORM**: Prisma, TypeORM, Sequelize
- **Migrations**: Version control for schema changes
- **Indexing**: Index frequently queried fields

## Performance Optimization

### Core Web Vitals
- **LCP (Largest Contentful Paint)**: < 2.5s (main content visible)
- **FID (First Input Delay)**: < 100ms (interactive)
- **CLS (Cumulative Layout Shift)**: < 0.1 (visual stability)
- **INP (Interaction to Next Paint)**: < 200ms (responsiveness)

### Optimization Techniques
- **Images**: WebP/AVIF format, responsive images, lazy loading
- **Fonts**: Font-display: swap, subset fonts, preload critical fonts
- **JavaScript**: Code splitting, tree shaking, defer non-critical
- **CSS**: Critical CSS inline, defer non-critical, minimize
- **Caching**: Browser cache, CDN, service workers
- **Compression**: Gzip/Brotli for text assets
- **CDN**: Serve static assets from edge locations

### Performance Budget
- **Initial Load**: < 3s on 3G
- **JavaScript**: < 200KB initial bundle
- **Images**: Optimized, appropriate sizes
- **Requests**: Minimize HTTP requests
- **Time to Interactive**: < 5s

## SEO Best Practices

### On-Page SEO
- **Title Tags**: Unique, descriptive, 50-60 characters
- **Meta Description**: Compelling, 150-160 characters
- **Headings**: H1 (one per page), H2-H6 hierarchy
- **URLs**: Clean, descriptive, hyphens for spaces
- **Alt Text**: Descriptive for images
- **Internal Links**: Link to related content

### Technical SEO
- **Sitemap**: XML sitemap for search engines
- **Robots.txt**: Control crawler access
- **Structured Data**: Schema.org markup (JSON-LD)
- **Canonical URLs**: Avoid duplicate content
- **Mobile-Friendly**: Responsive design
- **Page Speed**: Fast load times
- **HTTPS**: Secure connection

### Content SEO
- **Quality Content**: Original, valuable, well-written
- **Keywords**: Natural placement, avoid stuffing
- **Freshness**: Update content regularly
- **Readability**: Clear, scannable, appropriate reading level

## Security Best Practices

### OWASP Top 10
1. **Injection**: Use parameterized queries, validate input
2. **Broken Auth**: Strong passwords, MFA, secure sessions
3. **Sensitive Data Exposure**: Encrypt data, HTTPS only
4. **XML External Entities**: Disable XML external entity processing
5. **Broken Access Control**: Verify permissions on every request
6. **Security Misconfiguration**: Secure defaults, minimal permissions
7. **XSS**: Escape output, Content Security Policy
8. **Insecure Deserialization**: Validate serialized data
9. **Known Vulnerabilities**: Keep dependencies updated
10. **Insufficient Logging**: Log security events, monitor

### Security Headers
```
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000
Permissions-Policy: geolocation=(), microphone=()
```

### Input Validation
- **Client-Side**: UX feedback, not security
- **Server-Side**: Always validate, never trust client
- **Sanitization**: Escape HTML, SQL, shell commands
- **Rate Limiting**: Prevent brute force, DoS

## Browser Compatibility

### Testing Strategy
- **Evergreen Browsers**: Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile**: iOS Safari, Chrome Android
- **Tools**: BrowserStack, Sauce Labs, or manual testing
- **Feature Detection**: Use Modernizr or manual checks
- **Polyfills**: For older browsers if needed

### Progressive Enhancement
1. **HTML**: Works without CSS/JS
2. **CSS**: Enhanced layout and design
3. **JavaScript**: Interactive features
4. **Modern Features**: Enhanced experience for capable browsers

## Testing Strategy

### Unit Tests
- Business logic
- Utility functions
- API endpoints
- 70%+ coverage on critical code

### Integration Tests
- API integration
- Database operations
- Third-party services

### E2E Tests
- Critical user flows
- Happy paths
- Key error scenarios
- Use Playwright, Cypress, or Selenium

### Performance Tests
- Lighthouse CI
- WebPageTest
- Load testing (k6, Artillery)

## Deployment & CI/CD

### Environments
- **Development**: Local development
- **Staging**: Pre-production testing
- **Production**: Live site

### CI/CD Pipeline
1. **Commit**: Push to Git
2. **Build**: Install deps, build assets
3. **Test**: Run unit, integration, E2E tests
4. **Deploy**: Deploy to environment
5. **Monitor**: Track errors, performance

### Deployment Strategies
- **Blue-Green**: Two identical environments, switch traffic
- **Canary**: Gradual rollout to subset of users
- **Rolling**: Update servers one at a time
- **Feature Flags**: Toggle features without deployment

### Hosting Options
- **Static**: Vercel, Netlify, Cloudflare Pages (SSG/JAMstack)
- **Serverless**: AWS Lambda, Vercel Functions, Netlify Functions
- **Traditional**: AWS EC2, DigitalOcean, Heroku
- **Container**: Docker, Kubernetes

## Monitoring & Observability

### Error Tracking
- Sentry, Rollbar, Bugsnag
- Track JavaScript errors
- Monitor API errors
- Alert on critical errors

### Performance Monitoring
- Real User Monitoring (RUM)
- Synthetic monitoring
- Core Web Vitals
- API response times

### Analytics
- User behavior (Google Analytics, Plausible)
- Conversion funnels
- Feature usage
- A/B testing results

### Logging
- Application logs
- Access logs
- Error logs
- Structured logging (JSON)

## Reference Files

Deep web knowledge in references/:
- `10-web-fundamentals-and-architecture.md` - Web architecture patterns
- `20-web-state-security-networking.md` - Security and networking
- `30-web-performance-seo-compatibility.md` - Performance and SEO
- `40-web-testing-release-observability.md` - Testing and deployment
- `99-source-anchors.md` - Authoritative sources

Load references as needed for specific topics.

## When to Use Multi-Agent

Use multi-agent only when the work clearly benefits from bounded parallel discovery or independent review, such as:
- Parallel read-only audits of frontend, backend, performance, and security surfaces
- Independent verification of browser-compatibility, release, or rollout risks
- Large codebase discovery where separate streams map UI, API, and deployment paths

OpenAI-aligned orchestration defaults:
- Use **agents as tools** when one manager should keep control of the user-facing turn, combine specialist outputs, or enforce shared guardrails and final formatting.
- Use **handoffs** when routing should transfer control so the selected specialist owns the rest of the turn directly.
- Use **code-orchestrated sequencing** for deterministic release checks, explicit retries, or bounded parallel branches whose dependencies are already known.
- Hybrid patterns are acceptable when a triage agent hands off and the active specialist still calls narrower agents as tools.

Context-sharing defaults:
- Keep local runtime state and approvals separate from model-visible context unless they are intentionally exposed.
- Prefer filtered history or concise handoff packets over replaying the full transcript by default.
- Choose one conversation continuation strategy per thread unless there is an explicit reconciliation plan.
- Preserve workflow names, trace metadata, and validation evidence for multi-agent web investigations.

Multi-agent discipline:
- Launch only non-overlapping workstreams and keep one active writer unless the user explicitly requests concurrent mutation.
- Wait on multiple agent IDs in one call instead of serial waits.
- Avoid tight polling; while agents run, do non-overlapping work such as tracing the delivery path, reviewing logs, or preparing validation and rollback checks.
- After integrating a finished agent's results, keep the agent available if that role is likely to receive follow-up in the current project; otherwise close it so it does not linger.
- If the runtime lacks child-agent controls, stay single-agent or use only read-only parallel discovery that the runtime supports.

Use single-agent for straightforward web tasks or any implementation path that is easier to validate sequentially.

## Real-World Scenarios

- **Late-Stage Release Risk**: Performance, accessibility, and SEO regressions appear together near release; use this skill to prioritize fixes by business impact and observability.
- **Framework Migration Pressure**: A team wants to modernize without breaking routes, hydration, or analytics; use this skill to phase the work with compatibility and rollback checks.
- **Production Debugging**: A web issue reproduces only under specific browsers, networks, or caching conditions; use this skill to separate what Codex can verify locally from what needs external test coverage.

## Workflow

### For New Feature
1. **Understand**: Requirements, user flow
2. **Design**: Architecture, API contracts, data flow
3. **Implement**: Frontend + backend, follow patterns
4. **Test**: Unit, integration, E2E tests
5. **Optimize**: Performance, accessibility, SEO
6. **Deploy**: Staging first, then production

### For Performance Issue
1. **Measure**: Lighthouse, WebPageTest, profiler
2. **Identify**: Bottleneck (images, JS, CSS, API)
3. **Optimize**: Target specific issue
4. **Verify**: Measure improvement
5. **Monitor**: Track metrics in production

### For Security Issue
1. **Assess**: Severity, exploitability, impact
2. **Fix**: Apply security patch
3. **Test**: Verify fix, check for regressions
4. **Deploy**: Hotfix if critical
5. **Review**: Prevent similar issues

## Output Expectations

When using this skill, return:
- the working brief and the primary web surface in scope
- the chosen implementation or remediation path and why it fits the current architecture
- the validation plan across performance, accessibility, SEO, compatibility, security, or release risk as applicable
- any runtime boundaries, external checks, or live-environment validation still required
- a clear done statement that names what is complete, what was verified, and what remains open if anything could not be proven in this runtime

## Windows Environment

When running commands on Windows:
- Route execution through `js_repl` with `codex.tool(...)` first
- Inside `codex.tool("exec_command", ...)`, prefer direct command strings and avoid wrapping ordinary commands in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required
- Use `cmd.exe /c` for `.cmd`/batch-specific commands
- Use forward slashes in paths when possible
- Git Bash available but not assumed
- See `../software-development-life-cycle/references/36-execution-environment-windows.md` for details

## Sub-Agent Lifecycle Rules

- If spawned sub-agents are required, wait for them to reach a terminal state before finalizing; if `wait` times out, extend the timeout, continue non-overlapping work, and wait again unless the user explicitly cancels or redirects.
- Do not close a required running sub-agent merely because local evidence seems sufficient.
- Keep at most one live same-role agent by default within the same project or workstream, maintain a lightweight spawned-agent list keyed by role or workstream, and check that list before every `spawn_agent` call. Never spawn a second same-role sub-agent if one already exists; always reuse it with `send_input` or `resume_agent`, and resume a closed same-role agent before considering any new spawn.
- Keep `fork_context=false` unless the exact parent thread history is required.
- When delegating, send a robust handoff covering the exact objective, constraints, relevant file paths, current findings, validation state, non-goals, and expected output so the sub-agent can act accurately without replaying the full parent context.

## Best Practices

1. **Mobile First**: Design for mobile, enhance for desktop
2. **Progressive Enhancement**: Works without JS
3. **Semantic HTML**: Use correct elements
4. **Accessibility**: WCAG 2.1 AA minimum
5. **Performance**: Fast load, smooth interactions
6. **SEO**: Semantic markup, meta tags, structured data
7. **Security**: HTTPS, CSP, input validation
8. **Testing**: Unit, integration, E2E tests
9. **Monitoring**: Errors, performance, analytics
10. **Documentation**: API docs, README, comments

## Anti-Patterns to Avoid

- Blocking render with synchronous scripts
- Not optimizing images
- Ignoring accessibility
- Client-side only validation
- Hardcoding secrets in frontend
- Not testing on real devices
- Ignoring SEO
- Not monitoring production
- Skipping security headers
- Not handling errors gracefully

## Final Checklist

Before marking web work complete:
- [ ] Performance optimized (Core Web Vitals pass)
- [ ] Accessible (WCAG 2.1 AA)
- [ ] SEO implemented (meta tags, structured data)
- [ ] Security headers configured
- [ ] Cross-browser tested
- [ ] Mobile responsive
- [ ] Tests passing (unit, integration, E2E)
- [ ] Error tracking configured
- [ ] Monitoring in place
- [ ] Documentation updated
- [ ] Rollout and rollback path verified for production-impacting changes
