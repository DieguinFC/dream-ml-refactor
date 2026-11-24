"""Gate test 7: skipped without an issue link on purpose. Never merge."""
import pytest


@pytest.mark.unit
@pytest.mark.skip(reason="Gate test 7, skipped on purpose")
def test_gate_probe():
    assert True
