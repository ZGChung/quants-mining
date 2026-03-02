"""
更多高级策略
"""

import pandas as pd
import numpy as np
from src.trading.strategies.strategy import Strategy, Signal
from src.data.indicators import sma, ema, rsi, macd, bollinger_bands, atr


class ADXStrategy(Strategy):
    """ADX 趋势策略"""
    
    def __init__(self, adx_period: int = 14, adx_threshold: int = 25):
        super().__init__(f"ADX_{adx_period}_{adx_threshold}")
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import adx
        
        signals = pd.Series(0, index=data.index)
        adx_val = adx(data, self.adx_period)
        
        # ADX > threshold 表示趋势明确
        signals[adx_val > self.adx_threshold] = Signal.BUY
        
        return signals


class VWAPStrategy(Strategy):
    """VWAP 策略"""
    
    def __init__(self, deviation_threshold: float = 0.02):
        super().__init__(f"VWAP_{deviation_threshold}")
        self.threshold = deviation_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import vwap
        
        signals = pd.Series(0, index=data.index)
        vwap_val = vwap(data)
        
        # 价格低于 VWAP 买入，高于卖出
        signals[data['Close'] < vwap_val * (1 - self.threshold)] = Signal.BUY
        signals[data['Close'] > vwap_val * (1 + self.threshold)] = Signal.SELL
        
        return signals


class OBVStrategy(Strategy):
    """OBV 能量潮策略"""
    
    def __init__(self, period: int = 20):
        super().__init__(f"OBV_{period}")
        self.period = period
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import obv
        
        signals = pd.Series(0, index=data.index)
        obv_val = obv(data)
        obv_ma = obv_val.rolling(window=self.period).mean()
        
        # OBV 上穿均线买入
        signals[obv_val > obv_ma] = Signal.BUY
        signals[obv_val < obv_ma] = Signal.SELL
        
        return signals


class CCIStrategy(Strategy):
    """CCI 商品通道指数策略"""
    
    def __init__(self, period: int = 20, oversold: float = -100, overbought: float = 100):
        super().__init__(f"CCI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import cci
        
        signals = pd.Series(0, index=data.index)
        cci_val = cci(data, self.period)
        
        signals[cci_val < self.oversold] = Signal.BUY
        signals[cci_val > self.overbought] = Signal.SELL
        
        return signals


class MFIStrategy(Strategy):
    """MFI 资金流量策略"""
    
    def __init__(self, period: int = 14, oversold: int = 20, overbought: int = 80):
        super().__init__(f"MFI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import mfi
        
        signals = pd.Series(0, index=data.index)
        mfi_val = mfi(data, self.period)
        
        signals[mfi_val < self.oversold] = Signal.BUY
        signals[mfi_val > self.overbought] = Signal.SELL
        
        return signals


class WilliamsRStrategy(Strategy):
    """Williams %R 策略"""
    
    def __init__(self, period: int = 14, oversold: int = -80, overbought: int = -20):
        super().__init__(f"WilliamsR_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.advanced_indicators import williams_r
        
        signals = pd.Series(0, index=data.index)
        wr_val = williams_r(data, self.period)
        
        signals[wr_val < self.oversold] = Signal.BUY
        signals[wr_val > self.overbought] = Signal.SELL
        
        return signals


class StochasticStrategy(Strategy):
    """随机指标策略"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3, oversold: int = 20, overbought: int = 80):
        super().__init__(f"Stochastic_{k_period}_{d_period}")
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        from src.data.indicators import stochastic
        
        signals = pd.Series(0, index=data.index)
        stoch = stochastic(data, self.k_period, self.d_period)
        
        # %K < 20 超卖买入，%K > 80 超买卖出
        signals[stoch['k'] < self.oversold] = Signal.BUY
        signals[stoch['k'] > self.overbought] = Signal.SELL
        
        return signals


class MultiTimeframeStrategy(Strategy):
    """多时间框架策略"""
    
    def __init__(self, short_period: int = 10, long_period: int = 50):
        super().__init__(f"MultiTF_{short_period}_{long_period}")
        self.short_period = short_period
        self.long_period = long_period
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=data.index)
        
        # 使用日线数据
        short_ma = sma(data, self.short_period)
        long_ma = sma(data, self.long_period)
        
        # 金叉买入，死叉卖出
        signals[short_ma > long_ma] = Signal.BUY
        signals[short_ma < long_ma] = Signal.SELL
        
        return signals


# 注册更多策略
from src.trading.strategies.strategy import STRATEGIES

STRATEGIES.update({
    'adx': ADXStrategy,
    'vwap': VWAPStrategy,
    'obv': OBVStrategy,
    'cci': CCIStrategy,
    'mfi': MFIStrategy,
    'williams_r': WilliamsRStrategy,
    'stochastic': StochasticStrategy,
    'multi_timeframe': MultiTimeframeStrategy,
})


if __name__ == "__main__":
    from src.data.mock import generate_mock_data
    from src.data.advanced_indicators import add_all_indicators
    
    data = generate_mock_data("TEST", start_date="2024-01-01")
    data = add_all_indicators(data)
    
    strategies = [
        ADXStrategy(14, 25),
        VWAPStrategy(0.02),
        OBVStrategy(20),
        CCIStrategy(20),
        MFIStrategy(14),
        WilliamsRStrategy(14),
        StochasticStrategy(14, 3),
    ]
    
    print(f"Total strategies: {len(STRATEGIES)}")
    for s in strategies:
        signals = s.generate_signals(data)
        print(f"{s.name}: Buy={sum(signals==1)}, Sell={sum(signals==-1)}")
