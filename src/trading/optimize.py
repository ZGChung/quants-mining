"""
策略参数优化
网格搜索最佳策略参数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import itertools

from src.data.mock import generate_multiple_stocks
from src.data import add_indicators
from src.trading.strategies import create_strategy, Strategy
from src.trading.backtesting.portfolio_backtest import PortfolioBacktester


@dataclass
class OptimizationResult:
    """优化结果"""

    best_params: Dict[str, Any]
    best_return: float
    best_sharpe: float
    all_results: List[Dict]


class StrategyOptimizer:
    """策略参数优化器"""

    def __init__(
        self,
        data: Dict[str, pd.DataFrame],
        strategy_name: str,
        metric: str = "sharpe_ratio",  # 优化目标
    ):
        self.data = data
        self.strategy_name = strategy_name
        self.metric = metric

    def optimize(
        self,
        param_grid: Dict[str, List[Any]],
        initial_capital: float = 100000,
        max_positions: int = 3,
    ) -> OptimizationResult:
        """
        运行网格搜索优化

        Args:
            param_grid: 参数网格 {param_name: [values]}
            initial_capital: 初始资金
            max_positions: 最大持仓数

        Returns:
            OptimizationResult
        """
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(itertools.product(*param_values))

        print(f"🔍 Testing {len(combinations)} parameter combinations...")

        results = []

        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))

            try:
                # 创建策略
                strategy = create_strategy(self.strategy_name, **params)

                # 运行回测
                backtester = PortfolioBacktester(
                    initial_capital=initial_capital,
                    max_positions=max_positions,
                    position_size=1.0 / max_positions,
                )

                result = backtester.run(self.data, strategy)

                # 记录结果
                record = {
                    "params": params,
                    "total_return": result["total_return"],
                    "annual_return": result["annual_return"],
                    "sharpe_ratio": result["sharpe_ratio"],
                    "max_drawdown": result["max_drawdown"],
                    "total_trades": result["total_trades"],
                }
                results.append(record)

                print(
                    f"  [{i+1}/{len(combinations)}] {params} -> Sharpe: {record['sharpe_ratio']:.3f}, Return: {record['total_return']:.2%}"
                )

            except Exception as e:
                print(f"  [{i+1}/{len(combinations)}] {params} -> Error: {e}")
                continue

        # 找到最佳参数
        if not results:
            raise ValueError("No valid results found")

        # 按优化目标排序
        if self.metric == "sharpe_ratio":
            results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        elif self.metric == "total_return":
            results.sort(key=lambda x: x["total_return"], reverse=True)
        elif self.metric == "max_drawdown":
            results.sort(key=lambda x: x["max_drawdown"], reverse=True)  # 最大回撤越小越好

        best = results[0]

        print(f"\n✅ Best parameters: {best['params']}")
        print(f"   Sharpe Ratio: {best['sharpe_ratio']:.3f}")
        print(f"   Total Return: {best['total_return']:.2%}")

        return OptimizationResult(
            best_params=best["params"],
            best_return=best["total_return"],
            best_sharpe=best["sharpe_ratio"],
            all_results=results,
        )


def run_optimization_example():
    """运行优化示例"""
    print("=" * 60)
    print("🔧 Strategy Parameter Optimization")
    print("=" * 60)

    # 准备数据
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    data = generate_multiple_stocks(tickers, start_date="2024-01-01")
    for ticker in data:
        data[ticker] = add_indicators(data[ticker])

    # SMA 策略参数网格
    param_grid = {
        "fast_period": [10, 20, 30],
        "slow_period": [30, 50, 70],
    }

    # 运行优化
    optimizer = StrategyOptimizer(data, "sma_crossover", metric="sharpe_ratio")
    result = optimizer.optimize(param_grid, initial_capital=100000, max_positions=3)

    # 打印 Top 5
    print("\n📊 Top 5 Results:")
    print("-" * 60)
    for i, r in enumerate(result.all_results[:5]):
        print(
            f"{i+1}. Sharpe: {r['sharpe_ratio']:.3f}, Return: {r['total_return']:.2%}, Params: {r['params']}"
        )

    return result


if __name__ == "__main__":
    run_optimization_example()
