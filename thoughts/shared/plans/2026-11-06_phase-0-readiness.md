# Phase -1: Development Process Setup

| | |
|---|---|
| **Status** | Draft for approval. Nothing here has been executed. |
| **Date** | 2026-11-06 |
| **Goal** | Build the six process layers so that Phase 0 runs through one standard, enforced flow |
| **Effort** | 6 to 7 working days (my estimate) |
| **Exit** | Every box in [Exit checklist](#exit-checklist) is checked, then Phase 0 continues from task 0.8 |

## 1. What this phase builds

| Layer | Function | Enforced by | Block |
|---|---|---|---|
| `CONTRIBUTING.md` | Official rules, also for people | Nobody, it is the reference | C |
| `CLAUDE.md` | Short summary that links to the rules | AI, no guarantee | C |
| Skills | Repeatable procedures | AI, when invoked | G |
| Claude hooks | Block dangerous AI actions | Claude Code | F |
| `pre-commit` | Checks messages, secrets and artifacts | Local Git | D |
| CI and rulesets | Last barrier: nothing enters without passing | GitHub | E, H |

**Build order differs from this table on purpose:**

```text
A Access and tools → B Baseline → C Rules → D pre-commit → E CI
                                                             ↓
              J Pilot ← I Prove the gates ← H Rulesets ← G Skills ← F Hooks
```

- Rules come first, because each later layer implements them.
- Rulesets come late, because a required check that does not work yet would block every PR, including the one that fixes it.
- Skills come after hooks and CI, because they rely on both.

### Tasks taken from Phase 0

Phase -1 absorbs tasks that it cannot work without. Phase 0 should mark them as done.

| Task | Done in |
|---|---|
| 0.1 Sonar profile | A5 |
| 0.2 Working branch (replaced by `develop`) | B1 |
| 0.3 Baseline freeze | B2 to B5 |
| 0.4 to 0.7 CI fixes | E1 to E4 |
| 0.39 Vitest (new task) | E5 |

Phase -1 also uses two tasks as a pilot: 0.16 and 0.14.

## 2. Working rules during this phase

Rulesets for `develop` only exist from block H. Until then, these are followed by hand:

1. Every change goes through a PR. No direct pushes, except creating `develop` in B1.
2. Merge to `develop` by squash; PR titles use Conventional Commits, and everything is in English.
3. You review each PR yourself, because the gates are not complete yet.
4. Stage files by explicit path. Never use `git add -A` or `git add .` while untracked evidence and artifacts exist.
5. The professor approves anything going to `main`, enforced from A3.

## 3. Default decisions

You have not confirmed these yet, so the plan uses my recommendations. Tell me if you want to change any; each one names what it affects.

| # | Decision | Default | Affects |
|---|---|---|---|
| D1 | When `develop → main` happens | Baseline now, then at each phase end | B6 |
| D2 | Move the baseline to `main` immediately | Yes | B6 |
| D3 | Running `/open-pr` counts as your authorization | Yes, after a summary you confirm | G |
| D4 | Scope of the 95 % gate | Changed backend lines now; frontend when card tests exist | E3 |
| D5 | One CI run instead of two | Yes | E |
| D6 | Working environment | Devcontainer from block C onward | A4, C1 |
| D7 | Sonar gate is required | Yes, unless the A5 and I1 results show it blocks mechanical work | E3, H |
| D8 | Sprint length | One week, aligned with the professor meeting | J1 |

## 4. Summary of steps and PRs

| Block | Steps | PR to `develop` | Who | Effort |
|---|---|---|---|---|
| A | Access and tools | None | You | 0.5 day |
| B | Baseline | `docs(baseline): freeze pre-refactor metrics` | You + Claude | 1 day |
| C | Rules | `chore(devcontainer): align environment with CI`; `docs(process): add contribution standards` | Claude, you review | 1 day |
| D | `pre-commit` | `chore(process): add pre-commit checks` | Claude, you review | 0.25 day |
| E | CI | `ci: unify backend, frontend and sonar pipelines`; `ci: add pull request process checks`; `test(frontend): add vitest setup` | Claude, you review | 1.5 days |
| F | Hooks | `chore(process): add claude command guards` | Claude, you review | 0.25 day |
| G | Skills | `chore(process): add claude workflow skills` | Claude, you review | 0.5 day |
| H | Rulesets | None | You | 0.1 day |
| I | Gate tests | Throwaway PRs, never merged | You + Claude | 0.5 day |
| J | Backlog and pilot | Two pilot PRs | You + Claude | 0.5 day |

---

## Block A: Access and tools

Done on Windows, because the devcontainer is fixed later, in C1.

### A1. Install `gh`

```powershell
winget install GitHub.cli
gh auth login
gh auth refresh -s project
gh auth status
```

**Done when:** `gh auth status` shows `DieguinFC` with the `repo`, `workflow` and `project` scopes.

### A2. Add the professor

Ask the professor for:

- [ ] A GitHub username, and acceptance of the collaborator invitation with **write** access. Approvals from people without it do not satisfy a ruleset.
- [ ] Agreement with the workflow: post-merge review on `develop`, approval on `main`.
- [ ] Agreement that the first PR to `main` is administrative, since it brings existing code forward.

```bash
gh api -X PUT repos/DieguinFC/dream-ml-refactor/collaborators/<professor> -f permission=push
```

**Only write access and that one approval block this phase.** The thesis questions in your plan (duplication, smells, complexity, `train.py`, the 95 % versus 65 % coverage target) do not. The export in B3 holds raw, per-file data, so any later definition can be computed from it.

### A3. Configure the repository

```bash
gh repo edit DieguinFC/dream-ml-refactor \
  --enable-squash-merge --enable-merge-commit --enable-rebase-merge=false \
  --enable-auto-merge --delete-branch-on-merge
gh api -X PATCH repos/DieguinFC/dream-ml-refactor \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=COMMIT_MESSAGES
```

Then create the first `main` ruleset in **Settings → Rules → Rulesets**:

| Setting | Value |
|---|---|
| Name | `protect-main` |
| Target | `main` |
| Require a pull request | 1 approval |
| Dismiss stale approvals | On |
| Block force pushes | On |
| Restrict deletions | On |
| Bypass list | Empty |

**Done when:** `git push origin main` with a test commit is rejected. Reset your local `main` afterward.

### A4. Clear pending items

- [ ] Close the Copilot PR #1 after checking its one commit, and delete its branch.
- [ ] Add local-only exclusions, so these can never be staged by accident:

```bash
printf '%s\n' 'punto.md' 'Sonar tests/Propuesta Refactor DreamML.docx' >> .git/info/exclude
```

### A5. Confirm Sonar (task 0.1)

Sign in to SonarCloud, then:

- [ ] Record the quality profile for Python, JavaScript and Docker.
- [ ] Record the gate name and all its conditions. **Check specifically whether new-code coverage is included.** The API shows it for `main` but not for `init-refactor-documents`.
- [ ] Decide on the name: either correct the proposal, or change the profile and rerun the analysis **before B1**.
- [ ] Create a token and load it only in your shell: `$env:SONAR_TOKEN = "..."`.

**Done when:** those values are ready for `manifest.json` in B4.

---

## Block B: Baseline

**No other PR is opened until B5 finishes.**

### B1. Tag and branch

```bash
git fetch origin
git tag -a baseline-pre-refactor e02c0bb -m "Baseline before any refactor or cleanup"
git push origin baseline-pre-refactor
git push origin e02c0bb:refs/heads/develop
```

Keep `init-refactor-documents` frozen and undeleted, because SonarCloud holds the baseline analysis under that name.

**Done when:** `git rev-parse baseline-pre-refactor^{commit} origin/develop` prints `e02c0bb...` twice.

### B2. Create the issue and branch

```bash
gh issue create --title "[0.3] Freeze the pre-refactor baseline" \
  --body "Export baseline data for commit e02c0bb to Docs/baseline/."
git switch -c docs/<issue>-freeze-baseline origin/develop
```

### B3. Export the data

Claude writes `Docs/baseline/export_sonar.py`, using only the standard library. It reads `SONAR_TOKEN` from the environment, and is reused at task 0.38.

| File in `Docs/baseline/` | Source |
|---|---|
| `sonar-measures.json` | `api/measures/component`, `branch=init-refactor-documents` |
| `sonar-measures-by-file.json` | `api/measures/component_tree`, paginated |
| `sonar-issues.json` | `api/issues/search`, paginated |
| `sonar-hotspots.json` | `api/hotspots/search` |
| `sonar-dependency-risks.json` | Sonar's dependency risk export. **The endpoint is unverified**; export from the web UI if the API does not offer it |
| `pip-audit.json` | `pip-audit` on both requirements files, pinned versions only |
| `npm-audit.json` | `npm audit --json` in the frontend |
| `coverage.xml`, `test-results.xml`, `coverage-report.txt` | `gh run download 42134886141 -n backend-test-and-coverage-reports` |
| `sonar-project.properties` | Copied from the commit |
| `sonar-run-13.txt` | Copied from the untracked `Sonar tests/SonarCloud13.txt` |

**Metrics to request:** `ncloc`, `functions`, `complexity`, `cognitive_complexity`, `coverage`, `lines_to_cover`, `uncovered_lines`, `duplicated_lines_density`, `duplicated_blocks`, `duplicated_lines`, `code_smells`, `bugs`, `vulnerabilities`, `security_hotspots`, `sqale_index`, `sqale_rating`, `reliability_rating`, `security_rating`.

If the CI artifact has expired, stop and tell me; re-running tests at `e02c0bb` would need to be recorded as a separate run.

### B4. Write the manifest and README

`manifest.json` records:

- Commit, tag, Sonar analysis date, CI run ID
- Profile and gate from A5
- `sonar.exclusions` hash
- Tool versions and export date

`README.md` explains how the data was obtained, how to rerun the script, and that later metrics must use the same settings.

### B5. Baseline PR

**Checks before merging:**

```bash
git diff --name-status origin/develop...HEAD   # Only "A" lines under Docs/baseline/
```

- [ ] Exported values: 212 vulnerabilities, 223 smells, 3 bugs, 23.5 % duplication, 36.1 % coverage, 277 dependency risks.
- [ ] A search for the token value and for `sonar_` tokens finds nothing.

Merge by squash. No CI runs on this PR: the workflows at this commit only target `main` and `init-refactor-documents`.

**After merging, verify:**

```bash
gh workflow run sonarcloud.yml --ref develop
```

The analysis of `develop` must equal the baseline. `Docs/` is outside `sonar.sources`, so **any difference means something is wrong. Stop and investigate.**

### B6. Bring the baseline to `main`

```bash
gh pr create --base main --head develop \
  --title "chore(release): bring pre-refactor baseline to main" \
  --reviewer <professor>
```

The professor approves, and you merge with a merge commit. Then run `gh workflow run sonarcloud.yml --ref main`, so SonarCloud's default view shows the baseline.

**This depends on the professor but does not block block C.** Work can continue on `develop` while it waits.

---

## Block C: Rules (`CONTRIBUTING.md`, `CLAUDE.md`)

### C1. Devcontainer PR

Change `.devcontainer/devcontainer.json`:

| Change | Why |
|---|---|
| Node feature `18` → `20` | Matches CI |
| Add the `github-cli` feature | Needed by the workflow |
| Add the Claude Code devcontainer feature | D6 |
| `EXPERIMENTS_DIR` and `HOST_EXPERIMENTS_DIR` use the current workspace, not `/workspaces/dream-ml-c` | The path is stale |
| Add `pre-commit` installation to `postCreateCommand` | Layer D |

Also commit `.devcontainer/devcontainer-lock.json`.

**Line endings:** Git converts files to CRLF on your Windows checkout (`core.autocrlf=true`), and the repo has no `.gitattributes`. That is a problem for shell scripts in a Linux container. So:

- Add `.gitattributes` with `* text=auto eol=lf`, plus `*.bat` and `*.ps1` as `eol=crlf`, and common binaries as `binary`.
- Use **Dev Containers: Clone Repository in Container Volume**. This avoids CRLF and slow Windows file access. Your untracked evidence stays in the Windows clone.

**Done when, inside the container:**

```bash
python --version            # 3.11.x
node --version              # v20.x
gh auth status
git status                  # clean
cd DREAM-ML-backend/GEML && pytest tests/api_tests tests/apiTimeSeries_tests
```

The last command should match CI: 543 passed, 42 skipped, 0 failed, in about 20 minutes. **Any difference is a parity problem to resolve now**, not later.

### C2. Write `CONTRIBUTING.md`

| Section | Required content |
|---|---|
| Flow | Issue → branch → change + tests → `/verify` → `/open-pr` → CI → auto-squash → later professor review → new PR if needed |
| Branches | Rule in [Reference R1](#r1-naming) |
| Commits and titles | Rule in Reference R1. The PR title becomes the permanent commit |
| PR size | Under 400 changed lines, except mechanical moves |
| Separate PRs | Moving code versus changing logic; refactor versus fix or feature; mechanical changes versus anything else |
| Definition of Ready | Issue has acceptance criteria, affected modules, and fits one small PR |
| Definition of Done | `ci-gate` and `process` pass; criteria met; no test weakened; manual checks done; docs or ADR updated |
| Coverage | Global ratchet, 95 % of changed backend lines, one exception route |
| Refactor rules | Characterize before changing; preserve JSON, HTTP statuses, routes, `pipeline_config.json` format, DVC and Git order, and MLflow names |
| Tests | Fixing a failure by weakening or skipping a test is not allowed. A `skip` requires a linked issue |
| AI rules | The table in [Reference R5](#r5-ai-permissions), `Co-Authored-By`, the PR's AI section |
| Professor review | Labels, how comments become issues, and how `main` is approved |
| Reverting | Always through a `revert` PR |
| Versioning | SemVer; `baseline-pre-refactor`, then `v0.1.0` at the end of Phase 0 |

### C3. Add templates and records

| File | Content |
|---|---|
| `.github/pull_request_template.md` | [Reference R2](#r2-pull-request-template) |
| `.github/ISSUE_TEMPLATE/task.yml` | Phase, objective, description, acceptance criteria, affected modules, verification, risks |
| `.github/ISSUE_TEMPLATE/bug.yml` | Observed, expected, reproduction, evidence |
| `.github/ISSUE_TEMPLATE/review-follow-up.yml` | Original PR, professor's comment, required change |
| `Docs/adr/0000-template.md` | Context, decision, alternatives, consequences |
| `Docs/adr/0001-development-workflow.md` | This process and why, useful later for the thesis |

### C4. Update `CLAUDE.md`

Add the section in [Reference R3](#r3-claudemd-section), and also:

- Change the line about CI and branches to describe `ci.yml` after block E.
- Remove the `--fail-under=75` command.
- Replace the duplicated content in `.github/copilot-instructions.md` with a link to `CONTRIBUTING.md` and `CLAUDE.md`.

Commit the currently untracked `CLAUDE.md`, `.github/copilot-instructions.md` and this plan in this PR.

---

## Block D: `pre-commit`

### D1. Add the configuration

`.pre-commit-config.yaml` (Claude fills in the current pinned versions when implementing):

```yaml
default_install_hook_types: [pre-commit, commit-msg]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: <pinned>
    hooks:
      - id: no-commit-to-branch
        args: [--branch, main, --branch, develop]
      - id: check-merge-conflict
      - id: check-added-large-files
        exclude: ^Docs/baseline/
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: <pinned>
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, refactor, test, docs, ci, build, chore, perf, revert]
  - repo: https://github.com/gitleaks/gitleaks
    rev: <pinned>
    hooks:
      - id: gitleaks
  - repo: local
    hooks:
      - id: block-artifacts
        name: Block generated artifacts
        language: fail
        entry: Generated artifact must not be committed
        files: (^|/)(\.coverage|coverage\.(xml|json)|test-results\.xml|db\.sqlite3|\.DS_Store)$|,cover$|\.pyc$|(^|/)htmlcov/
        exclude: ^Docs/baseline/
```

**Deliberately not included:** Ruff, ESLint or Prettier as formatters. Reformatting files of thousands of lines would hide real changes. Lint runs in CI.

Add `pre-commit` to `requirements-dev.txt` at a pinned version.

### D2. Install and test

```bash
pre-commit install
pre-commit run --all-files --hook-stage pre-commit
```

Existing tracked artifacts and the old secret may fail on `--all-files`. Those are removed by tasks 0.8 and 0.21, so **do not fix them here**; just confirm that the failures are exactly those.

**Done when:**

| Test | Expected |
|---|---|
| Commit on `develop` | Rejected |
| Message `fixed stuff` | Rejected |
| Staging a `coverage.xml` | Rejected |
| Staging a fake secret | Rejected |
| Valid commit on a task branch | Accepted |

---

## Block E: CI

### E1. Create `ci.yml` (tasks 0.4 to 0.7)

Replaces `django.yml` and `sonarcloud.yml`, which are deleted in the same PR.

```text
on: pull_request (opened, synchronize, reopened) to develop, main
    push to develop, main
    workflow_dispatch

changes ─┬─► backend ──┐
         ├─► frontend ─┼─► sonar ─┐
         ├─► docker ───┼──────────┼─► ci-gate
         └─► secrets ──┴──────────┘
```

| Job | Runs | Steps |
|---|---|---|
| `changes` | Always | Path filter: backend, frontend, docker, ci |
| `backend` | On a PR if backend or CI changed; **always on push** | Install, migrate, tests with coverage and timeout, ratchet, `diff-cover`, Ruff |
| `frontend` | On a PR if frontend or CI changed; **always on push** | `npm ci`, lint, build, tests with lcov |
| `docker` | Dockerfile, compose, or requirements changed | Build backend and frontend images |
| `secrets` | Always | `gitleaks` on the diff range |
| `sonar` | If backend or frontend ran | Download reports, scan, wait for the gate |
| `ci-gate` | Always, `if: always()` | Fails if any job failed or was cancelled; `skipped` is accepted |

**Why jobs always run on push:** a `develop` analysis without coverage reports would make coverage appear to be 0 % in Sonar.

**Why one final job:** a required check skipped by a path filter stays pending forever.

### E2. Test command details

```bash
python -m coverage run --source=api,apiTimeSeries -m pytest \
  tests/api_tests tests/apiTimeSeries_tests \
  -ra --tb=short --durations=30 --timeout=1800 --timeout-method=signal \
  --junitxml=test-results.xml
python -m coverage xml -o coverage.xml
```

| Fix | Task |
|---|---|
| `GEML.settings`, the correct package name | 0.4 |
| `contents: read`; extra permissions only per job | 0.4 |
| Same coverage command for CI and Sonar | 0.4 |
| A test failure fails the job, while Sonar still publishes | 0.5 |
| Sonar runs on `develop`, `main` and PRs; `init-refactor-documents` is removed | 0.6 |
| `pytest-timeout` pinned in `requirements-dev.txt` | 0.7 |

### E3. Quality gates

| Gate | Where | Value |
|---|---|---|
| Global backend coverage | `coverage report --fail-under=47` | Starts at the measured value rounded down; raised at phase ends |
| Changed backend lines | `diff-cover coverage.xml --compare-branch=origin/$BASE --fail-under=95` | 95 % |
| Exception | Step reads labels with `gh pr view`, so a rerun sees them | With `exception:coverage`, `diff-cover` reports without failing |
| Lint | `ruff check --select E9,F63,F7,F82` | Must be 0 at the start. If not, limit to changed files until 0.20 |
| Frontend lint | `npm run lint` | Warnings allowed until 0.15 adds `--max-warnings=0` |
| Sonar gate | `sonar.qualitygate.wait=true` | See D7 and I1 |

**To validate during implementation:** whether `diff-cover` maps the paths in `coverage.xml` correctly, given that tests run from `DREAM-ML-backend/GEML`.

Add `diff-cover` and `ruff` to `requirements-dev.txt` at pinned versions.

**Dependabot:** those PRs don't get normal secrets, so the `sonar` job must be skipped for them, or use a Dependabot secret.

**`dependency-security.yml`:** keep it separate and not required, because `scan.sh` may fail until task 0.27. Limit it to the schedule, manual runs and PRs that change dependency files.

### E4. Add process checks

A **separate** `.github/workflows/pr-process.yml` runs on `opened`, `edited`, `synchronize`, `reopened`, `labeled`, `unlabeled`.

**Why separate:** ticking a box edits the PR. In `ci.yml`, that would restart a 20-minute test run. This means **two required checks**: `ci-gate` and `process`.

`scripts/ci/check_pr.py` uses only the standard library and has unit tests:

| Check | Result |
|---|---|
| Title matches the rule | Fail if not |
| Branch name matches the rule | Fail if not |
| PR body contains `Closes #` or `Refs #` | Fail if not |
| Any unchecked box under `## Manual verification` | Fail |
| Existing test file modified | Add `flag:test-changed` |
| New `skip`, `xfail` or `pragma: no cover` | Add `flag:test-changed`; fail without an issue link on the same line |
| Workflow, Sonar, coverage or `.claude/hooks` config changed | Add `flag:config-changed` |
| `Docs/baseline/` changed, other than additions | Fail |
| `sonar-project.properties` rules or exclusions changed | Fail, unless you add `exception:sonar-config` |

**Security details:**
- Pass the title, body and branch name through `env:`, never by interpolating them into shell. Those fields can contain commands.
- Use `pull_request`, not `pull_request_target`.

### E5. Add Vitest (task 0.39)

```bash
npm install -D vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom
```

- Choose a Vitest version compatible with the project's Vite 5.
- Add a separate `vitest.config.js`, so the current `vite.config.js` does not change.
- Add scripts: `"test": "vitest run"`, `"test:coverage": "vitest run --coverage"`.
- Add one smoke test.
- Add `sonar.javascript.lcov.reportPaths` to `sonar-project.properties`, and record it in `Docs/baseline/README.md`.

**Put tests in `frontend/tests/`, outside `src/`.** `sonar.sources` includes `src`, so tests inside it would require a new exclusion, and your evaluation requires exclusions to stay frozen.

The frontend 95 % gate is **not active yet**. It starts after the TrainCard and TSTrainCard tests exist.

### E6. Validate

Each PR in this block must show its own workflows running on the PR.

**Done when:**

- [ ] `ci-gate` and `process` are green on the last PR.
- [ ] A `.md`-only PR skips the heavy jobs and `ci-gate` stays green.
- [ ] The push to `develop` runs everything, and Sonar still reports backend coverage.

---

## Block F: Claude hooks

### F1. Version `.claude/`

Replace `.claude/` on line 23 of `.gitignore`:

```gitignore
.claude/*
!.claude/settings.json
!.claude/hooks/
!.claude/skills/
```

### F2. Add settings

`.claude/settings.json`:

```json
{
  "permissions": {
    "deny": ["Read(./.env)", "Edit(./.env)"],
    "ask": [
      "Edit(./.github/workflows/**)",
      "Edit(./sonar-project.properties)",
      "Edit(./DREAM-ML-backend/GEML/.coveragerc)",
      "Edit(./.pre-commit-config.yaml)",
      "Edit(./.claude/settings.json)",
      "Edit(./.claude/hooks/**)",
      "Edit(./Docs/baseline/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard_commands.py\""
          }
        ]
      }
    ]
  }
}
```

### F3. Write the guard

`.claude/hooks/guard_commands.py`, standard library only. It reads the tool call as JSON from stdin, checks `tool_input.command`, and exits with code 2 and a reason when a rule matches.

| Blocks | Reason shown |
|---|---|
| `git push` to `main` or `develop`, or from those branches | Use a PR |
| `git commit` on `main` or `develop` | Use a task branch |
| `git push --force` to protected branches; `--force` without an explicit task branch | Protected history |
| `git reset --hard origin/...`, `git clean -fd` | Destructive |
| `--no-verify`, `--no-gpg-sign` | Do not skip checks |
| `git add -A`, `git add .`, `git add --all` | Stage explicit paths |
| `gh pr merge` without both `--auto` and `--squash`, or with `--admin` | Must wait for CI |
| `gh pr merge` with a PR whose base is `main` | Human decision |
| `gh pr review --approve` | Human decision |
| Adding `exception:*` labels | Only you can grant exceptions |
| `gh api` writes to rulesets or branch settings; `gh repo edit`; `gh secret`; `gh variable` | Protects the rules |
| Commands that print `.env` or `SONAR_TOKEN` | Secrets |
| `git tag` or `git push` on `baseline-pre-refactor` | Frozen |

For the check on PR base, the guard calls `gh pr view <n> --json baseRefName`. **If the call fails, it blocks.**

**Limit:** pattern matching can be bypassed. This prevents accidents; rulesets are the real boundary.

### F4. Test it

`.claude/hooks/tests/test_guard_commands.py` has an allowed and a blocked case for each rule, and runs in CI through the `backend` job or its own small job.

**Done when:** tests pass, and in a live session, Claude's attempt at each blocked command is stopped. The live check is in I2, because Claude Code's permission mode may change how `ask` rules behave.

---

## Block G: Skills

Files go in `.claude/skills/<name>/SKILL.md`. Skills with external effects set `disable-model-invocation: true`, so only you can start them.

**Built now, because Phase 0 needs them:**

| Skill | Manual only | What it does | Stops for |
|---|---|---|---|
| `/create-issues <phase>` | Yes | Creates missing labels, milestone and issues. Repeating it creates no duplicates | Your review of the list |
| `/start-task <issue>` | Yes | Checks Definition of Ready, updates `develop`, creates the branch, moves the card, proposes a plan | **Your plan approval** |
| `/verify` | No | Chooses checks by changed area, runs them, lists manual checks, reports real output | Any failure |
| `/commit` | Yes | Stages explicit paths, separates by concern, writes the message with AI attribution | Your review of the list |
| `/open-pr` | Yes | See below | **Your confirmation** |
| `/handle-review <pr>` | Yes | Turns professor comments into linked `review:follow-up` issues, updates labels | Your review of the issues |
| `/weekly-report` | No | Lists merged PRs, pending reviews, flags, exceptions and metric changes. Read-only | None |

**Built when first needed:**

| Skill | When |
|---|---|
| `/characterize <module>` | At the start of the safety net work after Phase 0 |
| `/close-phase <n>` | At the end of Phase 0. The B6 PR is done by hand |

Existing commands are reused: `/code-review`, `/simplify`, `/security-review`.

### `/open-pr` in detail

```markdown
---
name: open-pr
description: Verify, self-review and open a pull request to develop with auto-merge.
disable-model-invocation: true
---

1. Confirm the branch follows the naming rule and is not main or develop.
2. Rebase on origin/develop. Stop if there are conflicts you cannot resolve safely.
3. Run /verify. Stop on any failure. Never weaken a test to pass.
4. Run /code-review high on the branch. Fix real findings or list them.
5. Fill .github/pull_request_template.md in English from the issue and the diff.
   Only check a box under "Manual verification" if the user confirmed that it was done.
6. Show the user: title, changed files, tests changed, manual checks, findings.
   Stop until the user confirms.
7. Push the branch and open the PR. End the description with the required attribution.
8. Run: gh pr merge <n> --squash --auto
9. Report the PR link and its status. Do not claim that it merged until it has.
```

### Validate

Each skill runs once in block J. `/verify`, `/commit` and `/open-pr` are the essential ones.

---

## Block H: Rulesets

Create or update them in **Settings → Rules → Rulesets**, only after E6 passes.

| Rule | `protect-develop` | `protect-main` |
|---|---|---|
| Require a pull request | Yes | Yes |
| Required approvals | 0 | 1 |
| Dismiss stale approvals | Not applicable | Yes |
| Required checks | `ci-gate`, `process` | `ci-gate`, `process` |
| Branch up to date | Yes | Yes |
| Conversations resolved | Yes | Yes |
| Block force pushes | Yes | Yes |
| Restrict deletions | Yes | Yes |
| Allowed merge method | Squash | Merge |
| Bypass list | Empty | Empty |

Also create labels, if `/create-issues` has not:

```bash
gh label create "review:pending" --color FBCA04
gh label create "exception:coverage" --color D93F0B
# Full list in Reference R4
```

---

## Block I: Prove the gates

Throwaway PRs are closed without merging. **Disable auto-merge on them** and check that nothing reaches `develop`.

### I1. GitHub gates

| # | Test | Expected |
|---|---|---|
| 1 | Add a failing test | `ci-gate` red, Sonar still publishes, no merge |
| 2 | Add an untested backend line | `diff-cover` fails |
| 3 | Same as 2, with `exception:coverage` and a rerun | Passes; shortfall visible in the run |
| 4 | Title `Fixed stuff` | `process` fails |
| 5 | Branch `my-branch` | `process` fails |
| 6 | Unchecked manual box, then check it | Fails, then passes without rerunning tests |
| 7 | New `@pytest.mark.skip` without an issue | `process` fails |
| 8 | Modify an existing test | `flag:test-changed` added |
| 9 | Fake secret in the diff | `secrets` fails |
| 10 | `.md`-only PR | Heavy jobs skipped, `ci-gate` green |
| 11 | Direct push to `develop` and `main` | Rejected |
| 12 | PR to `main` without approval | Merge blocked |
| 13 | Change a frontend line with no test | **Shows whether the Sonar gate blocks mechanical work** |

**If test 13 fails on Sonar coverage (risk R1):** task 0.11 would be blocked as well. Choose one of these, and record it in `Docs/baseline/README.md`:

- **Recommended:** keep the gate required for security, reliability and duplication, and report coverage from `diff-cover` only.
- **Alternative:** use the human exception on the affected PRs.

Do not silently change the gate.

### I2. Local and AI gates

| # | Test | Expected |
|---|---|---|
| 14 | Ask Claude to run each blocked command in F3 | Blocked with a reason |
| 15 | Ask Claude to edit a workflow | Requires your confirmation |
| 16 | Ask Claude to read `.env` | Denied |
| 17 | Manual commit with `--no-verify` | Commits locally, but CI still catches the problem |

Test 17 shows why CI is the final barrier.

---

## Block J: Backlog and pilot

### J1. Create the backlog

1. Create the GitHub Project with these statuses: Backlog, Ready, In progress, In PR, Review pending, Done, and a one-week iteration field.
2. Run `/create-issues 0` on the Phase 0 text you shared, translated to English.
3. Close the tasks already completed, as listed in [Tasks taken from Phase 0](#tasks-taken-from-phase-0).
4. Apply these updates:

| Task | Update |
|---|---|
| 0.9 | Keep the `.claude/` rules, and add `!Docs/baseline/**` so its patterns do not hide new exports |
| 0.11 to 0.15 | Follow the decision from I1 test 13 |
| 0.27 | File name: `Docs/baseline/dependency-risks.md` |
| 0.33 | File name: `Docs/baseline/reference-metrics.json` |
| 0.36 | Use `develop`, not `refactor/**`; Dependabot targets `develop` with `chore(deps)`; `/open-pr` does not apply to its PRs |
| 0.38 | `sonar.projectVersion=phase-0`; reuse `export_sonar.py` |

### J2. Pilot

| Task | Why | What it exercises |
|---|---|---|
| **0.16** Remove unreachable code | Backend, no new lines to cover | `/start-task`, `/verify`, `/commit`, `/open-pr`, auto-merge, `review:pending` |
| **0.14** Add `noopener` | Frontend, needs a real browser check | The manual verification gate |

Then ask the professor to comment on one merged PR, and run `/handle-review` on it. If the professor is unavailable, leave a test comment yourself.

### J3. Retrospective

Answer:

- Which steps added no value, and can be removed?
- Which failures were unclear?
- Was the time from issue to merge acceptable?

Update `CONTRIBUTING.md` through a normal PR, then generate the first `/weekly-report`.

---

## Exit checklist

**Foundation**
- [ ] `gh`, devcontainer and local test run match CI
- [ ] The professor has write access and agrees with the process
- [ ] Sonar profile and gate conditions are recorded

**Baseline**
- [ ] `baseline-pre-refactor` points to `e02c0bb`
- [ ] `Docs/baseline/` is merged, and the `develop` analysis equals the baseline
- [ ] `main` contains the baseline with professor approval

**The six layers**
- [ ] `CONTRIBUTING.md` is merged
- [ ] `CLAUDE.md` is committed with the workflow section
- [ ] The seven skills work
- [ ] Hooks are versioned, tested and active
- [ ] `pre-commit` rejects each D2 case
- [ ] Both rulesets are active with empty bypass lists, and `ci-gate` and `process` are required

**Proof**
- [ ] All tests in block I gave the expected result
- [ ] The Sonar coverage question has a recorded decision
- [ ] Phase 0 tasks are on the board
- [ ] Both pilot tasks merged through the full flow
- [ ] The retrospective's changes are merged

## Schedule

My estimate, assuming a start on Monday 9 November and near full-time work. Professor approval runs in parallel.

| Day | Blocks |
|---|---|
| Mon 9 Nov | A, B1 to B3 |
| Tue 10 Nov | B4, B5, B6 requested; C1 |
| Wed 11 Nov | C2 to C4, D |
| Thu 12 Nov | E1 to E3 |
| Fri 13 Nov | E4 to E6 |
| Mon 16 Nov | F, G, H |
| Tue 17 Nov | I, J |
| Wed 18 Nov | Phase 0 continues from task 0.8 |

**If time runs short,** cut in this order: `/weekly-report` and `/handle-review` (do them by hand), the `docker` job, project board fields, ADR 0001.

**Never cut:** the baseline, CI, rulesets, hooks, and the gate tests.

**This takes from your 8-week window.** Your Phase 0 estimate of 8 to 12 days already includes tasks 0.1 to 0.7, but the rest of Phase -1 is additional. Compensate using the cuts your plan already lists.

## Stop conditions

Stop and decide before continuing if:

| Situation | Why |
|---|---|
| The exported data does not match the expected values in B5 | The baseline would be wrong |
| Sonar on `develop` differs from the baseline | Configuration or data has changed |
| The CI artifact for run `42134886141` is gone | Evidence must be recreated and recorded |
| The test run in the devcontainer differs from CI | Local results cannot be trusted |
| The professor rejects the post-merge review | The `develop` rules change |
| Block I shows that a gate fails to block | The automated flow is not safe yet |

## Risks

| # | Risk | Response |
|---|---|---|
| R1 | Sonar's gate requires coverage on new code, and blocks mechanical frontend tasks | Resolved through A5 and I1, test 13 |
| R2 | AI writes code and tests, so 95 % may come from weak tests | Fresh-context review, `/code-review`, your review, flags on changed tests, and the professor's later review. Consider mutation testing for `core/` later |
| R3 | 20-minute CI plus "branch up to date" slows parallel work | One open PR at a time; mark slow tests after the safety net exists |
| R4 | Too much process for one person | The retrospective in J3 removes what adds no value |

---

## Reference

### R1. Naming

**Branches:**

```text
^(feature|fix|refactor|test|docs|ci|chore|hotfix|revert)/[0-9]+-[a-z0-9-]+$
```

Exempt: `main`, `develop`, `dependabot/*`.

**Titles and commits:**

```text
^(feat|fix|refactor|test|docs|ci|build|chore|perf|revert)(\([a-z0-9-]+\))?!?: .{1,72}$
```

**Scopes:** `api`, `ts`, `core`, `train`, `frontend`, `ci`, `deps`, `docker`, `security`, `baseline`, `docs`, `process`, `release`.

**Example commit:**

```text
refactor(train): extract ARIMA trainer into its own module

Move the code without changing logic. Characterization tests stay
green and the JSON response is unchanged.

Refs #42
Co-Authored-By: <AI attribution given by the tool>
```

### R2. Pull request template

```markdown
## What and why
<!-- Two or three lines. -->
Closes #

## Type of change
- [ ] Refactor (no behavior change)
- [ ] Fix
- [ ] Feature
- [ ] Tests
- [ ] CI, docs or chore

## Behavior preservation
- [ ] Existing tests pass unmodified, or the changes are explained below
- [ ] JSON responses and HTTP statuses are unchanged
- [ ] Impact on `pipeline_config.json` and `run-pipeline` was checked
- [ ] Impact on DVC, MLflow and the filesystem was checked

Tests changed or skipped, and why:

## Manual verification
<!-- CI fails while a box here is unchecked. If nothing needs checking,
     write "None" and the reason, with no boxes. -->
- [ ]

## Metrics
<!-- Required when touching api/services.py, apiTimeSeries/services.py,
     TrainCard.jsx or TSTrainCard.jsx. -->
| Metric | Baseline | Before | After |
|---|---|---|---|
| Cyclomatic complexity | | | |
| Code smells | | | |
| Duplication | | | |
| Coverage | | | |

## Risks and rollback

## Architecture decision
<!-- ADR link, if applicable. -->

## AI usage
- Assisted tasks:
- [ ] I reviewed and understand the whole diff
```

### R3. `CLAUDE.md` section

```markdown
## Development workflow

Full rules are in CONTRIBUTING.md. In short:

- Every change starts from a GitHub issue and goes through one PR to `develop`.
  Never commit or push directly to `develop` or `main`.
- Use the skills: /start-task, /verify, /commit, /open-pr.
- All repository text is in English. Existing user-facing app strings stay as they are.
- A refactor must not change behavior. Never mix it with a fix or feature.
  Squash merges keep one commit per PR, so each concern needs its own PR.
- Do not modify or skip existing tests, lower thresholds, add dependencies, or
  change CI, Sonar or hook configuration, unless the issue requires it or the
  user approves it.
- `Docs/baseline/` and the `baseline-pre-refactor` tag are frozen.
- Stage files by explicit path.
- Report verification with real command output. Never say something passed
  without running it.
```

### R4. Labels

| Group | Labels |
|---|---|
| Phase | `phase:0` |
| Priority | `priority:P1`, `priority:P2`, `priority:P3` |
| Area | `area:backend`, `area:ts`, `area:frontend`, `area:ci`, `area:docker`, `area:deps`, `area:docs` |
| Thesis objective | `obj:1`, `obj:2`, `obj:3`, `obj:4` |
| Review | `review:pending`, `review:done`, `review:follow-up` |
| Flags | `flag:test-changed`, `flag:config-changed` |
| Exceptions (only you) | `exception:coverage`, `exception:sonar-config` |

### R5. AI permissions

| On its own | With your approval | Never |
|---|---|---|
| Read code, create task branches | Task plan | Direct push to `main` or `develop` |
| Write code and new tests | New dependencies | Force-push to protected branches, or skip checks |
| Run tests and linters | Changing or skipping an existing test | Approve a PR |
| Commit locally through `/commit` | CI, threshold, Sonar or hook changes | Merge to `main` |
| Generate reports | Confirming `/open-pr`, which enables auto-merge | Grant exceptions or touch the frozen baseline |
