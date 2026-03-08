"""
回测结果可视化
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def plot_backtest_results(
    equity_curve: pd.Series, title: str = "Backtest Results", save_path: Optional[str] = None
):
    """
    绘制回测结果图表

    Args:
        equity_curve: 权益曲线
        title: 图表标题
        save_path: 保存路径
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, axes = plt.subplots(3, 1, figsize=(14, 12))

        # 1. 权益曲线
        ax1 = axes[0]
        ax1.plot(equity_curve.index, equity_curve.values, linewidth=2, color="#2E86AB")
        ax1.axhline(
            equity_curve.iloc[0], color="gray", linestyle="--", alpha=0.7, label="Initial Capital"
        )
        ax1.fill_between(
            equity_curve.index,
            equity_curve.values,
            equity_curve.iloc[0],
            where=equity_curve.values >= equity_curve.iloc[0],
            color="green",
            alpha=0.3,
            interpolate=True,
        )
        ax1.fill_between(
            equity_curve.index,
            equity_curve.values,
            equity_curve.iloc[0],
            where=equity_curve.values < equity_curve.iloc[0],
            color="red",
            alpha=0.3,
            interpolate=True,
        )
        ax1.set_title(f"{title} - Equity Curve", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Portfolio Value ($)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # 2. 收益率曲线
        ax2 = axes[1]
        returns = equity_curve.pct_change().fillna(0)
        cumulative_returns = (1 + returns).cumprod() - 1
        ax2.plot(
            cumulative_returns.index, cumulative_returns.values * 100, linewidth=2, color="#A23B72"
        )
        ax2.axhline(0, color="gray", linestyle="--", alpha=0.7)
        ax2.fill_between(
            cumulative_returns.index,
            cumulative_returns.values * 100,
            0,
            where=cumulative_returns.values >= 0,
            color="green",
            alpha=0.3,
        )
        ax2.fill_between(
            cumulative_returns.index,
            cumulative_returns.values * 100,
            0,
            where=cumulative_returns.values < 0,
            color="red",
            alpha=0.3,
        )
        ax2.set_title("Cumulative Returns (%)", fontsize=14, fontweight="bold")
        ax2.set_ylabel("Return (%)")
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # 3. 回撤曲线
        ax3 = axes[2]
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax * 100
        ax3.fill_between(drawdown.index, drawdown.values, 0, color="red", alpha=0.5)
        ax3.plot(drawdown.index, drawdown.values, color="darkred", linewidth=1)
        ax3.set_title("Drawdown (%)", fontsize=14, fontweight="bold")
        ax3.set_ylabel("Drawdown (%)")
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Chart saved to {save_path}")

        plt.show()

    except ImportError:
        logger.warning("matplotlib not installed, skipping plot")
    except Exception as e:
        logger.error(f"Error plotting results: {e}")


def plot_strategy_comparison(results: Dict[str, Dict], save_path: Optional[str] = None):
    """
    绘制多策略对比图

    Args:
        results: 策略结果字典 {strategy_name: {metrics}}
        save_path: 保存路径
    """
    try:
        import matplotlib.pyplot as plt

        strategies = list(results.keys())

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 总收益对比
        ax1 = axes[0, 0]
        returns = [results[s]["total_return"] * 100 for s in strategies]
        colors = ["green" if r > 0 else "red" for r in returns]
        bars = ax1.bar(strategies, returns, color=colors, alpha=0.7)
        ax1.axhline(0, color="gray", linestyle="--")
        ax1.set_title("Total Return (%)", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Return (%)")
        for bar, val in zip(bars, returns):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        # 2. 夏普比率对比
        ax2 = axes[0, 1]
        sharpes = [results[s]["sharpe_ratio"] for s in strategies]
        colors = ["green" if s > 0 else "red" for s in sharpes]
        bars = ax2.bar(strategies, sharpes, color=colors, alpha=0.7)
        ax2.axhline(0, color="gray", linestyle="--")
        ax2.set_title("Sharpe Ratio", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Sharpe Ratio")
        for bar, val in zip(bars, sharpes):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        # 3. 最大回撤对比
        ax3 = axes[1, 0]
        drawdowns = [abs(results[s]["max_drawdown"] * 100) for s in strategies]
        ax3.bar(strategies, drawdowns, color="red", alpha=0.7)
        ax3.set_title("Max Drawdown (%)", fontsize=12, fontweight="bold")
        ax3.set_ylabel("Drawdown (%)")
        for i, (s, val) in enumerate(zip(strategies, drawdowns)):
            ax3.text(i, val + 1, f"{val:.1f}%", ha="center", va="bottom", fontsize=10)

        # 4. 交易次数
        ax4 = axes[1, 1]
        trades = [results[s]["total_trades"] for s in strategies]
        ax4.bar(strategies, trades, color="blue", alpha=0.7)
        ax4.set_title("Total Trades", fontsize=12, fontweight="bold")
        ax4.set_ylabel("Number of Trades")
        for i, val in enumerate(trades):
            ax4.text(i, val + 1, str(val), ha="center", va="bottom", fontsize=10)

        plt.suptitle("Strategy Comparison", fontsize=16, fontweight="bold", y=1.02)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"📊 Chart saved to {save_path}")

        plt.show()

    except ImportError:
        logger.warning("matplotlib not installed, skipping plot")


def plot_equity_curves(equity_curves: Dict[str, pd.Series], save_path: Optional[str] = None):
    """
    绘制多条权益曲线对比

    Args:
        equity_curves: 权益曲线字典 {name: Series}
        save_path: 保存路径
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(14, 7))

        for name, curve in equity_curves.items():
            # 归一化到起始值
            normalized = curve / curve.iloc[0] * 100
            ax.plot(normalized.index, normalized.values, linewidth=2, label=name)

        ax.axhline(100, color="gray", linestyle="--", alpha=0.7)
        ax.set_title("Normalized Equity Curves (Base = 100)", fontsize=14, fontweight="bold")
        ax.set_ylabel("Relative Value")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        plt.show()

    except ImportError:
        logger.warning("matplotlib not installed, skipping plot")


if __name__ == "__main__":
    # 测试
    from src.data.mock import generate_multiple_stocks
    from src.data import add_indicators
    from src.trading.strategies import SMACrossover, RSIStrategy
    from src.trading.backtesting.portfolio_backtest import PortfolioBacktester

    # 生成数据
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = generate_multiple_stocks(tickers, start_date="2024-01-01")
    for ticker in data:
        data[ticker] = add_indicators(data[ticker])

    # 测试 SMA 策略
    strategy = SMACrossover(20, 50)
    backtester = PortfolioBacktester(initial_capital=100000, max_positions=3)
    result = backtester.run(data, strategy)

    # 绘制结果
    plot_backtest_results(result["equity_curve"], title=f"{strategy.name} Backtest")
