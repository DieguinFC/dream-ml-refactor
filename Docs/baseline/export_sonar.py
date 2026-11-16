"""Export a frozen snapshot of SonarCloud data for one branch of DREAM ML.

Used for the pre-refactor baseline (task 0.3) and reused for the final
measurement (task 0.38). Standard library only.

Usage (PowerShell):
    $env:SONAR_TOKEN = Read-Host "Sonar token"
    python Docs/baseline/export_sonar.py
    python Docs/baseline/export_sonar.py --branch develop --out Docs/phase-0-final

The token is read from the SONAR_TOKEN environment variable and is never
written to disk. Without a token, public data is still exported, but the
quality profile and quality gate details may be unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOST = "https://sonarcloud.io"
PROJECT = "DieguinFC_dream-ml-refactor"
ORGANIZATION = "dieguinfc"
PAGE_SIZE = 500
# component_tree accepts at most 15 metric keys per request.
FILE_METRIC_CHUNKS = [
    [
        "ncloc", "lines", "functions", "classes", "statements",
        "complexity", "cognitive_complexity", "comment_lines_density",
        "duplicated_lines", "duplicated_blocks", "duplicated_lines_density",
        "coverage", "line_coverage", "lines_to_cover", "uncovered_lines",
    ],
    [
        "bugs", "vulnerabilities", "code_smells", "security_hotspots",
        "sqale_index", "sqale_rating", "reliability_rating", "security_rating",
        "branch_coverage", "conditions_to_cover", "uncovered_conditions",
    ],
]


class SonarClient:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def get(self, path: str, **params: object) -> dict:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        request = urllib.request.Request(f"{HOST}/{path}?{query}")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                body = error.read().decode("utf-8", "replace")[:300]
                if error.code == 429 and attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"{path} -> HTTP {error.code}: {body}") from None
        raise RuntimeError(f"{path} -> too many retries")

    def paged(self, path: str, items_key: str, **params: object) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            data = self.get(path, p=page, ps=PAGE_SIZE, **params)
            batch = data.get(items_key, [])
            items.extend(batch)
            paging = data.get("paging", {})
            total = paging.get("total", len(items))
            if not batch or len(items) >= total:
                return items
            if len(items) >= 10_000:
                raise RuntimeError(f"{path}: more than 10,000 results; the API cannot page further")
            page += 1


def export_measures(client: SonarClient, branch: str) -> dict:
    metrics = client.paged("api/metrics/search", "metrics")
    keys = sorted(m["key"] for m in metrics if not m.get("hidden"))
    measures: list[dict] = []
    for start in range(0, len(keys), 50):
        data = client.get(
            "api/measures/component",
            component=PROJECT,
            branch=branch,
            metricKeys=",".join(keys[start:start + 50]),
        )
        measures.extend(data["component"].get("measures", []))
    return {"measures": sorted(measures, key=lambda m: m["metric"])}


def export_measures_by_file(client: SonarClient, branch: str) -> dict:
    files: dict[str, dict] = {}
    for chunk in FILE_METRIC_CHUNKS:
        components = client.paged(
            "api/measures/component_tree",
            "components",
            component=PROJECT,
            branch=branch,
            qualifiers="FIL",
            metricKeys=",".join(chunk),
        )
        for component in components:
            entry = files.setdefault(
                component["key"],
                {"path": component.get("path"), "language": component.get("language"), "measures": {}},
            )
            for measure in component.get("measures", []):
                entry["measures"][measure["metric"]] = measure.get("value")
    return {"files": [dict(key=key, **files[key]) for key in sorted(files)]}


def export_issues(client: SonarClient, branch: str) -> dict:
    issues = client.paged(
        "api/issues/search",
        "issues",
        componentKeys=PROJECT,
        branch=branch,
        additionalFields="_all",
    )
    return {"issues": sorted(issues, key=lambda i: i["key"])}


def export_hotspots(client: SonarClient, branch: str) -> dict:
    hotspots = client.paged("api/hotspots/search", "hotspots", projectKey=PROJECT, branch=branch)
    return {"hotspots": sorted(hotspots, key=lambda h: h["key"])}


def export_quality_config(client: SonarClient, branch: str) -> dict:
    result: dict[str, object] = {
        "gate_status": client.get("api/qualitygates/project_status", projectKey=PROJECT, branch=branch),
    }
    gate = client.get("api/qualitygates/get_by_project", project=PROJECT, organization=ORGANIZATION)
    result["gate"] = gate
    gate_name = gate.get("qualityGate", {}).get("name")
    if gate_name:
        result["gate_conditions"] = client.get("api/qualitygates/show", name=gate_name, organization=ORGANIZATION)
    result["profiles"] = client.get("api/qualityprofiles/search", project=PROJECT, organization=ORGANIZATION)
    return result


def export_analyses(client: SonarClient, branch: str) -> dict:
    return {"analyses": client.paged("api/project_analyses/search", "analyses", project=PROJECT, branch=branch)}


EXPORTS = {
    "sonar-analyses.json": export_analyses,
    "sonar-measures.json": export_measures,
    "sonar-measures-by-file.json": export_measures_by_file,
    "sonar-issues.json": export_issues,
    "sonar-hotspots.json": export_hotspots,
    "sonar-quality-config.json": export_quality_config,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--branch", default="init-refactor-documents")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument(
        "--expect-revision",
        default="e02c0bbf34b5a8b34b2949facc7157f535667783",
        help="Commit the measured code must match; only reported, never enforced.",
    )
    args = parser.parse_args()

    token = os.environ.get("SONAR_TOKEN") or None
    if not token:
        print("warning: SONAR_TOKEN is not set; gate and profile data may be missing", file=sys.stderr)
    client = SonarClient(token)
    args.out.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for filename, exporter in EXPORTS.items():
        try:
            payload = exporter(client, args.branch)
        except (RuntimeError, urllib.error.URLError, KeyError) as error:
            failures.append(f"{filename}: {error}")
            print(f"FAILED  {filename}: {error}", file=sys.stderr)
            continue
        document = {
            "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "host": HOST,
            "project": PROJECT,
            "branch": args.branch,
            "authenticated": token is not None,
            **payload,
        }
        path = args.out / filename
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        count = next((len(v) for v in payload.values() if isinstance(v, list)), None)
        print(f"ok      {filename}" + (f" ({count} items)" if count is not None else ""))

    analyses_path = args.out / "sonar-analyses.json"
    if analyses_path.exists():
        analyses = json.loads(analyses_path.read_text(encoding="utf-8"))["analyses"]
        latest = analyses[0].get("revision") if analyses else None
        print(f"latest analysis revision: {latest}")
        if latest != args.expect_revision:
            print(
                f"note: latest analysis is not {args.expect_revision[:7]}; "
                "check sonar-analyses.json and record the difference in manifest.json",
                file=sys.stderr,
            )

    if failures:
        print(f"\n{len(failures)} export(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
