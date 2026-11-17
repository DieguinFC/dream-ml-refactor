"""Process checks for pull requests (the `process` required check).

Reads the PR metadata from environment variables, never from command-line
interpolation, because titles, bodies and branch names are user input:

    PR_TITLE, PR_BODY, HEAD_REF, BASE_SHA, HEAD_SHA, LABELS (JSON list or one per line)

Prints every problem found and exits 1 if any check fails. Labels that should
be added to the PR are written, one per line, to the file named by
LABELS_TO_ADD (if set). Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

TITLE_RE = re.compile(r"^(feat|fix|refactor|test|docs|ci|build|chore|perf|revert)(\([a-z0-9-]+\))?!?: .{1,72}$")
BRANCH_RE = re.compile(r"^(feature|fix|refactor|test|docs|ci|chore|hotfix|revert)/[0-9]+-[a-z0-9-]+$")
EXEMPT_BRANCHES = {"main", "develop"}
ISSUE_REF_RE = re.compile(r"\b(Closes|Refs)\s+#\d+\b", re.IGNORECASE)
ISSUE_LINK_RE = re.compile(r"#\d+|/issues/\d+")
UNCHECKED_RE = re.compile(r"^\s*[-*]\s+\[ \]", re.MULTILINE)
REVIEWED_RE = re.compile(r"^\s*[-*]\s+\[[xX]\]\s+I reviewed and understand the whole diff", re.MULTILINE)
SKIP_RE = re.compile(
    r"pytest\.skip\(|@pytest\.mark\.(skip|skipif|xfail)\b|pytest\.xfail\("
    r"|pragma:\s*no cover|\b(it|describe|test)\.skip\("
)

CODE_PATH_RE = re.compile(r"\.(py|js|jsx|ts|tsx)$")
TEST_PATH_RE =re.compile(r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$|\.test\.[jt]sx?$")
CONFIG_PATH_RE = re.compile(
    r"^(\.github/workflows/|sonar-project\.properties$|DREAM-ML-backend/GEML/\.coveragerc$"
    r"|\.pre-commit-config\.yaml$|\.claude/hooks/|\.claude/settings\.json$|scripts/ci/)"
)
SONAR_FROZEN_KEY_RE = re.compile(
    r"^[+-]\s*sonar\.(sources|tests|inclusions|exclusions|test\.inclusions|test\.exclusions"
    r"|coverage\.exclusions|cpd\.exclusions|issue\.[^=\s]*)\s*="
)

BASELINE_MANIFEST = "Docs/baseline/manifest.json"
FLAG_TEST = "flag:test-changed"
FLAG_CONFIG = "flag:config-changed"
EXCEPTION_SONAR = "exception:sonar-config"


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    labels: set[str] = field(default_factory=set)


def section(body: str, heading: str) -> str:
    """Return the text under `## heading`, up to the next `## ` heading, without HTML comments."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def check_metadata(title: str, body: str, head_ref: str) -> list[str]:
    errors = []
    if not TITLE_RE.match(title):
        errors.append(f"Title is not a Conventional Commit: {title!r} (see CONTRIBUTING.md, Naming)")
    release = head_ref in EXEMPT_BRANCHES
    if not (release or head_ref.startswith("dependabot/") or BRANCH_RE.match(head_ref)):
        errors.append(f"Branch name does not match <type>/<issue>-<slug>: {head_ref!r}")
    if not release and not ISSUE_REF_RE.search(body):
        errors.append("PR body must reference its issue with 'Closes #<n>' or 'Refs #<n>'")
    verification = section(body, "Manual verification")
    if not verification.strip():
        errors.append("PR body is missing the '## Manual verification' section")
    elif UNCHECKED_RE.search(verification):
        errors.append("Manual verification has unchecked boxes; check them, or write 'None' and the reason")
    if not release and not REVIEWED_RE.search(body):
        errors.append("AI usage: check 'I reviewed and understand the whole diff'")
    return errors


def only_adds(old: object, new: object) -> bool:
    """True if `new` keeps every value of `old`: dict keys may be added, lists may grow at the end."""
    if isinstance(old, dict):
        return isinstance(new, dict) and all(k in new and only_adds(v, new[k]) for k, v in old.items())
    if isinstance(old, list):
        return isinstance(new, list) and len(new) >= len(old) and all(only_adds(a, b) for a, b in zip(old, new))
    return old == new


