"""PostToolUse hook: run Ruff's CI error rules on a backend Python file Claude just edited.

Uses the ruff-check hook from .pre-commit-config.yaml, so the Ruff version and rules
(E9, F63, F7, F82) are the same as at commit time and in CI. On errors it exits with
code 2, which shows Ruff's output to Claude right after the edit. When pre-commit is
not installed it does nothing: the git hook and CI still check the file.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
BACKEND_PY_RE = re.compile(r"^DREAM-ML-backend/.*\.py$")
EDIT_TOOLS = {"Edit", "MultiEdit", "Write"}


def backend_file(payload, project_dir=PROJECT_DIR):
    """Return the edited file relative to the project when it is backend Python, else None."""
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    path = Path(payload.get("tool_input", {}).get("file_path") or "")
    if not path.is_absolute():
        path = project_dir / path
    try:
        relative = path.resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError:
        return None
    return relative if BACKEND_PY_RE.match(relative) else None


def run_ruff(relative, project_dir=PROJECT_DIR):
    """Return (failed, output)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "ruff-check", "--files", relative],
            cwd=project_dir, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    if "No module named pre_commit" in result.stderr:
        return False, ""
    return result.returncode != 0, (result.stdout + result.stderr).strip()


def main():
    try:
        relative = backend_file(json.loads(sys.stdin.read().lstrip(chr(0xFEFF))))  # PowerShell pipes add a BOM
    except Exception:
        return 0
    if not relative:
        return 0
    failed, output = run_ruff(relative)
    if failed:
        print(f"Ruff found errors in {relative} (same rules as CI):\n{output}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
