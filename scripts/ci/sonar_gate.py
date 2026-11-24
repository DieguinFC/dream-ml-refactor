"""Wait for this run's SonarCloud analysis and enforce its quality gate.

Runs after the scanner, which writes the id of its background task to
.scannerwork/report-task.txt. The gate is read from that exact analysis, never from
an older one of the same PR.

With the owner's exception:coverage label, a failing gate passes only if new_coverage
is its single failing condition. Anything unexpected (failed analysis, missing data,
API error, timeout) fails. Standard library only.

Environment: SONAR_TOKEN, LABELS (one per line; empty on pushes), GITHUB_STEP_SUMMARY.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Fixed, so the token is only ever sent to SonarCloud.
HOST = "https://sonarcloud.io"
REPORT = Path(".scannerwork/report-task.txt")
EXCEPTION = "exception:coverage"
COVERAGE_METRIC = "new_coverage"
PENDING = {"PENDING", "IN_PROGRESS"}
TIMEOUT_SECONDS = 600
POLL_SECONDS = 5


class GateError(Exception):
    """The gate could not be read."""


def read_task_id(report: Path) -> str:
    if not report.is_file():
        raise GateError(f"{report} not found; did the scan run?")
    for line in report.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "ceTaskId" and value.strip():
            return value.strip()
    raise GateError(f"{report} has no ceTaskId")


def fetch(path: str, token: str, **params: str) -> dict:
    url = f"{HOST}/api/{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def wait_for_analysis(task_id: str, get, sleep=time.sleep, clock=time.monotonic) -> str:
    """Return the analysis id of the task. `get` is called as get(path, **params)."""
    deadline = clock() + TIMEOUT_SECONDS
    while True:
        task = get("ce/task", id=task_id)["task"]
        status = task["status"]
        if status == "SUCCESS":
            return task["analysisId"]
        if status not in PENDING:
            raise GateError(f"the analysis ended with status {status}")
        if clock() >= deadline:
            raise GateError(f"the analysis did not finish in {TIMEOUT_SECONDS} s")
        sleep(POLL_SECONDS)


def decide(gate: dict, exception: bool) -> tuple[bool, str]:
    """Return (passes, message) for a projectStatus response."""
    status = gate["status"]
    if status == "OK":
        return True, "Quality gate passed."
    if status != "ERROR":
        return False, f"Unexpected quality gate status: {status}."
    failing = [condition for condition in gate["conditions"] if condition["status"] != "OK"]
    details = "; ".join(
        f"{c['metricKey']} = {c.get('actualValue', '?')} (threshold {c.get('errorThreshold', '?')})" for c in failing
    )
    if not failing:
        return False, "Quality gate failed without a failing condition."
    if exception and [c["metricKey"] for c in failing] == [COVERAGE_METRIC]:
        return True, f"{EXCEPTION} is set; coverage is the only failing condition and is not enforced: {details}."
    return False, f"Quality gate failed: {details}."


def run(env, get=None, report: Path = REPORT) -> tuple[bool, str]:
    token = env.get("SONAR_TOKEN", "")
    if not token:
        return False, "SONAR_TOKEN is not set."
    get = get or (lambda path, **params: fetch(path, token, **params))
    exception = EXCEPTION in env.get("LABELS", "").splitlines()
    try:
        analysis_id = wait_for_analysis(read_task_id(report), get)
        return decide(get("qualitygates/project_status", analysisId=analysis_id)["projectStatus"], exception)
    except Exception as error:  # fail closed
        return False, f"Could not read the quality gate ({type(error).__name__}: {error})."


def main() -> int:
    passes, message = run(os.environ)
    level = "error" if not passes else "warning" if EXCEPTION in message else "notice"
    print(f"::{level}::{message}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## SonarCloud quality gate\n\n{message}\n")
    return 0 if passes else 1


if __name__ == "__main__":
    sys.exit(main())
