# ADR 0001: Development workflow for the refactor

- Status: Accepted
- Date: 2026-11-16
- Issue: #

## Context

DREAM ML is being refactored incrementally as a thesis project, mostly by one author working with AI assistants, under weekly Scrum meetings with a guiding professor. The thesis compares the system before and after the refactor using SonarCloud metrics, test coverage, an extensibility case and a user survey, so:

- The "before" state must be frozen and reproducible.
- Every change must be traceable to a task, and small enough to review and revert.
- Behavior must not change by accident, because the frontend, `run-pipeline` and experiment repositories depend on exact responses, file formats and DVC/Git/MLflow side effects.
- AI-generated changes need the same, or stricter, controls as human ones.
- Work cannot stop while waiting for the professor's availability.

## Decision

1. **Branches.** `main` holds released states; `develop` is the integration branch. Work happens on short-lived branches named `<type>/<issue>-<slug>`, created from `develop`.
2. **Traceability.** Every change starts from an issue and reaches `develop` through one PR. Commits and PR titles follow Conventional Commits.
3. **Merging.** PRs to `develop` are squash merged as soon as CI passes, with no required approval. `develop` reaches `main` at the end of each phase through a PR merged with a merge commit, and is tagged with a SemVer version. `main` requires a PR but no approval.
4. **Review after merge.** The professor reviews merged PRs; requested changes become new issues and PRs, tracked with `review:*` labels.
5. **Baseline.** The tag `baseline-pre-refactor` (commit `e02c0bb`) and `Docs/baseline/` freeze the pre-refactor measurements and are never modified.
6. **Quality gates in CI.** Tests, a global coverage ratchet (47 % at the start), 95 % coverage of changed backend lines, linting, secret scanning and SonarCloud, plus a process check on PR titles, branch names and templates.
7. **AI usage.** AI assistants work under the permissions in `CONTRIBUTING.md`. They are not credited as commit co-authors; each PR declares its AI usage instead, and the author reviews the whole diff.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| Trunk-based development on `main` only | Leaves no stable, released state separate from work in progress for the thesis comparison and the professor |
| Requiring the professor's approval on each PR | GitHub does not allow approving your own PR, so every merge would wait on the professor's schedule |
| Requiring the professor's approval on `main` only | Same blocking problem at every phase end; review after merge gives the same feedback without stopping work |
| Merge commits on `develop` | Keeps work-in-progress commits; one squashed commit per PR is easier to read, bisect and revert |
| Crediting AI as co-author in commits | The author is responsible for every line; AI usage is disclosed per PR instead |

## Consequences

- Each concern needs its own PR, because squash merging keeps one commit per PR.
- Problems found in review are fixed forward, never by rewriting history.
- The process itself produces evidence for the thesis: issues, PRs, CI runs and ADRs.
- CI must be reliable enough to be the only merge gate on `develop`; it is built and tested in Phase −1 before refactoring starts.
