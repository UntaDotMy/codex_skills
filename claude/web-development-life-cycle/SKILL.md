---
name: web-development-life-cycle
description: Web development for websites and web applications. Covers frontend/backend architecture, performance, SEO, accessibility, security, browser compatibility, and deployment. TRIGGER when building web apps, optimizing performance, implementing SEO, or ensuring accessibility.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, WebFetch, WebSearch
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

## Windows Environment

When running commands on Windows:
- Prefer direct command invocation for ordinary commands instead of wrapping them in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required
- Use `cmd.exe /c` for `.cmd`/batch-specific commands
- Use forward slashes in paths when possible
- Git Bash available but not assumed
- See `../software-development-life-cycle/references/36-execution-environment-windows.md` for details

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
