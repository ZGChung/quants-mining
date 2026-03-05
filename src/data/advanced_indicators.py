"""
高级技术指标模块
"""

import pandas as pd
import numpy as np
from typing import Optional


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average Directional Index (ADX)
    趋势强度指标
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # +DM 和 -DM
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # TR (True Range)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 平滑
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # ADX
    adx = dx.rolling(window=period).mean()
    
    return adx


def vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume Weighted Average Price (VWAP)
    成交量加权平均价
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap


def obv(df: pd.DataFrame) -> pd.Series:
    """
    On-Balance Volume (OBV)
    能量潮
    """
    obv = pd.Series(index=df.index, dtype=float)
    obv.iloc[0] = df['Volume'].iloc[0]
    
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + df['Volume'].iloc[i]
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - df['Volume'].iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def stochastic_rsi(df: pd.DataFrame, rsi_period: int = 14, stoch_period: int = 14) -> pd.Series:
    """
    Stochastic RSI
    随机相对强弱指数
    """
    from src.data.indicators import rsi
    
    rsi_val = rsi(df, rsi_period)
    
    stoch_rsi = 100 * (rsi_val - rsi_val.rolling(window=stoch_period).min()) / \
                 (rsi_val.rolling(window=stoch_period).max() - rsi_val.rolling(window=stoch_period).min())
    
    return stoch_rsi


def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Williams %R
    威廉指标
    """
    highest_high = df['High'].rolling(window=period).max()
    lowest_low = df['Low'].rolling(window=period).min()
    
    williams = -100 * (highest_high - df['Close']) / (highest_high - lowest_low)
    
    return williams


def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Commodity Channel Index (CCI)
    商品通道指数
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    sma = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )
    
    cci = (typical_price - sma) / (0.015 * mean_deviation)
    
    return cci


def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Money Flow Index (MFI)
    资金流量指标
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + positive_mf / negative_mf))
    
    return mfi


def ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ichimoku Cloud
    一目均衡表
    """
    nine_period_high = df['High'].rolling(window=9).max()
    nine_period_low = df['Low'].rolling(window=9).min()
    tenkan_sen = (nine_period_high + nine_period_low) / 2
    
    twenty_six_period_high = df['High'].rolling(window=26).max()
    twenty_six_period_low = df['Low'].rolling(window=26).min()
    kijun_sen = (twenty_six_period_high + twenty_six_period_low) / 2
    
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
    
    fifty_two_period_high = df['High'].rolling(window=52).max()
    fifty_two_period_low = df['Low'].rolling(window=52).min()
    senkou_span_b = ((fifty_two_period_high + fifty_two_period_low) / 2).shift(26)
    
    chikou_span = df['Close'].shift(-26)
    
    return pd.DataFrame({
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    })


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    添加所有高级指标
    """
    from src.data.indicators import add_indicators
    
    # 先添加基础指标
    result = add_indicators(df)
    
    # 添加高级指标
    result['adx_14'] = adx(result, 14)
    result['vwap'] = vwap(result)
    result['obv'] = obv(result)
    result['stoch_rsi'] = stochastic_rsi(result)
    result['williams_r'] = williams_r(result)
    result['cci_20'] = cci(result, 20)
    result['mfi_14'] = mfi(result, 14)
    
    # Ichimoku (多列)
    ichimoku_df = ichimoku(result)
    for col in ichimoku_df.columns:
        result[col] = ichimoku_df[col]
    
    return result


if __name__ == "__main__":
    from src.data.mock import generate_mock_data
    
    df = generate_mock_data("AAPL", start_date="2024-01-01")
    df = add_all_indicators(df)
    
    print("Available indicators:")
    print([col for col in df.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits', 'ticker']])
