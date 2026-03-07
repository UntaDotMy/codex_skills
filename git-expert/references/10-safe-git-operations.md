# Safe Git Operations

## Objective

Keep repository history safe, auditable, and user-approved.

## Approval Rules

Require explicit user confirmation before:

- `git commit`
- `git push`
- `git merge`
- `git rebase`
- `git reset`
- `git revert`
- `git cherry-pick`
- branch/tag deletion
- force push operations

## Safe-First Command Strategy

1. Inspect first:
   - `git status -sb`
   - `git branch -vv`
   - `git remote -v`
   - `git log --oneline --decorate --graph -n <N>`
2. Plan and explain risk.
3. Execute lowest-risk command path.
4. Re-check repository state after each write.

## History Safety Guidance

- Shared branch correction: prefer `git revert`.
- Local unpublished cleanup: `git reset` may be acceptable with user approval.
- Force push only when necessary; prefer `git push --force-with-lease`.

## Commit Quality Guidance

- Keep commits atomic and traceable to a single intent.
- Avoid mixed unrelated changes in one commit.
- Include context in commit body for non-trivial changes.
- Ensure sensitive files and local artifacts are not staged.
- Verify `.gitignore` coverage before first commit in a repository or when new tooling is introduced.
