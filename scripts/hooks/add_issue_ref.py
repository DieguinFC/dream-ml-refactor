"""prepare-commit-msg hook: add "Refs #<n>" taken from the branch name.

On branch test/17-add-vitest, a commit message that does not mention #17 gets a
"Refs #17" line. Merge, squash and amend messages are left alone. The hook never
fails a commit: when it cannot read the branch, it does nothing.
"""

import os
import re
import subprocess
import sys

ISSUE_FROM_BRANCH_RE = re.compile(r"^[a-z]+/(\d+)-")
# Sources from git: message (-m/-F), template, merge, squash, commit (amend, -c, -C).
SKIP_SOURCES = {"merge", "squash", "commit"}


def issue_from_branch(branch):
    match = ISSUE_FROM_BRANCH_RE.match(branch)
    return match.group(1) if match else None


def add_ref(message, issue):
    """Return the message with "Refs #<issue>" before git's comment lines."""
    if re.search(rf"#{issue}\b", message):
        return message
    lines = message.splitlines(keepends=True)
    cut = next((i for i, line in enumerate(lines) if line.startswith("#")), len(lines))
    text = "".join(lines[:cut]).rstrip()
    comments = "".join(lines[cut:])
    ref = f"Refs #{issue}\n"
    # An empty text means the editor is about to open: keep the first line free for the subject.
    new_text = f"\n\n{ref}" if not text else f"{text}\n\n{ref}"
    return f"{new_text}\n{comments}" if comments else new_text


def current_branch():
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip()


def main(argv):
    if len(argv) < 2:
        return 0
    source = os.environ.get("PRE_COMMIT_COMMIT_MSG_SOURCE") or (argv[2] if len(argv) > 2 else "")
    if source in SKIP_SOURCES:
        return 0
    issue = issue_from_branch(current_branch())
    if not issue:
        return 0
    path = argv[1]
    with open(path, encoding="utf-8", newline="") as handle:
        message = handle.read()
    new_message = add_ref(message, issue)
    if new_message != message:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(new_message)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
