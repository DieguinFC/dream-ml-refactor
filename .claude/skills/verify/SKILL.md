---
name: verify
description: Run the local checks that match the changed files, report their real output, and list the manual checks still needed. Use before committing or opening a PR.
---

Verify the current branch. Report only what you ran, with its real output. Never say a check passed without running it. Reply to the author in Spanish.

## 1. Collect the changed files

- Committed on the branch: `git diff --name-only origin/develop...HEAD`
- Not committed yet: `git status --short`

Run `git fetch origin develop` first if `origin/develop` may be stale.

## 2. Run the checks for each area

Run from the repository root unless noted. Run everything that applies, even after a failure, so the report is complete.

| Changed paths | Checks |
|---|---|
| Any file | `python -m pre_commit run --files <changed files>`: commit hooks, including gitleaks, Ruff errors and artifact blocking |
| `DREAM-ML-backend/**/*.py` | From `DREAM-ML-backend/GEML`, the tests for the touched modules: `python -m pytest <test files> -q`. For changes to shared code, also run `python -m coverage run --source=api,apiTimeSeries -m pytest -q` and `python -m coverage report` |
| `DREAM-ML-frontend/frontend/**` | From that folder: `npm run lint` and `npm test`, plus `npm run build` when `src/` or the build config changed |
| `scripts/ci/**` | `python -m unittest discover -s scripts/ci/tests` |
| `scripts/hooks/**` | `python -m unittest discover -s scripts/hooks/tests` |
| `.claude/hooks/**`, `.claude/settings.json` | `python -m unittest discover -s .claude/hooks/tests` |
| `.pre-commit-config.yaml` | `python -m pre_commit validate-config` |
| `.github/workflows/*.yml` | Parse each file as YAML. If no YAML parser is installed, say so and leave it to CI |

If a tool or dependency is missing locally, for example backend packages or `node_modules`, say which one. Report that check as "not run locally; CI runs it", never as passed. The full backend suite also runs in CI.

## 3. On a failure

- Show the failing output.
- Explain the likely cause.
- Propose a fix.

Never weaken, skip or delete a test, lower a threshold, or add `pragma: no cover` to make a check pass. Changing an existing test needs the author's approval.

## 4. Report

1. A table with one row per check: area, command, result (passed, failed or not run) and the key output line. For tests, that is the summary line, for example "543 passed, 42 skipped".
2. Manual checks still needed, taken from:
   - the issue's acceptance criteria that commands cannot prove
   - "Behavior preservation" in `.github/pull_request_template.md` when backend or frontend code changed

   The author confirms each one before it can be checked in the PR.
