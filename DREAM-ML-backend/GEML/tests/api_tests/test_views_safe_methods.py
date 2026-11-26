"""Tests for the HTTP methods accepted by the read-only api views."""
import json
import pytest
from django.test import Client, RequestFactory

from api import views

READ_ONLY_VIEWS = [views.get_pipeline_config, views.get_experiment_summary]


@pytest.mark.unit
@pytest.mark.parametrize("view", READ_ONLY_VIEWS)
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_unsafe_methods_return_405(view, method):
    request = getattr(RequestFactory(), method)("/?directory_path=/test/experiment")

    response = view(request)

    assert response.status_code == 405
    assert set(response["Allow"].split(", ")) == {"GET", "HEAD"}


@pytest.mark.unit
def test_get_pipeline_config_still_answers_get(tmp_path):
    (tmp_path / "pipeline_config.json").write_text('{"steps": []}', encoding="utf-8")
    request = RequestFactory().get("/", {"directory_path": str(tmp_path)})

    response = views.get_pipeline_config(request)

    assert response.status_code == 200
    assert json.loads(response.content) == {"steps": []}


@pytest.mark.unit
def test_get_pipeline_config_does_not_need_a_csrf_token(tmp_path):
    client = Client(enforce_csrf_checks=True)

    response = client.get("/api/get-pipeline-config/", {"directory_path": str(tmp_path)})

    assert response.status_code == 404
