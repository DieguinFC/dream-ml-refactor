"""Tests for the HTTP methods accepted by the apiTimeSeries index view."""
import pytest
from django.test import Client


@pytest.mark.unit
def test_index_answers_get():
    response = Client().get("/api/ts/")

    assert response.status_code == 200


@pytest.mark.unit
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_index_rejects_unsafe_methods(method):
    response = getattr(Client(), method)("/api/ts/")

    assert response.status_code == 405
    assert set(response["Allow"].split(", ")) == {"GET", "HEAD"}
