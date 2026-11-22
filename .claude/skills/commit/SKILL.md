---
name: commit
description: Group the current changes by concern and give the author the exact git add and git commit commands, with a Conventional Commits message and no AI attribution.
disable-model-invocation: true
---

Prepare a commit of the current changes. The author runs the commands. Reply to the author in Spanish; the commit message is in English.

## 1. Inspect the changes

Run:

- `git branch --show-current`
- `git status --short`
- `git diff` and `git diff --staged`

Stop if:

- The branch is `main` or `develop`. Use `/start-task` first.
- There is nothing to commit.

## 2. Choose the files

- List each changed file with one line on what changed.
- Keep out:
  - generated artifacts (coverage reports, `__pycache__`, `db.sqlite3`, build output, `.DS_Store`)
  - `.env` and any secrets
  - files unrelated to the branch's issue
- Never change `Docs/baseline/`, except an additive note in `manifest.json`.
- If the changes mix concerns, propose one commit per concern and say whether they belong in separate PRs. Each of these is a concern:
  - a refactor
  - a fix or feature
  - a mechanical move or rename
  - test changes that are not part of the same change

## 3. Write the message

- **Subject:** `type(scope): summary` must match `^(feat|fix|refactor|test|docs|ci|build|chore|perf|revert)(\([a-z0-9-]+\))?!?: .{1,72}$`.
  - Scopes are listed in `CONTRIBUTING.md`.
  - The summary is imperative and lowercase, with no final period.
- **Body:** one or two sentences on why, wrapped around 72 characters.
- **No AI attribution:** never add `Co-Authored-By` or "Generated with" lines. A git hook rejects them.
- **Issue reference:** do not add `Refs #<n>`. The `add-issue-ref` git hook adds it from the branch name. Add it by hand only if the branch name has no issue number.

## 4. Give the commands

List every path explicitly. Never use `git add .`, `git add -A` or `git commit -a`. Use one `-m` per paragraph, and keep quotes out of the text so it works in PowerShell and bash:

```powershell
git add <path> <path>
git status
git commit -m "<subject>" -m "<body>"
git log -1
```

Tell the author what `git status` should show staged. `git log -1` should end with `Refs #<n>`. If a hook rejects the commit, ask for its output and fix the cause. Never suggest `--no-verify`.
