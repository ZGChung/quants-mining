"""
QuantMining - 量化挖矿项目
探索量子计算在量化交易中的应用
"""

from . import data
from . import trading
from .pipeline import Pipeline, PipelineConfig

__version__ = "0.1.0"

__all__ = [
    "data",
    "trading",
    "Pipeline",
    "PipelineConfig",
]
