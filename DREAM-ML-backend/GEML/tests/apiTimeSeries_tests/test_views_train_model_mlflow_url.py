"""Tests for the MLflow UI link returned by the apiTimeSeries train_model view."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from apiTimeSeries import views

EXPECTED_PATH = "/#/experiments/exp-123/runs/run-123"


@pytest.mark.unit
@pytest.mark.parametrize("mlflow_ui_url, expected_base", [
    (None, "http://localhost:5000"),
    ("http://backend:5000", "http://backend:5000"),
    ("https://mlflow.example.com", "https://mlflow.example.com"),
])
@patch("apiTimeSeries.views.trainModelService")
@patch("apiTimeSeries.views.mlflow")
@patch("apiTimeSeries.views.os.path.isdir", return_value=True)
def test_mlflow_ui_has_a_single_scheme(_mock_isdir, mock_mlflow, mock_train,
                                       mlflow_ui_url, expected_base):
    training_result = {"run_id": "run-123"}
    mock_train.train_model_logic.return_value = training_result
    mock_mlflow.active_run.return_value = None
    mock_mlflow.get_experiment_by_name.return_value = MagicMock(experiment_id="exp-123")
    request = RequestFactory().post("/train-model/", {
        "file": SimpleUploadedFile("train.csv", b"a,b\n1,2\n", content_type="text/csv"),
        "data": json.dumps({"experiment_dir": "/test/experiment"}),
    })

    with patch.dict(os.environ):
        os.environ.pop("MLFLOW_UI_URL", None)
        if mlflow_ui_url is not None:
            os.environ["MLFLOW_UI_URL"] = mlflow_ui_url
        response = views.train_model(request)

    assert response.status_code == 200
    assert json.loads(response.content)["mlflow_ui"] == expected_base + EXPECTED_PATH
