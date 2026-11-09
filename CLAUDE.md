# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

DREAM ML is a Django + React system that automates and documents the lifecycle of machine-learning experiments (mainly classification, plus time series), using MLflow for tracking and DVC for data/model versioning. The README is in Spanish. The same guidance is also in `.github/copilot-instructions.md`.

## Commands

### Backend (`DREAM-ML-backend/GEML`, Python 3.11-compatible)

```bash
python -m pip install -r requirements-base.txt -r requirements-dev.txt
python manage.py migrate
python -m uvicorn GEML.asgi:application --port 8000   # what the container runs; `manage.py runserver` works but doesn't serve WebSockets (no daphne)
pytest                                            # full suite
pytest tests/api_tests/test_views.py::test_name   # single test
pytest -m unit                                    # by marker; also: integration, slow, requires_mlflow, requires_dvc
pytest -m "not slow"
coverage run --source=. -m pytest && coverage report --fail-under=75   # CI-equivalent
```

`pytest.ini` sets `DJANGO_SETTINGS_MODULE=GEML.settings`. Tests live in `tests/api_tests` and `tests/apiTimeSeries_tests`. Settings load `.env` from the repo root. Outside Docker, set `EXPERIMENTS_DIR` to a writable local path, because the default `/app/experimentos` is a container path.

### Frontend (`DREAM-ML-frontend/frontend`, Vite + React)

```bash
npm ci
npm run dev
npm run build
npm run lint
```

There are no frontend tests; ESLint and the production build are the only checks.

### Full stack

Copy `.env.example` to `.env`, then `docker compose up --build`. Frontend is on port 5173, Django/ASGI backend on 8000. MLflow on 5000 runs inside the backend container and is started on demand by the `start-mlflow` view. Platform-specific Buildx steps are in each service's `BUILD_INSTRUCTIONS.md`.

CI workflows are in `.github/workflows`: `django.yml` runs on `main`, `sonarcloud.yml` on `init-refactor-documents`, plus `dependency-security.yml`.

## Architecture

- **Two backend apps, two URL namespaces**: `api` (classification) is mounted at `/api/`, `apiTimeSeries` at `/api/ts/` (see `GEML/urls.py`). Check both `urls.py` modules before adding or changing an endpoint. The time-series app reuses the classification `analyze_csv` endpoint where the behavior is intentionally shared.
- **Layering**: keep HTTP handling in `views.py`. Put reusable workflow and ML logic in `services.py` or `utils.py` so it can be tested outside Django views. The two apps structure this differently: `api/services.py` has `*_logic` functions, and `apiTimeSeries/services.py` has service classes (`PreProcessingService`, `EdaService`, `DataEncodingService`, `TrainModelService`, `PipelineService`). `api` also has `data_cleaning.py`, `data_encoding.py`, `train.py`, `consumers.py` (WebSocket) and `start_mlflow.py`.
- **Time-series training**: `TrainModelService` dispatches to `train_arima_model`, `train_xgboost_model`, `train_lstm_model` (TensorFlow/Keras) or `train_patchtsmixer_model` (PyTorch), all in `apiTimeSeries/train.py`. That file is about 7k lines, so search it and read sections rather than the whole file.
- **Experiments are filesystem-backed**: experiment directories (datasets, reports, model artifacts, DVC metadata, MLflow runs) are created under `EXPERIMENTS_DIR` (container default `/app/experimentos`). Never assume a repo-relative path.
- **Each experiment is its own git + DVC repo**: services shell out to `dvc add`, `git commit` and `dvc push` with `cwd=experiment_dir`, so these commits never touch this repo. Workflow steps record their inputs and outputs in the experiment's `pipeline_config.json`.
- **Pipeline re-execution**: `run-pipeline` takes that config, creates a new experiment, fetches the raw data from the old one with `dvc get`, and replays the steps through the same logic as the individual endpoints. A change to a step's config or outputs therefore also affects the replay.
- **Progress updates**: services push to `/ws/progreso/` (`GEML/routing.py`, `api/consumers.py`) through an in-memory channel layer, which only works within a single process.
- **Frontend state machine**: `App.jsx` renders `Dashboard`, whose tabs host both the classification and the time-series (`TS*`) cards. `AppContext.jsx` holds the ordered workflow (create experiment → DVC setup → cleaning → EDA → encoding → training). MLflow, manual EDA, and summary steps are tracked separately. When you add a step, extend the context flags and status state rather than adding competing global state. Components in `src/components` are the per-step cards and call the API through the shared Axios config.
- **API paths in the frontend**: the Axios `baseURL` already ends in `/api`, so cards use paths like `/train-model/` and `/ts/train-model/`. Routes must match exactly: `/api/ts/run-pipeline` has no trailing slash, unlike the other routes.
- **Docker build args** `VITE_API_URL`, `VITE_WS_URL`, `VITE_EXPERIMENTS_DIR` must stay aligned with the backend service and mounted paths. `VITE_API_URL` and `VITE_WS_URL` are compiled into the bundle and used by the browser, and `nginx.conf` has no API proxy, so they must be reachable from the host browser. `VITE_WS_URL` includes the `ws://` scheme. Don't hard-code localhost or container paths in components.

## Conventions

- Preserve the JSON response shapes and HTTP statuses the frontend cards expect when refactoring services (subprocess, DVC, MLflow, and filesystem behavior is part of that contract).
- Add tests beside the workflow they exercise and use the existing pytest markers.
- Dependencies are pinned. Update `requirements-base.txt` and `requirements-dev.txt` together.
- Don't commit runtime artifacts: experiment data, MLflow/DVC state, `media/`, `db.sqlite3`, coverage output, frontend build output.
- Keep the existing GPLv3 copyright headers in files that have them.
- Known test-suite issue (see `punto.md`): several backend tests patch `builtins.open` globally with `mock_open`, which is too broad and can break MLflow's own file reads. Prefer narrowly scoped file mocks, and patch names where the code under test resolves them (`api.services.pd.read_csv`, not `pd.read_csv`).
- Past design and implementation plans are in `thoughts/shared/plans/` and `Docs/`. They're useful background, but check them against the current code.
