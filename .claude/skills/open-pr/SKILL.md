---
name: open-pr
description: Check the branch, run /verify and a code review, fill the PR template, and give the author the push and gh pr create commands.
disable-model-invocation: true
---

Prepare a pull request from the current branch to `develop`. The author pushes, creates and merges the PR. Reply to the author in Spanish; the PR text is in English.

## 1. Check the branch

- Get the branch with `git branch --show-current`.
  - It must not be `main` or `develop`.
  - It must match `^(feature|fix|refactor|test|docs|ci|chore|hotfix|revert)/[0-9]+-[a-z0-9-]+$`.
  - The number in it is the issue. Read the issue with `gh issue view <n>`.
- Run `git fetch origin`.
- Check that every change is committed. Run `git status --short`, and stop if a tracked file is modified. A fix left uncommitted is not in the PR.
- Check whether the branch is behind develop with `git rev-list --count HEAD..origin/develop`. If it is behind, give the update commands and stop until the author runs them:
  - Branch not pushed yet: `git rebase origin/develop`
  - Branch already pushed: `git merge origin/develop`. Squash merging makes the merge commit harmless.

## 2. Verify and review

1. Follow `/verify`. Stop on any failure. If `/verify` already ran in this session and nothing changed since, reuse its report instead of running it again.
2. Review the diff against `origin/develop`. Match the depth to the change:
   - Code in `DREAM-ML-backend/`, `DREAM-ML-frontend/`, `scripts/` or `.claude/hooks/`: run `/code-review high`.
   - Small changes without code, such as docs or ignore rules: review the diff yourself and say so in the summary.
   - For each real finding, propose a fix and, if the author agrees, make it.
   - The author then commits with `/commit`.
   - Findings left open go in the PR description.

## 3. Measure the change

- Run `git diff --stat origin/develop...HEAD`.
- Over 400 changed lines: only mechanical moves and generated files are allowed. Otherwise propose a split.
- List the tests changed or skipped.
- Say which labels the `process` check will add:
  - `flag:test-changed` when existing tests change
  - `flag:config-changed` when CI, Sonar, coverage, hook or `scripts/ci/` files change

## 4. Write the description

Fill `.github/pull_request_template.md` from the issue, the diff and the `/verify` report:

- **Issue reference:**
  - Write `Closes #<n>` if the PR completes the issue, or `Refs #<n>` if it is one part.
  - GitHub does not close issues from PRs to `develop`, so the author closes them by hand.
- **Changes:** what changed and why. Do not restate the whole diff.
- **Manual verification:**
  - Check a box only if you ran it and have the output, or the author confirmed it.
  - A box that can only be checked after merge would keep `process` red. Write it as plain text instead.
- **AI usage:** say which parts were assisted. Leave "I reviewed and understand the whole diff" unchecked; only the author checks it.
- Add no AI attribution footer.

Save it to a file outside the repository, such as the session scratchpad, and give its full absolute path.

## 5. Show and hand over

1. Show a summary:
   - the title, which becomes the squash commit. It must follow Conventional Commits.
   - the changed files and size
   - the tests changed
   - the manual checks still open
   - the review findings
2. Give the commands:

   ```powershell
   git push -u origin <branch>
   gh pr create --base develop --title "<title>" --body-file "<full path>"
   ```

3. Remind the author of the steps on GitHub:
   - Check the Commits tab shows every commit.
   - Review the diff and check the AI review box.
   - Wait for `ci-gate` and `process` to pass.
   - Squash and merge.
   - Then run `git switch develop`, `git pull` and `git branch -D <branch>`.
   - Close the issue if the PR completes it.

Never run `gh pr merge`, approve a PR, or add `exception:*` labels.
