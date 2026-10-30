"""apiTimeSeries_tests specific fixtures."""
import pytest
import pandas as pd
import numpy as np
import logging
from unittest.mock import MagicMock, patch

# Suppress CodeCarbon logging errors about closed file handles
logging.getLogger('codecarbon').setLevel(logging.CRITICAL + 1)
# Add NullHandler to completely suppress logging output
logging.getLogger('codecarbon').addHandler(logging.NullHandler())


@pytest.fixture(scope="session", autouse=True)
def disable_codecarbon_globally():
    """Disable CodeCarbon globally for all tests to prevent I/O errors.

    This fixture runs automatically for all tests and patches CodeCarbon
    to prevent instantiation, which eliminates the logging errors about
    closed file handles from background threads.
    """
    with patch('codecarbon.EmissionsTracker', MagicMock) as mock_tracker:
        # Configure the mock to return a mock tracker that does nothing
        mock_instance = MagicMock()
        mock_instance.start.return_value = None
        mock_instance.stop.return_value = None
        mock_tracker.return_value = mock_instance
        yield


@pytest.fixture(scope="session")
def sample_time_series_df():
    """Sample time series DataFrame for testing.

    Scope: session - expensive to create, reusable across tests
    """
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'date': dates,
        'value': np.random.randn(100).cumsum(),
        'feature1': np.random.randn(100)
    })


@pytest.fixture(scope="session")
def sample_lstm_sequences():
    """Sample LSTM input sequences.

    Scope: session - expensive to create, reusable across tests
    """
    np.random.seed(42)
    n_samples = 50
    n_timesteps = 10
    n_features = 3
    X = np.random.randn(n_samples, n_timesteps, n_features)
    y = np.random.randn(n_samples, 1)
    return X, y


@pytest.fixture(scope="session")
def sample_arima_data():
    """Sample stationary time series for ARIMA testing.

    Scope: session - reusable across tests
    """
    np.random.seed(42)
    return np.random.randn(100)
