# Web Performance, SEO, and Compatibility

## Coverage

This file covers topics 48, 50, and 51.

## Web Performance Fundamentals

- Track user-centric metrics (including Core Web Vitals concepts).
- Use caching strategy at browser, CDN, and origin layers.
- Optimize delivery with compression, minification, code-splitting, and lazy loading.
- Eliminate render-blocking bottlenecks on critical paths.

## Performance Trade-off Rules

- Profile first; optimize bottlenecks with measurable user impact.
- Balance payload size against client CPU cost.
- Avoid over-fragmented bundles that increase request overhead.

## SEO Fundamentals

- Ensure crawlable content and discoverable internal linking.
- Maintain accurate metadata (title, description, canonical, structured hints where relevant).
- Prevent accidental blocking through robots/noindex misconfiguration.
- Treat performance and accessibility as SEO quality multipliers.

## Browser Compatibility and Progressive Enhancement

- Build baseline functionality that works broadly first.
- Use feature detection before enabling modern APIs.
- Add polyfills only where required by support matrix.
- Test representative browsers and versions defined in project support policy.
