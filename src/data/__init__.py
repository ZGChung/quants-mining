"""
数据模块
"""

from .fetcher import StockDataFetcher
from .indicators import (
    sma, ema, rsi, macd, bollinger_bands, 
    atr, stochastic, add_indicators
)
from .real import DataFetcher, data_fetcher, get_data, set_api_keys
from .mock import generate_multiple_stocks

__all__ = [
    'StockDataFetcher',
    'sma', 'ema', 'rsi', 'macd', 'bollinger_bands',
    'atr', 'stochastic', 'add_indicators',
    'DataFetcher', 'data_fetcher', 'get_data', 'set_api_keys',
    'generate_multiple_stocks'
]