def check_files(name_status: list[tuple[str, str]], manifest_versions: tuple[str, str] | None = None) -> Result:
    """name_status: (status letter, path) pairs from `git diff --name-status`.

    manifest_versions: (old, new) text of the baseline manifest, when it was modified.
    """
    result = Result()
    for status, path in name_status:
        if path == BASELINE_MANIFEST and status == "M" and manifest_versions:
            try:
                additive = only_adds(json.loads(manifest_versions[0]), json.loads(manifest_versions[1]))
            except json.JSONDecodeError:
                additive = False
            if not additive:
                result.errors.append(f"{path}: notes may be added, but existing values must not change or disappear")
        elif path.startswith("Docs/baseline/") and status != "A":
            result.errors.append(f"Docs/baseline/ is frozen; only new files may be added ({status} {path})")
        if TEST_PATH_RE.search(path) and status != "A":
            result.labels.add(FLAG_TEST)
        if CONFIG_PATH_RE.search(path):
            result.labels.add(FLAG_CONFIG)
    return result


def check_added_lines(patch: str) -> Result:
    """Inspect added lines of a unified diff (`git diff -U0`)."""
    result = Result()
    current = None
    for line in patch.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            # Only code counts; docs and this checker's own tests mention these markers on purpose.
            current = path if path and CODE_PATH_RE.search(path) and not path.startswith("scripts/ci/") else None
            continue
        if not line.startswith("+") or current is None:
            continue
        if SKIP_RE.search(line):
            result.labels.add(FLAG_TEST)
            if not ISSUE_LINK_RE.search(line):
                result.errors.append(
                    f"{current}: new skip, xfail or 'no cover' needs an issue link on the same line: {line[1:].strip()}"
                )
    return result


def check_sonar_config(patch: str, labels: set[str]) -> list[str]:
    changed = [line for line in patch.splitlines() if SONAR_FROZEN_KEY_RE.match(line)]
    if changed and EXCEPTION_SONAR not in labels:
        return [
            "sonar-project.properties: sources, tests, exclusions and issue rules are frozen for the thesis "
            f"comparison; the owner must add the '{EXCEPTION_SONAR}' label to allow: " + "; ".join(changed)
        ]
    return []


def parse_labels(raw: str) -> set[str]:
    """Accept a JSON list (as produced by toJSON in the workflow) or one label per line."""
    raw = raw.strip()
    if raw.startswith("["):
        return {str(label) for label in json.loads(raw)}
    return {label for label in raw.splitlines() if label}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout


def main() -> int:
    env = os.environ
    title, body, head_ref = env.get("PR_TITLE", ""), env.get("PR_BODY", ""), env.get("HEAD_REF", "")
    labels = parse_labels(env.get("LABELS", ""))
    diff_range = f"{env['BASE_SHA']}...{env['HEAD_SHA']}"

    name_status = []
    for row in git("diff", "--name-status", "--no-renames", diff_range).splitlines():
        status, _, path = row.partition("\t")
        name_status.append((status[:1], path))

    manifest_versions = None
    if ("M", BASELINE_MANIFEST) in name_status:
        manifest_versions = (
            git("show", f"{env['BASE_SHA']}:{BASELINE_MANIFEST}"),
            git("show", f"{env['HEAD_SHA']}:{BASELINE_MANIFEST}"),
        )

    errors = check_metadata(title, body, head_ref)
    files = check_files(name_status, manifest_versions)
    added = check_added_lines(git("diff", "-U0", diff_range))
    errors += files.errors + added.errors
    errors += check_sonar_config(git("diff", "-U0", diff_range, "--", "sonar-project.properties"), labels)
    new_labels = sorted((files.labels | added.labels) - labels)

    if new_labels and env.get("LABELS_TO_ADD"):
        with open(env["LABELS_TO_ADD"], "w", encoding="utf-8") as handle:
            handle.write("\n".join(new_labels) + "\n")

    for label in sorted(files.labels | added.labels):
        print(f"flag: {label}")
    for error in errors:
        print(f"::error::{error}")
    if errors:
        print(f"\n{len(errors)} process check(s) failed. See CONTRIBUTING.md.")
        return 1
    print("All process checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
