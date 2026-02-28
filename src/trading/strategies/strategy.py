"""
交易策略基类
定义策略接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
import pandas as pd
import numpy as np


class Signal:
    """交易信号"""
    BUY = 1
    SELL = -1
    HOLD = 0
    
    @staticmethod
    def to_string(signal: int) -> str:
        if signal == Signal.BUY:
            return "BUY"
        elif signal == Signal.SELL:
            return "SELL"
        return "HOLD"


class Strategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.position = 0  # 当前持仓状态
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            data: 包含价格数据的 DataFrame
            
        Returns:
            Series of signals (1=Buy, -1=Sell, 0=Hold)
        """
        pass
    
    def calculate_positions(self, signals: pd.Series) -> pd.Series:
        """
        根据信号计算持仓
        
        Args:
            signals: 交易信号
            
        Returns:
            持仓序列
        """
        positions = signals.copy()
        positions[positions == Signal.SELL] = 0
        
        # 持仓时保持买入信号
        positions = positions.replace(0, np.nan).ffill().fillna(0)
        return positions
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"


class SMACrossover(Strategy):
    """简单移动平均线交叉策略"""
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        super().__init__(f"SMA_Crossover_{fast_period}_{slow_period}")
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import sma
        
        signals = pd.Series(0, index=data.index)
        
        fast_sma = sma(data, self.fast_period)
        slow_sma = sma(data, self.slow_period)
        
        # 金叉买入，死叉卖出
        signals[fast_sma > slow_sma] = Signal.BUY
        signals[fast_sma < slow_sma] = Signal.SELL
        
        return signals


class RSIStrategy(Strategy):
    """RSI 策略"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import rsi
        
        signals = pd.Series(0, index=data.index)
        rsi_values = rsi(data, self.period)
        
        # RSI < 30 超卖买入，RSI > 70 超买卖出
        signals[rsi_values < self.oversold] = Signal.BUY
        signals[rsi_values > self.overbought] = Signal.SELL
        
        return signals


class MACDStrategy(Strategy):
    """MACD 策略"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD_{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import macd
        
        signals = pd.Series(0, index=data.index)
        macd_df = macd(data, self.fast, self.slow, self.signal)
        
        # MACD 金叉 Signal 买入，死叉卖出
        signals[macd_df['macd'] > macd_df['signal']] = Signal.BUY
        signals[macd_df['macd'] < macd_df['signal']] = Signal.SELL
        
        return signals


class BollingerBandsStrategy(Strategy):
    """布林带策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(f"BB_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import bollinger_bands
        
        signals = pd.Series(0, index=data.index)
        bb = bollinger_bands(data, self.period, self.std_dev)
        
        # 价格触及下轨买入，触及上轨卖出
        signals[data['Close'] < bb['lower']] = Signal.BUY
        signals[data['Close'] > bb['upper']] = Signal.SELL
        
        return signals


class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, lookback: int = 20, threshold: float = 0.02):
        super().__init__(f"Momentum_{lookback}")
        self.lookback = lookback
        self.threshold = threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=data.index)
        
        # 计算动量
        momentum = data['Close'].pct_change(self.lookback)
        
        # 动量正向买入，负向卖出
        signals[momentum > self.threshold] = Signal.BUY
        signals[momentum < -self.threshold] = Signal.SELL
        
        return signals


# 策略注册表
STRATEGIES = {
    'sma_crossover': SMACrossover,
    'rsi': RSIStrategy,
    'macd': MACDStrategy,
    'bollinger': BollingerBandsStrategy,
    'momentum': MomentumStrategy,
}


def create_strategy(strategy_name: str, **kwargs) -> Strategy:
    """
    创建策略实例
    
    Args:
        strategy_name: 策略名称
        **kwargs: 策略参数
        
    Returns:
        Strategy 实例
    """
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    return STRATEGIES[strategy_name](**kwargs)


if __name__ == "__main__":
    # 测试
    from data.fetcher import StockDataFetcher
    from data.indicators import add_indicators
    
    fetcher = StockDataFetcher()
    data = fetcher.fetch("AAPL", period="1y")
    data = add_indicators(data)
    
    # 测试 SMA 策略
    strategy = SMACrossover(20, 50)
    signals = strategy.generate_signals(data)
    print(f"Strategy: {strategy.name}")
    print(f"Buy signals: {(signals == Signal.BUY).sum()}")
    print(f"Sell signals: {(signals == Signal.SELL).sum()}")
