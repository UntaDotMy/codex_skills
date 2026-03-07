# `.gitignore` and Secret-Hygiene Review

## Objective

Reduce accidental commits of secrets, machine-local files, generated artifacts, and non-essential repository noise.

## Review Checklist

1. `.gitignore` exists and matches the active stack/tooling.
2. Secrets and credentials are excluded (for example `.env*`, private keys, cert bundles, cloud credentials).
3. Build outputs, caches, and logs are excluded.
4. IDE/OS-local artifacts are excluded.
5. Local-only docs/data/exports are excluded when not required in version control.
6. Allowlist exceptions remain intentional (for example `.env.example`, seed fixtures explicitly needed).
7. Patterns are specific enough to avoid hiding required source files.

## Sensitive File Exposure Checks

- Detect currently tracked sensitive paths before release.
- If secrets are committed, mark at least Major (often Blocker) and recommend:
  1. secret rotation/revocation
  2. history cleanup (for example `git-filter-repo`)
  3. follow-up validation that leaks are removed from reachable refs

## Suggested Baseline Ignore Categories

- Environment/config secrets: `.env`, `.env.*` (keep sample files like `.env.example`)
- Credentials: `*.pem`, `*.key`, `*.p12`, service-account files
- Build outputs: `dist/`, `build/`, `.next/`, `target/`, `out/`
- Dependencies/caches: `node_modules/`, `.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.gradle/`
- Logs/temp: `*.log`, `tmp/`, `.cache/`
- OS/IDE: `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/`

## Remediation Guidance

When gaps are found, provide:

1. Minimal safe `.gitignore` additions.
2. Rationale for each rule.
3. Side effects/trade-offs (what could be accidentally hidden).
4. Verification steps (`git status`, `git check-ignore -v`, targeted repo scan).
