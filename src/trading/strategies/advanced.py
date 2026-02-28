"""
更多交易策略
"""

import pandas as pd
import numpy as np
from typing import Optional
from src.trading.strategies.strategy import Strategy, Signal


class MeanReversionStrategy(Strategy):
    """均值回归策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(f"MeanReversion_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=data.index)
        
        # 计算布林带
        sma = data['Close'].rolling(window=self.period).mean()
        std = data['Close'].rolling(window=self.period).std()
        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        
        # 价格低于下轨买入，高于上轨卖出
        signals[data['Close'] < lower] = Signal.BUY
        signals[data['Close'] > upper] = Signal.SELL
        
        return signals


class BreakoutStrategy(Strategy):
    """突破策略"""
    
    def __init__(self, lookback: int = 20, confirm_bars: int = 2):
        super().__init__(f"Breakout_{lookback}")
        self.lookback = lookback
        self.confirm_bars = confirm_bars
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=data.index)
        
        # 最高价突破
        highest = data['High'].rolling(window=self.lookback).max()
        # 最低价跌破
        lowest = data['Low'].rolling(window=self.lookback).min()
        
        # 向上突破买入
        signals[data['Close'] > highest.shift(1)] = Signal.BUY
        # 向下跌破卖出
        signals[data['Close'] < lowest.shift(1)] = Signal.SELL
        
        return signals


class DualMAStrategy(Strategy):
    """双均线策略 (更严格)"""
    
    def __init__(self, fast: int = 10, slow: int = 30, threshold: float = 0.02):
        super().__init__(f"DualMA_{fast}_{slow}_{threshold}")
        self.fast = fast
        self.slow = slow
        self.threshold = threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import ema
        
        signals = pd.Series(0, index=data.index)
        
        fast_ema = ema(data, self.fast)
        slow_ema = ema(data, self.slow)
        
        # 计算价差
        diff = (fast_ema - slow_ema) / slow_ema
        
        # 金叉且价差超过阈值买入
        signals[diff > self.threshold] = Signal.BUY
        # 死叉且价差低于负阈值卖出
        signals[diff < -self.threshold] = Signal.SELL
        
        return signals


class VolatilityStrategy(Strategy):
    """波动率策略"""
    
    def __init__(self, period: int = 20, atr_multiplier: float = 2.0):
        super().__init__(f"Volatility_{period}_{atr_multiplier}")
        self.period = period
        self.multiplier = atr_multiplier
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import atr, sma
        
        signals = pd.Series(0, index=data.index)
        
        # 计算 ATR
        atr_val = atr(data, self.period)
        sma_price = sma(data, self.period)
        
        # 计算止损/止盈位置
        upper_band = sma_price + self.multiplier * atr_val
        lower_band = sma_price - self.multiplier * atr_val
        
        # 价格触及上轨卖出，下轨买入
        signals[data['Close'] < lower_band] = Signal.BUY
        signals[data['Close'] > upper_band] = Signal.SELL
        
        return signals


class CompositeStrategy(Strategy):
    """复合策略 - 结合多个指标"""
    
    def __init__(
        self,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70
    ):
        super().__init__(f"Composite_RSI_MACD")
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import rsi, macd
        
        signals = pd.Series(0, index=data.index)
        
        # RSI 信号
        rsi_val = rsi(data, self.rsi_period)
        rsi_buy = rsi_val < self.rsi_oversold
        rsi_sell = rsi_val > self.rsi_overbought
        
        # MACD 信号
        macd_df = macd(data, self.macd_fast, self.macd_slow, self.macd_signal)
        macd_buy = macd_df['macd'] > macd_df['signal']
        macd_sell = macd_df['macd'] < macd_df['signal']
        
        # 复合条件: RSI 超卖 + MACD 金叉 = 买入
        signals[rsi_buy & macd_buy] = Signal.BUY
        
        # RSI 超买 + MACD 死叉 = 卖出
        signals[rsi_sell & macd_sell] = Signal.SELL
        
        return signals


class TrendFollowingStrategy(Strategy):
    """趋势跟随策略 - 结合 MA 和 ADX"""
    
    def __init__(self, ma_period: int = 50, adx_period: int = 14, adx_threshold: int = 25):
        super().__init__(f"Trend_{ma_period}_{adx_period}")
        self.ma_period = ma_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import sma
        
        signals = pd.Series(0, index=data.index)
        
        # 简单趋势判断: 价格在 MA 上方
        ma = sma(data, self.ma_period)
        
        # 价格上穿 MA 买入
        signals[data['Close'] > ma] = Signal.BUY
        # 价格下穿 MA 卖出
        signals[data['Close'] < ma] = Signal.SELL
        
        return signals


# 注册新策略
from src.trading.strategies.strategy import STRATEGIES

STRATEGIES.update({
    'mean_reversion': MeanReversionStrategy,
    'breakout': BreakoutStrategy,
    'dual_ma': DualMAStrategy,
    'volatility': VolatilityStrategy,
    'composite': CompositeStrategy,
    'trend_following': TrendFollowingStrategy,
})


if __name__ == "__main__":
    # 测试新策略
    from src.data.mock import generate_mock_data
    from src.data import add_indicators
    
    data = generate_mock_data("TEST", start_date="2024-01-01")
    data = add_indicators(data)
    
    strategies = [
        MeanReversionStrategy(20, 2.0),
        BreakoutStrategy(20),
        DualMAStrategy(10, 30),
        VolatilityStrategy(20, 2.0),
        CompositeStrategy(),
        TrendFollowingStrategy(50),
    ]
    
    for s in strategies:
        signals = s.generate_signals(data)
        print(f"{s.name}: Buy={sum(signals==1)}, Sell={sum(signals==-1)}")
