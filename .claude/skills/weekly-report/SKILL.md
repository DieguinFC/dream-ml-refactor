---
name: weekly-report
description: Read-only summary of the last week's merged PRs, pending reviews, flags, exceptions, open issues and SonarCloud metrics on develop.
argument-hint: "[start date YYYY-MM-DD, default 7 days ago]"
---

Write the weekly report. This skill only reads: it never edits files, labels, issues or PRs. Reply to the author in Spanish; the report itself is in English, so it can be shared with the professor.

## 1. Period

Use $ARGUMENTS as the start date, or 7 days before today if it is empty. The period ends today.

## 2. Collect

If `gh` is not on PATH, call it by its full path.

- Merged PRs: `gh pr list --state merged --base develop --search "merged:>=<start>" --limit 100 --json number,title,mergedAt,labels,additions,deletions`
- Releases to `main`, the same with `--base main`
- Open PRs: `gh pr list --state open --json number,title,createdAt,labels`
- Review status, from the labels on merged PRs: `review:pending`, `review:follow-up`, `review:done`, and merged PRs that have no review label
- Flags and exceptions on the period's PRs:
  - `flag:test-changed`, `flag:config-changed`
  - `exception:coverage`, `exception:sonar-config`, with the reason written in each PR
- Issues: closed in the period, opened in the period, and open with the `task` or `review:follow-up` label, grouped by milestone
- SonarCloud metrics on `develop`, from the public API without a token:

  ```text
  https://sonarcloud.io/api/measures/component?component=DieguinFC_dream-ml-refactor&branch=develop&metricKeys=coverage,lines_to_cover,uncovered_lines,bugs,vulnerabilities,code_smells,duplicated_lines_density,ncloc
  ```

  Use `api/measures/search_history` with `from=<start>` for the values at the start of the period. Compare them with the baseline in `Docs/baseline/manifest.json` (`headline_metrics`). Remember the analyzer note there: some differences come from rule changes, not code.

If a source fails, say which one in the report and continue with the rest.

## 3. Report

Write Markdown with these sections:

1. **Summary:** three lines on what moved forward.
2. **Merged:** table of PR, title, size and labels.
3. **Reviews:** pending, follow-ups and done.
4. **Flags and exceptions:** each with its PR and reason.
5. **Metrics:** table with metric, baseline, start of week, now and change.
6. **Open work:** next tasks by milestone, and open PRs.
7. **Blockers and risks:** for example failing checks, stale PRs, or issues not ready.

Save the report to a file outside the repository, such as the session scratchpad, and give its full absolute path. Show the summary and the metrics table in the reply.
