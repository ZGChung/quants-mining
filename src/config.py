"""
配置管理模块
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class DataConfig:
    """数据配置"""
    source: str = "mock"  # 'mock', 'yahoo', 'alpaca', etc.
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    api_key: Optional[str] = None
    tickers: list = None
    
    def __post_init__(self):
        if self.tickers is None:
            self.tickers = ["AAPL", "MSFT", "GOOGL"]


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    max_positions: int = 3
    period: str = "1y"


@dataclass
class AppConfig:
    """应用配置"""
    data: DataConfig = None
    backtest: BacktestConfig = None
    strategies: list = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = DataConfig()
        if self.backtest is None:
            self.backtest = BacktestConfig()
        if self.strategies is None:
            self.strategies = [
                StrategyConfig("sma_crossover", parameters={"fast_period": 20, "slow_period": 50}),
                StrategyConfig("rsi", parameters={"period": 14}),
            ]


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.config = self.load()
    
    def load(self) -> AppConfig:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return AppConfig(
                        data=DataConfig(**data.get('data', {})),
                        backtest=BacktestConfig(**data.get('backtest', {})),
                    )
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return AppConfig()
    
    def save(self):
        """保存配置"""
        data = {
            'data': asdict(self.config.data),
            'backtest': asdict(self.config.backtest),
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"配置已保存到 {self.config_file}")
    
    def get_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略参数"""
        for s in self.config.strategies:
            if s.name == strategy_name:
                return s.parameters
        return {}
    
    def set_strategy_params(self, strategy_name: str, parameters: Dict[str, Any]):
        """设置策略参数"""
        for s in self.config.strategies:
            if s.name == strategy_name:
                s.parameters = parameters
                return
        
        # 新策略
        self.config.strategies.append(
            StrategyConfig(strategy_name, parameters=parameters)
        )


# 全局配置实例
config = ConfigManager()


if __name__ == "__main__":
    # 测试
    config = ConfigManager()
    print(f"Initial capital: {config.config.backtest.initial_capital}")
    print(f"Data source: {config.config.data.source}")
    
    # 修改配置
    config.config.backtest.initial_capital = 200000
    config.save()
    
    print("✅ Config test completed")
