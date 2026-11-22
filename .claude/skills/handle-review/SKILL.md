---
name: handle-review
description: Turn the professor's review comments on a merged PR into review follow-up issue drafts, and give the author the commands to create them and update the PR labels.
argument-hint: <PR number>
disable-model-invocation: true
---

Handle the review of PR #$ARGUMENTS. The author creates the issues and changes the labels. Reply to the author in Spanish; issues are written in English.

## 1. Read the PR and its review

If `gh` is not on PATH, call it by its full path.

- `gh pr view $ARGUMENTS --json number,title,state,mergedAt,labels,url,reviews,comments`
- Inline comments: `gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq ".[] | {id, user: .user.login, path, line, body, html_url}"`

Keep only comments from reviewers who are not the author. If you are unsure who the reviewer is, ask. Stop if the PR is not merged: a review before merge is handled in that same PR.

## 2. Find follow-ups that already exist

Run `gh issue list --state all --label review:follow-up --json number,title,body,state`. Skip comments already linked from an issue body.

## 3. Classify each comment

| Kind | What to do |
|---|---|
| Change request | Draft one follow-up issue |
| Question | Draft an answer for the author to post. No issue unless the answer shows a needed change |
| Praise or "done" | Nothing |

- Group comments that ask for the same change into one issue.
- A comment that asks for several unrelated changes becomes several issues, one per concern.

## 4. Draft the issues

**Title:** `[review] <imperative summary>`.

**Label:** `review:follow-up`.

**Body:** the sections of `.github/ISSUE_TEMPLATE/review-follow-up.yml`, as `###` headings:

- **Original PR:** `#$ARGUMENTS`
- **Review comment:** the exact quote and the link to it (`html_url`)
- **Required change:** what will be done, the acceptance criteria as checkboxes, and the affected modules, so the issue meets the Definition of Ready

## 5. Show and stop

Show a table with these columns:

- the comment, shortened
- its kind
- the proposed issue title or answer

Stop until the author approves or changes it.

## 6. Write the commands

After approval:

1. Write each body to a file outside the repository, such as the session scratchpad.
2. Give the commands:

   ```powershell
   gh issue create --title "[review] <summary>" --label review:follow-up --body-file "<path>"
   gh pr edit $ARGUMENTS --remove-label review:pending --add-label review:follow-up
   ```

3. Choose the labels:
   - If the review asks for no changes, use `--remove-label review:pending --add-label review:done` instead.
   - Once every follow-up of this PR is merged, the PR gets `review:done`.
4. Each follow-up then starts with `/start-task <issue>`.
