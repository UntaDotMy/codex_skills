# Feedback Style and Remediation Planning

## Human-Reviewer Feedback Principles

- Be direct and specific.
- Focus on impact and risk, not personal preference.
- Provide clear remediation steps and verification guidance.
- Distinguish blockers from optional refinements.
- Consolidate duplicate findings into one root-cause item.
- Keep default feedback concise unless user requests full deep-dive review.

## Finding Template

For each finding:

1. Severity
2. Area (requirements, security, dependency, testing, etc.)
3. Issue summary
4. Why it matters
5. Recommended fix
6. Verification step
7. Evidence/source link

## Remediation Prioritization

Prioritize in this order:

1. Blockers with production safety impact
2. Majors affecting correctness/security/performance
3. Minors affecting maintainability and long-term velocity
4. Nits and polish

## Deduplication Rule

- If one root cause appears in multiple areas, report once and reference impacted areas in that same finding.
- Avoid repeating identical recommendation text in multiple sections.

## Closing the Loop

After fixes:

- Re-validate only changed risk areas first.
- Confirm no regressions on critical paths.
- Update verdict with residual risk statement.
