# Recovery and Incident Playbook

## Objective

Recover quickly from common Git mistakes while minimizing additional risk.

## Common Scenarios

### 1) Wrong commit on wrong branch

- If unpublished: user-approved reset/cherry-pick flow.
- If published/shared: prefer revert + new corrective commit.

### 2) Accidental force push or history rewrite

- Use reflog and remote history references to identify lost commits.
- Coordinate recovery plan before pushing restoration changes.

### 3) Merge conflict handling

- Confirm conflict strategy with user (ours/theirs/manual).
- Resolve deterministically, re-run checks, and document conflict decisions.

### 4) Secret accidentally committed

- Treat as security incident:
  - rotate/revoke secret
  - remove exposure from history when required
  - verify no accessible refs still contain the secret

## Safety Rules During Recovery

1. Snapshot current state before risky fixes when possible.
2. Explain rollback path before executing destructive operations.
3. Require explicit user approval for reset/rebase/force-push operations.
4. Prefer reversible operations on shared branches.
