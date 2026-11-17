#!/usr/bin/env bash
# Runs once after the dev container is created (postCreateCommand).
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install \
  -r DREAM-ML-backend/GEML/requirements-base.txt \
  -r DREAM-ML-backend/GEML/requirements-dev.txt

npm ci --prefix DREAM-ML-frontend/frontend

mkdir -p "$EXPERIMENTS_DIR" "$HOST_EXPERIMENTS_DIR"

# pre-commit comes from requirements-dev.txt. Installing the hook without a config would block every commit.
if [ -f .pre-commit-config.yaml ]; then
  pre-commit install
fi
