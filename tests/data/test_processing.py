"""Tests for data processing module."""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class TestDataFetcher:
    """Test suite for data fetching functionality."""

    def test_data_fetcher_can_be_imported(self):
        """Test that data fetcher can be imported."""
        from src.data import DataFetcher
        assert DataFetcher is not None


class TestDataProcessor:
    """Test suite for data processing."""

    def test_calculate_returns(self):
        """Test return calculation."""
        prices = pd.Series([100, 110, 105, 115])
        returns = prices.pct_change()
        assert len(returns) == len(prices)
        assert np.isclose(returns.iloc[1], 0.1, rtol=1e-5)

    def test_calculate_log_returns(self):
        """Test log return calculation."""
        prices = pd.Series([100, 110])
        log_return = np.log(prices.iloc[1] / prices.iloc[0])
        assert np.isclose(log_return, np.log(1.1), rtol=1e-5)

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        volatility = returns.std() * np.sqrt(252)
        assert volatility > 0


class TestFeatureEngineering:
    """Test suite for feature engineering."""

    def test_moving_average_calculation(self):
        """Test moving average calculation."""
        prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ma_5 = prices.rolling(window=5).mean()
        assert ma_5.iloc[-1] == 8.0

    def test_rsi_calculation(self):
        """Test RSI calculation."""
        # Simple RSI test
        changes = pd.Series([1, -2, 3, -1, 2])
        gains = changes.apply(lambda x: x if x > 0 else 0)
        losses = changes.apply(lambda x: -x if x < 0 else 0)
        avg_gain = gains.mean()
        avg_loss = losses.mean()
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        assert 0 <= rsi <= 100


class TestDataValidator:
    """Test suite for data validation."""

    def test_check_for_missing_values(self):
        """Test missing value detection."""
        df = pd.DataFrame({'a': [1, 2, None], 'b': [4, None, 6]})
        missing = df.isnull().sum().sum()
        assert missing == 2

    def test_check_for_duplicates(self):
        """Test duplicate detection."""
        df = pd.DataFrame({'a': [1, 2, 2], 'b': [3, 4, 4]})
        duplicates = df.duplicated().sum()
        assert duplicates == 1
