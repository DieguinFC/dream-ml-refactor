---
name: start-task
description: Check that a GitHub issue is ready, give the commands to create its branch from develop, and propose a plan for approval.
argument-hint: <issue number>
disable-model-invocation: true
---

Start work on issue #$ARGUMENTS. The author runs every command with an external effect: you read, check and propose, and you give commands to run. Reply to the author in Spanish; everything written for the repository is in English.

## 1. Read the issue

Run `gh issue view $ARGUMENTS --json number,title,body,labels,state,assignees`. If `gh` is not on PATH, call it by its full path. Stop if the issue is closed or does not exist.

## 2. Check the Definition of Ready

From `CONTRIBUTING.md`, the issue needs:

- acceptance criteria that can be checked
- the affected modules
- a scope that fits one PR of under 400 changed lines

If something is missing, list exactly what, suggest the text to add, and stop. Do not start on an issue that is not ready.

## 3. Check the working tree

Run `git status --short` and `git branch --show-current`.

- Uncommitted changes to tracked files: list them and ask what to do before creating a branch. They would move to the new branch.
- On a task branch whose remote was deleted (merged PR): say so. Its leftovers do not belong to this issue.

## 4. Name the branch

Format `<type>/<issue>-<slug>`. It must match `^(feature|fix|refactor|test|docs|ci|chore|hotfix|revert)/[0-9]+-[a-z0-9-]+$`.

- Choose the type from what the issue changes. Use `refactor` only when behavior must stay the same.
- The slug has 2 to 5 lowercase words from the title.

## 5. Give the branch commands

```powershell
git switch develop
git pull
git switch -c <branch>
```

## 6. Propose a plan

Read the code the issue touches before planning. Search and read sections of large files such as `apiTimeSeries/train.py`. The plan lists:

- **Files** to change or create, with one line each on what changes.
- **Tests:**
  - New tests for new behavior.
  - For a refactor, characterization tests that pin the current behavior first.
  - Any existing test that would need to change, with the reason. That needs the author's approval.
- **Contract:** what must not change. That includes JSON shapes, HTTP statuses, routes, `pipeline_config.json`, DVC and git order, and MLflow names. Say "none touched" when that is true.
- **Checks** `/verify` will run, and the manual checks the PR will need.
- **Size:** an estimate of the changed lines. If it is over 400, propose how to split it.
- **Separate concerns:** a refactor and a fix, or a move and a logic change, go in separate PRs.
- **Risks** and open questions.

Stop and wait for the author to approve or change the plan. Do not edit files before approval.
