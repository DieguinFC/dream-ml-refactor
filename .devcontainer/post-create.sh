#!/usr/bin/env bash
# Runs once after the dev container is created (postCreateCommand).
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install \
  -r DREAM-ML-backend/GEML/requirements-base.txt \
  -r DREAM-ML-backend/GEML/requirements-dev.txt
python -m pip install pre-commit==4.2.0

npm ci --prefix DREAM-ML-frontend/frontend

mkdir -p "$EXPERIMENTS_DIR" "$HOST_EXPERIMENTS_DIR"

# The hooks config arrives in a later PR; installing the hook before it exists would block every commit.
if [ -f .pre-commit-config.yaml ]; then
  pre-commit install
fi
