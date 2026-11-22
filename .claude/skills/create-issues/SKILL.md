---
name: create-issues
description: Turn a phase's task list into GitHub issue drafts, labels and a milestone without duplicates, and give the author the commands to create them.
argument-hint: <phase number> [path to the task list]
disable-model-invocation: true
---

Prepare the backlog for phase $ARGUMENTS. The author creates everything on GitHub. Reply to the author in Spanish; issues are written in English.

## 1. Get the task list

- Use the file path given after the phase number, or ask the author to paste the phase's tasks.
- The source may be in Spanish. Translate it into English, and keep each task's id, for example `0.16`.
- Do not copy the source document into the repository.

## 2. Read what already exists

If `gh` is not on PATH, call it by its full path.

- `gh issue list --state all --limit 500 --json number,title,state,labels,milestone`
- `gh label list --limit 200 --json name`
- `gh api repos/{owner}/{repo}/milestones?state=all --jq ".[].title"`

A task already has an issue when an issue title starts with `[<task id>]`. Also list issues whose title looks like the same work under another name, so the author can decide. Never create a second issue for the same task.

## 3. Draft each new issue

**Title:** `[<task id>] <imperative summary>`.

**Body:** the sections of `.github/ISSUE_TEMPLATE/task.yml`, as `###` headings in this order:

- Phase
- Objective
- Description
- Acceptance criteria (checkboxes)
- Affected modules
- Verification
- Risks

**Definition of Ready:** checkable acceptance criteria, the affected modules, and a scope that fits one PR of under 400 lines.

- Where the source does not give these, draft them from the code and mark the issue "needs author review".
- If a task is too big for one PR, propose how to split it into issues `<id>a`, `<id>b`.

**Labels and milestone:** label `task`, milestone `Phase <n>`.

**Plan updates:** check the plan in `thoughts/shared/plans/` for updates to a task, such as the block J table in the Phase -1 plan, and apply them.

## 4. Labels and milestone

The repository needs these labels. Draft only the missing ones:

- `task`
- `bug`
- `review:pending`, `review:done`, `review:follow-up`
- `flag:test-changed`, `flag:config-changed`
- `exception:coverage`, `exception:sonar-config`

Draft milestone `Phase <n>` if it does not exist.

## 5. Already finished tasks

Some tasks may already be done. Check merged PRs with `gh pr list --state merged --limit 100`. For those, propose creating the issue and closing it with a comment that names the PR, so the backlog shows the whole phase.

## 6. Show and stop

Show a table with these columns:

- task id
- title
- status: new, exists as #n, possible duplicate of #n, or done in PR #n
- size estimate
- "needs author review" marks

Stop until the author approves or changes the list.

## 7. Write the commands

After approval:

1. Write each body to a file in a folder outside the repository, such as the session scratchpad.
2. Write the commands in order, one per line, with full absolute paths:

   ```powershell
   gh label create "<name>" --color <hex> --description "<text>"
   gh api repos/{owner}/{repo}/milestones -f title="Phase <n>"
   gh issue create --title "[<id>] <summary>" --label task --milestone "Phase <n>" --body-file "<path>"
   gh issue close <n> --comment "Done in #<pr>."
   ```

3. Tell the author to run them in order and to paste any error.

Running the skill again must give an empty list for issues that were already created.
