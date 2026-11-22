"""PreToolUse hook: ask the author before Claude edits an existing test file.

CONTRIBUTING.md requires the author's approval to change an existing test. Creating a
new test file stays allowed. Test files are recognised with the same rule as the
process check (scripts/ci/check_pr.py), so both agree on what a test is.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "ci"))

from check_pr import TEST_PATH_RE  # noqa: E402

EDIT_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}


def relative_path(file_path, project_dir=PROJECT_DIR):
    path = Path(file_path)
    if not path.is_absolute():
        path = project_dir / path
    try:
        return path.resolve().relative_to(project_dir.resolve()).as_posix(), path
    except ValueError:
        return None, path  # outside the project


def decision(payload, project_dir=PROJECT_DIR):
    """Return the hook output as a dict, or None to let the normal permission flow decide."""
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    relative, absolute = relative_path(file_path, project_dir)
    if not relative or not TEST_PATH_RE.search(relative) or not absolute.exists():
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"{relative} is an existing test. Changing it needs the author's approval (CONTRIBUTING.md, Tests)."
            ),
        }
    }


def main():
    try:
        output = decision(json.loads(sys.stdin.read().lstrip(chr(0xFEFF))))  # PowerShell pipes add a BOM
    except Exception as error:  # fail towards asking, never towards allowing silently
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"The test-edit guard failed ({error!r}).",
            }
        }
    if output:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
