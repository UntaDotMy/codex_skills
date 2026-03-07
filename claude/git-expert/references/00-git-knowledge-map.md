# Git Expert Knowledge Map

Use this map to load only the references needed for the current Git request.

## Capability Matrix

| Need | Primary Reference |
|---|---|
| Safe command selection and write approvals | `10-safe-git-operations.md` |
| Issue -> branch -> PR workflow | `20-issue-branch-pr-flow.md` |
| Review feedback loop and human handoff | `30-review-fix-and-human-handoff.md` |
| Recovery from mistakes (reset/reflog/revert/force push incidents) | `40-recovery-and-incident-playbook.md` |
| Official source validation | `99-source-anchors.md` |

## Quick Sequence

1. Confirm user-approved operation scope.
2. Inspect repository state safely.
3. Execute requested Git workflow with explicit approvals.
4. Run review/fix loop if PR flow is requested.
5. If changes were made, finish with `$reviewer` and human review handoff; for advice-only tasks, reviewer is optional.
