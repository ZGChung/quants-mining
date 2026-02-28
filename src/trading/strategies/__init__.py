"""
Trading Strategies Module

Contains various quantitative trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self.positions = {}
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from market data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signal column
        """
        raise NotImplementedError("Subclasses must implement generate_signals")


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy
    
    Buy when short MA crosses above long MA, sell when short MA crosses below long MA.
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__("MA_Crossover")
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate MA crossover signals"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close'] if 'close' in data.columns else data.iloc[:, 0]
        
        # Calculate moving averages
        signals['short_ma'] = signals['price'].rolling(window=self.short_window).mean()
        signals['long_ma'] = signals['price'].rolling(window=self.long_window).mean()
        
        # Generate signals
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] <= signals['long_ma'], 'signal'] = -1
        
        # Position: 1 for long, 0 for flat, -1 for short
        signals['position'] = signals['signal'].diff()
        
        return signals


class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) Strategy
    
    Buy when RSI is oversold (<30), sell when RSI is overbought (>70).
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based signals"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close'] if 'close' in data.columns else data.iloc[:, 0]
        
        # Calculate RSI
        delta = signals['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        signals['rsi'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals['signal'] = 0
        signals.loc[signals['rsi'] < self.oversold, 'signal'] = 1  # Buy
        signals.loc[signals['rsi'] > self.overbought, 'signal'] = -1  # Sell
        
        signals['position'] = signals['signal']
        
        return signals


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy
    
    Buy when price is below moving average, sell when price is above.
    """
    
    def __init__(self, window: int = 20, std_dev: float = 2.0):
        super().__init__("MeanReversion")
        self.window = window
        self.std_dev = std_dev
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate mean reversion signals"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close'] if 'close' in data.columns else data.iloc[:, 0]
        
        # Calculate Bollinger Bands
        signals['ma'] = signals['price'].rolling(window=self.window).mean()
        signals['std'] = signals['price'].rolling(window=self.window).std()
        
        signals['upper'] = signals['ma'] + (self.std_dev * signals['std'])
        signals['lower'] = signals['ma'] - (self.std_dev * signals['std'])
        
        # Generate signals
        signals['signal'] = 0
        signals.loc[signals['price'] < signals['lower'], 'signal'] = 1  # Buy
        signals.loc[signals['price'] > signals['upper'], 'signal'] = -1  # Sell
        
        signals['position'] = signals['signal']
        
        return signals


# Strategy factory
STRATEGIES = {
    'ma_crossover': MovingAverageCrossover,
    'rsi': RSIStrategy,
    'mean_reversion': MeanReversionStrategy,
}


def get_strategy(name: str, **kwargs) -> BaseStrategy:
    """Get a strategy by name"""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name](**kwargs)
