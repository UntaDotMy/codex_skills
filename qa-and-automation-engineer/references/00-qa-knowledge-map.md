# QA Knowledge Map

Use this map to load only the references needed for the quality problem in front of you.

## Capability Matrix

| Need | Primary Reference |
|---|---|
| Risk-based planning and minimal reference loading | 10-test-strategy-and-risk-modeling.md |
| Coverage selection across unit, integration, contract, end-to-end, and performance layers | 10-test-strategy-and-risk-modeling.md + 20-e2e-api-performance-practices.md |
| UI journey, API contract, and performance execution details | 20-e2e-api-performance-practices.md |
| Intermittent failures, quarantine rules, and release readiness | 30-flake-triage-and-release-gates.md |
| Official testing, contract, and performance sources | 99-source-anchors.md |

## Default QA Sequence

1. Confirm requirement, critical path, and failure severity.
2. Build a reproduction packet with environment and runtime evidence.
3. Choose the minimum set of test layers that covers the highest risk.
4. Execute narrow tests first, then expand to adjacent regressions.
5. Triage failures into product, automation, data, environment, dependency, or observability buckets.
6. Apply release gates and state residual risk clearly.

## Escalation Triggers

Escalate from simple test guidance into a full playbook response when:
- the defect is intermittent or production-only
- the issue affects payments, auth, destructive actions, or data integrity
- the failure crosses UI, API, queue, or infrastructure boundaries
- release readiness depends on explaining why a green run should be trusted
