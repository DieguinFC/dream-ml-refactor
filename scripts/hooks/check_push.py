"""pre-push hook: stop pushes that GitHub or the process check would reject.

Blocks pushes to main or develop, which only change through PRs, and branch names
that do not follow <type>/<issue>-<slug>. Uses the same rule as scripts/ci/check_pr.py.
pre-commit passes the pushed refs in PRE_COMMIT_LOCAL_BRANCH and PRE_COMMIT_REMOTE_BRANCH.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))

from check_pr import BRANCH_RE, EXEMPT_BRANCHES  # noqa: E402

HEADS = "refs/heads/"


def check(remote_ref):
    """Return the errors for a push to remote_ref."""
    if not remote_ref.startswith(HEADS):
        return []  # tags and other refs
    branch = remote_ref[len(HEADS):]
    if branch in EXEMPT_BRANCHES:
        return [f"Do not push to {branch}: open a PR from a task branch."]
    if branch.startswith("dependabot/") or BRANCH_RE.match(branch):
        return []
    return [
        f"Branch name does not match <type>/<issue>-<slug>: {branch!r}. "
        "Rename it with: git branch -m <type>/<issue>-<slug>"
    ]


def main():
    remote_ref = os.environ.get("PRE_COMMIT_REMOTE_BRANCH", "")
    errors = check(remote_ref)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
