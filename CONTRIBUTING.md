# Contributing to DREAM ML

These rules apply to every change made during the architectural refactor of DREAM ML, by people and by AI assistants. The reasoning behind them is recorded in [ADR 0001](Docs/adr/0001-development-workflow.md).

All repository text (issues, PRs, commits, code comments and docs) is written in **English**. Existing user-facing strings in the app stay as they are.

## Local setup

Install the commit hooks once per clone, from the repository root:

```bash
python -m pip install pre-commit==4.7.0   # also in requirements-dev.txt
pre-commit install
```

The dev container does this automatically. Run `pre-commit install` again whenever `default_install_hook_types` in `.pre-commit-config.yaml` changes. The hooks only check what each commit or push adds:

| When | Check |
|---|---|
| Commit | Rejects commits to `main` or `develop`, merge conflict markers, large files, secrets and generated artifacts (coverage reports, `db.sqlite3`, `.pyc`, `.DS_Store`); runs Ruff's error rules (`E9,F63,F7,F82`, as in CI) on changed backend Python files |
| Commit message | Adds `Refs #<n>` from the branch name when the message does not mention that issue; rejects messages that are not Conventional Commits and AI co-author trailers |
| Push | Rejects pushes to `main` or `develop` and branch names that do not follow [Naming](#naming) |

Never bypass them with `--no-verify`; if a hook is wrong, fix it in a PR. Their scripts are in `scripts/hooks/`.

## Workflow

```text
Issue → branch from develop → change + tests → local checks → PR to develop
      → CI passes → squash merge → professor reviews later → follow-up PR if needed
```

1. **Issue.** Every change starts from a GitHub issue that meets the [Definition of Ready](#definition-of-ready).
2. **Branch.** Create it from `origin/develop` and name it after the issue (see [Naming](#naming)).
3. **Change.** Keep it to one concern. Add or update tests beside the workflow they exercise.
4. **Local checks.** Run the tests and linters for the parts you touched, and fill in the manual verification in the PR.
5. **Pull request** to `develop`, using the template.
6. **Merge.** Use **Squash and merge** as soon as CI passes. No approval is required on `develop`.
7. **Review.** The professor reviews merged PRs afterwards. Every requested change becomes a new issue and a new PR (see [Professor review](#professor-review)).

Never commit or push directly to `develop` or `main`.

### Releases to `main`

`main` only receives `develop` through a PR, at the end of each phase. That PR is merged with a **merge commit**, so the history of the phase stays visible, and it is tagged (see [Versioning](#versioning)). `main` requires a PR but no approval, so a release never waits on a reviewer.

## Naming

**Branches**

```text
^(feature|fix|refactor|test|docs|ci|chore|hotfix|revert)/[0-9]+-[a-z0-9-]+$
```

Example: `refactor/42-extract-arima-trainer`. Exempt: `main`, `develop`, `dependabot/*`.

**Commits and PR titles** follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
^(feat|fix|refactor|test|docs|ci|build|chore|perf|revert)(\([a-z0-9-]+\))?!?: .{1,72}$
```

Scopes: `api`, `ts`, `core`, `train`, `frontend`, `ci`, `deps`, `docker`, `security`, `baseline`, `docs`, `process`, `release`, `devcontainer`.

**The PR title becomes the permanent commit on `develop`**, because PRs are squash merged. Write it as carefully as a commit message.

Example:

```text
refactor(train): extract ARIMA trainer into its own module

Move the code without changing logic. Characterization tests stay
green and the JSON response is unchanged.

Refs #42
```

Use `Refs #<n>` in commits and `Closes #<n>` in the PR. GitHub only closes an issue automatically when the PR targets the default branch (`main`), so close issues by hand after merging into `develop`.

## Pull requests

### Automatic checks

Two checks must pass before merging:

- `ci-gate` (`.github/workflows/ci.yml`): tests, coverage, lint, build, secret scan and SonarCloud.
- `process` (`.github/workflows/pr-process.yml`): the title and branch follow [Naming](#naming); the body references the issue; every box under **Manual verification** and the AI review box are checked; `Docs/baseline/` only gains files or additive notes in `manifest.json`; Sonar sources, exclusions and issue rules are unchanged unless the owner adds `exception:sonar-config`; a new `skip`, `xfail` or `pragma: no cover` links an issue on the same line.

`process` also adds `flag:test-changed` when existing tests change or new skips appear, and `flag:config-changed` when CI, Sonar, coverage or hook configuration changes, so those PRs get a closer review. It re-runs on every edit of the PR, which is cheap; `ci.yml` does not.

### Size

Keep PRs **under 400 changed lines**. Mechanical moves and generated files are the only exception, and the PR must say so.

### One concern per PR

Open separate PRs for:

- Moving code and changing its logic
- A refactor and a fix or feature
- Mechanical changes (formatting, renames, moves) and anything else

Squash merges keep one commit per PR, so mixing concerns makes the history impossible to bisect or revert cleanly.

### Definition of Ready

An issue is ready when it has:

- Acceptance criteria that can be checked
- The affected modules
- A scope that fits one small PR

### Definition of Done

A PR is done when:

- The required CI checks pass
- The acceptance criteria are met
- No test was weakened, skipped or deleted without a linked issue
- Every manual verification box is checked
- Docs, or an ADR for design decisions, are updated

## Refactor rules

- **Characterize before changing.** Cover the current behavior with tests before restructuring code that has none.
- **A refactor does not change behavior.** Preserve:
  - JSON response shapes and HTTP statuses that the frontend cards expect
  - Routes, including trailing slashes (`/api/ts/run-pipeline` has none)
  - The `pipeline_config.json` format, because `run-pipeline` replays it
  - The order of DVC and Git operations inside experiment directories
  - MLflow experiment, run, metric and artifact names
- `Docs/baseline/` and the `baseline-pre-refactor` tag are **frozen**. Corrections go in a separate PR that adds a note to `Docs/baseline/manifest.json`; the data is never overwritten.

## Tests

- Fixing a failing test by weakening it, skipping it or deleting it is **not allowed**.
- A `skip` or `xfail` must link the issue that tracks it.
- Use the existing pytest markers: `unit`, `integration`, `slow`, `requires_mlflow`, `requires_dvc`.
- Mock narrowly. Patch names where the code under test resolves them (`api.services.pd.read_csv`, not `pd.read_csv`), and never patch `builtins.open` globally.

## Coverage

Enforced by the `backend` job in `.github/workflows/ci.yml`:

| Rule | Threshold |
|---|---|
| Global backend coverage (ratchet) | Starts at **47 %**, the measured baseline rounded down. Raised at the end of each phase, never lowered |
| Changed backend lines in a PR (`diff-cover`) | **95 %** |
| Exception | The `exception:coverage` label, applied only by the repository owner with the reason written in the PR. The shortfall stays visible in the CI run |

Frontend tests run in CI and their coverage is sent to SonarCloud. Frontend coverage thresholds are enforced once `TrainCard` and `TSTrainCard` have tests.

## AI assistants

AI tools (Claude Code, Copilot) may be used, under these permissions:

| On their own | With the author's approval | Never |
|---|---|---|
| Read code, create task branches | The task plan | Push directly to `main` or `develop` |
| Write code and new tests | New dependencies | Force-push to protected branches, or skip checks |
| Run tests and linters | Changing or skipping an existing test | Approve a PR |
| Commit locally | CI, threshold, Sonar or hook changes | Merge to `main` |
| Generate reports | Opening a PR | Grant exceptions or touch the frozen baseline |

Claude Code enforces part of this table through the shared project settings in `.claude/settings.json` and the hooks in `.claude/hooks/` (personal settings go in `.claude/settings.local.json`, which is ignored):

| Hook | When | What it does |
|---|---|---|
| `guard_commands.py` | Before each shell command | Blocks skipping checks (`--no-verify`, `SKIP=`, `core.hooksPath`), `git reset --hard`, `git clean -f`, `git add -A`/`.`/`--all`, `git commit -a`, deleting remote refs, `gh pr merge`, `gh pr review --approve`, `exception:*` labels, changes to rulesets, secrets, variables or repo settings, reading `.env` or `SONAR_TOKEN`, and any change to the `baseline-pre-refactor` tag |

The settings also deny reading `.env` and ask before editing CI, Sonar, coverage, hook or baseline files. Git hooks and GitHub rulesets still apply to every author; these hooks only add what an agent could do outside them. Their tests are in `.claude/hooks/tests` and run in the `process` check.

- Commits are authored by the person responsible for the change. **AI tools are not added as co-authors.**
- Every PR fills in the **AI usage** section of the template: which parts were assisted, and confirmation that the author reviewed and understands the whole diff.
- The author is responsible for every line merged, whoever wrote it.

## Professor review

The professor reviews PRs after they are merged, so work never waits on a review.

| Label | Meaning |
|---|---|
| `review:pending` | Merged, not yet reviewed |
| `review:done` | Reviewed, nothing to change |
| `review:follow-up` | Changes requested; a follow-up issue exists |

When a review requests a change:

1. Open an issue with the **Review follow-up** template, linking the original PR and quoting the comment.
2. Fix it in a new PR that references that issue.
3. Label the original PR `review:follow-up`, and `review:done` once the follow-up is merged.

## Reverting

Revert through a PR, never by force-pushing:

```bash
git switch -c revert/<issue>-<short-name> origin/develop
git revert <commit>
```

The PR title is `revert: <original title>` and explains why.

## Versioning

[Semantic Versioning](https://semver.org/). The starting point is the tag `baseline-pre-refactor`. The end of Phase 0 is tagged `v0.1.0`, and each later phase bumps the minor version.
