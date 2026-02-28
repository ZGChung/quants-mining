"""
策略模块
"""

from .strategy import (
    Strategy, Signal,
    SMACrossover, RSIStrategy, MACDStrategy,
    BollingerBandsStrategy, MomentumStrategy,
    create_strategy, STRATEGIES
)

# 导入高级策略
from .advanced import (
    MeanReversionStrategy,
    BreakoutStrategy,
    DualMAStrategy,
    VolatilityStrategy,
    CompositeStrategy,
    TrendFollowingStrategy,
)

__all__ = [
    'Strategy', 'Signal',
    'SMACrossover', 'RSIStrategy', 'MACDStrategy',
    'BollingerBandsStrategy', 'MomentumStrategy',
    'MeanReversionStrategy', 'BreakoutStrategy',
    'DualMAStrategy', 'VolatilityStrategy',
    'CompositeStrategy', 'TrendFollowingStrategy',
    'create_strategy', 'STRATEGIES'
]
