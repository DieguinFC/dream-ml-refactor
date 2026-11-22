"""SessionStart hook: tell Claude where the work stands before it does anything.

Prints the current branch, the issue taken from its name, whether the branch has
commits that are not on GitHub (or a remote branch that was deleted after a merge),
and uncommitted changes. Claude Code adds this output to the session context.
Never fails: missing information is simply left out.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "hooks"))

from add_issue_ref import issue_from_branch  # noqa: E402

MAX_STATUS_LINES = 20


def git(*args):
    try:
        result = subprocess.run(
            ["git", *args], cwd=PROJECT_DIR, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def build_context(branch, upstream, ahead, upstream_gone, status_lines):
    lines = ["Repository state at session start:"]
    if not branch:
        lines.append("- Detached HEAD or unknown branch.")
    else:
        issue = issue_from_branch(branch)
        lines.append(f"- Branch: {branch}" + (f" (issue #{issue})" if issue else ""))
        if branch in ("main", "develop"):
            lines.append("- This is a protected branch: create a task branch before changing anything.")
    if upstream_gone:
        lines.append(f"- The remote branch {upstream} no longer exists (probably merged). "
                     "Changes here will not reach the merged PR; start a new branch from develop.")
    elif upstream and ahead:
        lines.append(f"- {ahead} commit(s) not pushed to {upstream}.")
    elif branch and not upstream and branch not in ("main", "develop"):
        lines.append("- No remote branch yet: nothing from this branch is on GitHub.")
    if status_lines:
        shown = status_lines[:MAX_STATUS_LINES]
        lines.append(f"- Uncommitted changes ({len(status_lines)}):")
        lines.extend(f"    {line}" for line in shown)
        if len(status_lines) > MAX_STATUS_LINES:
            lines.append(f"    ... and {len(status_lines) - MAX_STATUS_LINES} more")
    else:
        lines.append("- Working tree clean.")
    return "\n".join(lines)


def main():
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") if branch else None
    upstream_gone = bool(branch) and upstream is None and \
        git("config", f"branch.{branch}.merge") is not None
    if upstream_gone:
        upstream = git("config", f"branch.{branch}.merge") or ""
        upstream = upstream.replace("refs/heads/", "origin/")
    ahead = git("rev-list", "--count", "@{u}..HEAD") if upstream and not upstream_gone else None
    status = git("status", "--short") or ""
    status_lines = [line for line in status.splitlines() if line.strip()]
    print(build_context(branch, upstream, int(ahead) if ahead and ahead.isdigit() else 0,
                        upstream_gone, status_lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
