# Review, Fix, and Human Handoff

## Objective

Close the loop from implementation to human reviewer handoff with clear evidence.

## Review/Fix Loop

1. Run local validation for changed scope.
2. Open/update PR with validation summary.
3. Triage feedback by severity and risk.
4. Apply focused fixes and avoid unrelated rewrites.
5. Re-run validation checks and update PR notes.

## Required Handoff Content

- What changed (concise diff-level summary)
- Why it changed (issue/user story reference)
- How it was validated (commands/results)
- Known residual risks and mitigations

## `$reviewer` Integration

When delivery flow includes PR readiness:

1. Run `$reviewer` on final change set.
2. Resolve Blockers.
3. Resolve or explicitly risk-accept Majors.
4. Re-run `$reviewer` after fixes.
5. Request human review if user requested full collaboration flow.
