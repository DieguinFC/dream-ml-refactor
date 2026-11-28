"""Tests for the values GEML.settings reads from the environment."""
import os
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

from GEML import settings as settings_module

SETTINGS_PATH = Path(settings_module.__file__)
ENV_NAME = "DJANGO_SECRET_KEY"


def load_settings(secret_key=None):
    """Run settings.py with the given secret key, ignoring the local .env file."""
    with patch.dict(os.environ), patch("dotenv.load_dotenv"):
        os.environ.pop(ENV_NAME, None)
        if secret_key is not None:
            os.environ[ENV_NAME] = secret_key
        return runpy.run_path(str(SETTINGS_PATH))


@pytest.mark.unit
class TestSecretKey:
    def test_uses_environment_variable(self):
        assert load_settings("key-from-environment")["SECRET_KEY"] == "key-from-environment"

    @pytest.mark.parametrize("secret_key", [None, ""])
    def test_generates_random_key_when_missing_or_empty(self, secret_key):
        first = load_settings(secret_key)["SECRET_KEY"]
        second = load_settings(secret_key)["SECRET_KEY"]

        assert len(first) >= 50
        assert first != second

    def test_no_key_in_source(self):
        assert "django-insecure" not in SETTINGS_PATH.read_text(encoding="utf-8")
