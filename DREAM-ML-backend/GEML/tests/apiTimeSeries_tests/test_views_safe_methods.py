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


CSRF_SECRET = "a" * 32


@pytest.mark.unit
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_index_rejects_unsafe_methods_without_csrf_token_with_403(method):
    client = Client(enforce_csrf_checks=True)

    response = getattr(client, method)("/api/ts/")

    assert response.status_code == 403


@pytest.mark.unit
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_index_rejects_unsafe_methods_with_csrf_token_with_405(method):
    client = Client(enforce_csrf_checks=True)
    client.cookies["csrftoken"] = CSRF_SECRET

    response = getattr(client, method)("/api/ts/", headers={"X-CSRFToken": CSRF_SECRET})

    assert response.status_code == 405
    assert set(response["Allow"].split(", ")) == {"GET", "HEAD"}
