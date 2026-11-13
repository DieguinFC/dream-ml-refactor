# Pre-refactor baseline

This folder is a frozen snapshot of DREAM ML **before any refactor or cleanup**. Every before/after comparison in the thesis is measured against it.

- Commit: `e02c0bb` (tag `baseline-pre-refactor`)
- CI run: [42134886141](https://github.com/DieguinFC/dream-ml-refactor/actions/runs/42134886141), SonarCloud branch `init-refactor-documents`
- Details and headline metrics: [`manifest.json`](manifest.json)

**Do not edit these files.** If a value turns out to be wrong, add a note to `manifest.json` in a separate PR and explain why. Do not overwrite the data.

## Headline metrics

| Metric | Value |
|---|---|
| Lines of code (ncloc) | 23,733 |
| Vulnerabilities | 212 |
| Code smells | 223 |
| Bugs | 3 |
| Security hotspots | 0 |
| Coverage | 36.1 % |
| Duplicated lines | 23.5 % |

## Files

| File | Content | Produced by |
|---|---|---|
| `export_sonar.py` | Downloads the Sonar data through the Web API (standard library only) | Written for task 0.3 |
| `sonar-analyses.json` | Analyses of the branch, with dates and commits | `export_sonar.py` |
| `sonar-measures.json` | All project-level metrics | `export_sonar.py` |
| `sonar-measures-by-file.json` | Size, complexity, duplication, coverage and issues per file | `export_sonar.py` |
| `sonar-issues.json` | Every issue, with rule, severity and location | `export_sonar.py` |
| `sonar-hotspots.json` | Security hotspots | `export_sonar.py` |
| `sonar-quality-config.json` | Quality gate definition and status, quality profiles | `export_sonar.py` (needs a token) |
| `pip-audit.json` | Known vulnerabilities in backend dependencies | `pip-audit` |
| `npm-audit.json` | Known vulnerabilities in frontend dependencies | `npm audit` |
| `ci-run/` | Coverage and test-result reports | `gh run download` |
| `sonar-run-13.txt` | Full CI log of the run above | GitHub Actions |

## How it was produced

From the repository root, in PowerShell:

```powershell
# Sonar data. The token stays in this shell session only.
$env:SONAR_TOKEN = Read-Host "Sonar token"
python Docs\baseline\export_sonar.py

# CI reports
gh run download 42134886141 -n backend-test-and-coverage-reports -D Docs\baseline\ci-run

# Dependency audits (both exit non-zero when they find vulnerabilities; that is expected)
cd DREAM-ML-frontend\frontend
npm audit --json > ..\..\Docs\baseline\npm-audit.json
cd ..\..
python -m venv $env:TEMP\auditenv
& $env:TEMP\auditenv\Scripts\python.exe -m pip install pip-audit
& $env:TEMP\auditenv\Scripts\pip-audit.exe -r DREAM-ML-backend\GEML\requirements-base.txt --no-deps --disable-pip -f json -o Docs\baseline\pip-audit.json
```

The audits reflect the advisory databases on the day they ran (2026-11-13), not on the baseline commit date.

## Notes

- **Latest analysis.** The most recent Sonar analysis of `init-refactor-documents` is for commit `94a7254`, which only added documents outside `sonar.sources`. Its metrics are identical to the analysis of `e02c0bb`. See `manifest.json`.
- **Coverage scope.** CI measured coverage with `--source=api,apiTimeSeries`, which differs from `.coveragerc` (`source=.`). Compare later measurements with the same scope.
- **Final measurement (task 0.38).** Run `python Docs\baseline\export_sonar.py --branch develop --out <new folder>` to produce the same files for the after-refactor state.
