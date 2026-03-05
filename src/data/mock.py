"""
生成模拟股票数据用于测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_mock_data(
    ticker: str,
    start_date: str = "2024-01-01",
    end_date: str = "2026-02-28",
    initial_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0001
) -> pd.DataFrame:
    """
    生成模拟股票数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        initial_price: 初始价格
        volatility: 波动率
        trend: 趋势
    
    Returns:
        包含 OHLCV 数据的 DataFrame
    """
    # 生成日期序列
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 过滤掉周末
    dates = dates[dates.weekday < 5]
    
    n = len(dates)
    
    # 生成随机价格变动
    returns = np.random.normal(trend, volatility, n)
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # 生成 OHLC 数据
    high = prices * (1 + np.abs(np.random.normal(0, volatility/2, n)))
    low = prices * (1 - np.abs(np.random.normal(0, volatility/2, n)))
    open_price = prices * (1 + np.random.normal(0, volatility/4, n))
    close = prices
    
    # 确保 high 是最高价，low 是最低价
    high = np.maximum.reduce([open_price, close, high])
    low = np.minimum.reduce([open_price, close, low])
    
    # 生成成交量
    volume = np.random.randint(1000000, 10000000, n).astype(float)
    
    df = pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Dividends': np.zeros(n),
        'Stock Splits': np.zeros(n),
    }, index=dates)
    
    df.index.name = 'Date'
    df['ticker'] = ticker.upper()
    
    return df


def generate_multiple_stocks(
    tickers: list,
    **kwargs
) -> dict:
    """生成多只股票的数据"""
    data = {}
    for ticker in tickers:
        # 每只股票使用不同的初始价格和波动率
        initial_price = np.random.uniform(50, 500)
        volatility = np.random.uniform(0.015, 0.03)
        data[ticker] = generate_mock_data(
            ticker, 
            initial_price=initial_price,
            volatility=volatility,
            **kwargs
        )
    return data


if __name__ == "__main__":
    # 测试生成数据
    df = generate_mock_data("AAPL", initial_price=150, volatility=0.02)
    print(df.head())
    print(f"\nGenerated {len(df)} days of data")
