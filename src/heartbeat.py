"""
QuantMining 心跳机制
定期检查和自动优化
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatStatus:
    """心跳状态"""

    timestamp: datetime
    status: str  # 'healthy', 'warning', 'error'
    message: str
    last_optimization: Optional[datetime] = None
    data_freshness: Optional[datetime] = None


class Heartbeat:
    """量化系统心跳"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.last_check = None
        self.status = None
        self.check_interval = self.config.get("check_interval", 3600)  # 默认1小时
        self.last_optimization_time = None

    def check_health(self) -> HeartbeatStatus:
        """
        检查系统健康状态

        Returns:
            HeartbeatStatus
        """
        self.last_check = datetime.now()
        messages = []
        status = "healthy"

        # 检查 1: 数据可用性
        try:
            from src.data.mock import generate_mock_data

            test_data = generate_mock_data("TEST", start_date="2025-01-01")
            if test_data.empty:
                messages.append("数据生成失败")
                status = "warning"
            else:
                messages.append("数据模块正常")
        except Exception as e:
            messages.append(f"数据模块错误: {e}")
            status = "error"

        # 检查 2: 策略可用性
        try:
            from src.trading.strategies import STRATEGIES

            if len(STRATEGIES) < 3:
                messages.append("策略数量不足")
                status = "warning"
            else:
                messages.append(f"策略模块正常 ({len(STRATEGIES)} 个策略)")
        except Exception as e:
            messages.append(f"策略模块错误: {e}")
            status = "error"

        # 检查 3: 回测引擎
        try:
            from src.trading.backtesting import PortfolioBacktester

            backtester = PortfolioBacktester(initial_capital=10000)
            messages.append("回测引擎正常")
        except Exception as e:
            messages.append(f"回测引擎错误: {e}")
            status = "error"

        # 检查 4: 优化器
        try:
            from src.trading.optimize import StrategyOptimizer

            messages.append("优化器正常")
        except Exception as e:
            messages.append(f"优化器错误: {e}")
            status = "warning"

        self.status = HeartbeatStatus(
            timestamp=self.last_check,
            status=status,
            message="; ".join(messages),
            last_optimization=self.last_optimization_time,
            data_freshness=self.last_check,
        )

        return self.status

    def should_optimize(self) -> bool:
        """判断是否应该运行优化"""
        if self.last_optimization_time is None:
            return True

        hours_since = (datetime.now() - self.last_optimization_time).total_seconds() / 3600
        return hours_since >= self.config.get("optimize_interval", 24)  # 默认24小时

    def run_auto_optimization(self) -> Optional[Dict]:
        """
        运行自动优化

        Returns:
            优化结果
        """
        if not self.should_optimize():
            logger.info("Skipping optimization - not time yet")
            return None

        logger.info("Running auto-optimization...")

        try:
            from src.data.mock import generate_multiple_stocks
            from src.data import add_indicators
            from src.trading.optimize import StrategyOptimizer

            # 生成测试数据
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
            data = generate_multiple_stocks(tickers, start_date="2024-01-01")
            for ticker in data:
                data[ticker] = add_indicators(data[ticker])

            # SMA 参数优化
            param_grid = {
                "fast_period": [10, 15, 20, 25, 30],
                "slow_period": [40, 50, 60, 70, 80],
            }

            optimizer = StrategyOptimizer(data, "sma_crossover", metric="sharpe_ratio")
            result = optimizer.optimize(param_grid)

            self.last_optimization_time = datetime.now()

            return {
                "best_params": result.best_params,
                "best_sharpe": result.best_sharpe,
                "best_return": result.best_return,
                "timestamp": self.last_optimization_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Auto-optimization failed: {e}")
            return None

    def run_diagnostics(self) -> Dict:
        """
        运行系统诊断

        Returns:
            诊断报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "health": None,
            "optimization_needed": self.should_optimize(),
            "recommendations": [],
        }

        # 健康检查
        health = self.check_health()
        report["health"] = {"status": health.status, "message": health.message}

        # 生成建议
        if health.status == "error":
            report["recommendations"].append("⚠️ 系统有错误，需要立即检查")
        elif health.status == "warning":
            report["recommendations"].append("⚡ 系统有警告，建议检查")
        else:
            report["recommendations"].append("✅ 系统运行正常")

        if self.should_optimize():
            report["recommendations"].append("📈 建议运行参数优化")

        # 检查策略表现
        try:
            from src.data.mock import generate_multiple_stocks
            from src.data import add_indicators
            from src.trading.strategies import SMACrossover
            from src.trading.backtesting import PortfolioBacktester

            tickers = ["AAPL", "MSFT", "GOOGL"]
            data = generate_multiple_stocks(tickers, start_date="2025-01-01")
            for ticker in data:
                data[ticker] = add_indicators(data[ticker])

            strategy = SMACrossover(20, 50)
            backtester = PortfolioBacktester(initial_capital=100000)
            result = backtester.run(data, strategy)

            if result["total_return"] < 0:
                report["recommendations"].append(
                    f"📉 当前策略表现不佳 (收益: {result['total_return']:.1%})，建议优化参数"
                )
            else:
                report["recommendations"].append(
                    f"📈 当前策略表现良好 (收益: {result['total_return']:.1%})"
                )

        except Exception as e:
            report["recommendations"].append(f"❌ 诊断过程出错: {e}")

        return report


def run_heartbeat_check():
    """运行心跳检查"""
    print("=" * 60)
    print("💓 QuantMining Heartbeat Check")
    print("=" * 60)

    heartbeat = Heartbeat()

    # 健康检查
    print("\n🔍 Running health check...")
    status = heartbeat.check_health()
    print(f"Status: {status.status.upper()}")
    print(f"Message: {status.message}")

    # 诊断
    print("\n📋 Running diagnostics...")
    report = heartbeat.run_diagnostics()
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  {rec}")

    print("\n" + "=" * 60)

    return report


if __name__ == "__main__":
    run_heartbeat_check()
