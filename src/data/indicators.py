"""
技术指标模块
提供常用的技术分析指标计算
"""

import pandas as pd
import numpy as np
from typing import Optional


def sma(df: pd.DataFrame, period: int, column: str = "Close") -> pd.Series:
    """简单移动平均 (Simple Moving Average)"""
    return df[column].rolling(window=period).mean()


def ema(df: pd.DataFrame, period: int, column: str = "Close") -> pd.Series:
    """指数移动平均 (Exponential Moving Average)"""
    return df[column].ewm(span=period, adjust=False).mean()


def rsi(df: pd.DataFrame, period: int = 14, column: str = "Close") -> pd.Series:
    """相对强弱指数 (Relative Strength Index)"""
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def macd(
    df: pd.DataFrame, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9,
    column: str = "Close"
) -> pd.DataFrame:
    """
    MACD (Moving Average Convergence Divergence)
    
    Returns:
        DataFrame with 'macd', 'signal', 'histogram' columns
    """
    ema_fast = ema(df, fast, column)
    ema_slow = ema(df, slow, column)
    
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line.to_frame(), signal, column)
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })


def bollinger_bands(
    df: pd.DataFrame, 
    period: int = 20, 
    std_dev: float = 2.0,
    column: str = "Close"
) -> pd.DataFrame:
    """布林带 (Bollinger Bands)"""
    sma_val = sma(df, period, column)
    std = df[column].rolling(window=period).std()
    
    upper = sma_val + (std_dev * std)
    lower = sma_val - (std_dev * std)
    
    return pd.DataFrame({
        'middle': sma_val,
        'upper': upper,
        'lower': lower
    })


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """平均真实波幅 (Average True Range)"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def stochastic(
    df: pd.DataFrame, 
    k_period: int = 14, 
    d_period: int = 3
) -> pd.DataFrame:
    """随机指标 (Stochastic Oscillator)"""
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    k = 100 * (df['Close'] - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()
    
    return pd.DataFrame({
        'k': k,
        'd': d
    })


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    为 DataFrame 添加所有常用指标
    
    Args:
        df: 包含 OHLCV 数据的 DataFrame
        
    Returns:
        添加了指标的 DataFrame
    """
    result = df.copy()
    
    # 移动平均线
    result['sma_20'] = sma(result, 20)
    result['sma_50'] = sma(result, 50)
    result['sma_200'] = sma(result, 200)
    result['ema_12'] = ema(result, 12)
    result['ema_26'] = ema(result, 26)
    
    # RSI
    result['rsi_14'] = rsi(result, 14)
    
    # MACD
    macd_df = macd(result)
    result['macd'] = macd_df['macd']
    result['macd_signal'] = macd_df['signal']
    result['macd_histogram'] = macd_df['histogram']
    
    # 布林带
    bb = bollinger_bands(result)
    result['bb_middle'] = bb['middle']
    result['bb_upper'] = bb['upper']
    result['bb_lower'] = bb['lower']
    
    # ATR
    result['atr_14'] = atr(result, 14)
    
    # 随机指标
    stoch = stochastic(result)
    result['stoch_k'] = stoch['k']
    result['stoch_d'] = stoch['d']
    
    # 价格变化
    result['returns'] = result['Close'].pct_change()
    result['log_returns'] = np.log(result['Close'] / result['Close'].shift(1))
    
    return result


if __name__ == "__main__":
    # 简单测试
    from data.fetcher import StockDataFetcher
    
    fetcher = StockDataFetcher()
    df = fetcher.fetch("AAPL", period="6mo")
    df_with_indicators = add_indicators(df)
    print(df_with_indicators.tail())
