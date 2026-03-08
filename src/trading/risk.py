"""
风险指标模块
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    计算 Value at Risk (VaR)

    Args:
        returns: 收益率序列
        confidence: 置信水平

    Returns:
        VaR 值
    """
    return returns.quantile(1 - confidence)


def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    计算 Conditional VaR (CVaR) / Expected Shortfall

    Args:
        returns: 收益率序列
        confidence: 置信水平

    Returns:
        CVaR 值
    """
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def calculate_sortino_ratio(
    returns: pd.Series, target_return: float = 0.0, periods_per_year: int = 252
) -> float:
    """
    计算 Sortino 比率

    Args:
        returns: 收益率序列
        target_return: 目标收益率
        periods_per_year: 每年交易日数

    Returns:
        Sortino 比率
    """
    excess_returns = returns - target_return / periods_per_year
    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0:
        return 0.0

    downside_std = downside_returns.std() * np.sqrt(periods_per_year)

    if downside_std == 0:
        return 0.0

    annual_return = excess_returns.mean() * periods_per_year
    return annual_return / downside_std


def calculate_calmar_ratio(returns: pd.Series, equity: pd.Series) -> float:
    """
    计算 Calmar 比率 (年化收益 / 最大回撤)

    Args:
        returns: 收益率序列
        equity: 权益曲线

    Returns:
        Calmar 比率
    """
    # 年化收益率
    annual_return = returns.mean() * 252

    # 最大回撤
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_drawdown = abs(drawdown.min())

    if max_drawdown == 0:
        return 0.0

    return annual_return / max_drawdown


def calculate_information_ratio(
    returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = 252
) -> float:
    """
    计算信息比率

    Args:
        returns: 策略收益率
        benchmark_returns: 基准收益率
        periods_per_year: 每年交易日数

    Returns:
        信息比率
    """
    excess_returns = returns - benchmark_returns
    tracking_error = excess_returns.std() * np.sqrt(periods_per_year)

    if tracking_error == 0:
        return 0.0

    return (excess_returns.mean() * periods_per_year) / tracking_error


def calculate_win_loss_ratio(trades: list) -> float:
    """
    计算盈亏比

    Args:
        trades: 交易列表

    Returns:
        盈亏比
    """
    if not trades:
        return 0.0

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [abs(t.pnl) for t in trades if t.pnl < 0]

    if not losses:
        return float("inf") if wins else 0.0

    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses)

    return avg_win / avg_loss if avg_loss > 0 else 0.0


def calculate_profit_factor(trades: list) -> float:
    """
    计算盈利因子

    Args:
        trades: 交易列表

    Returns:
        盈利因子
    """
    if not trades:
        return 0.0

    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return gross_profit / gross_loss


def calculate_all_risk_metrics(
    equity: pd.Series, returns: pd.Series, trades: list, benchmark_returns: pd.Series = None
) -> Dict:
    """
    计算所有风险指标

    Args:
        equity: 权益曲线
        returns: 收益率序列
        trades: 交易列表
        benchmark_returns: 基准收益率 (可选)

    Returns:
        风险指标字典
    """
    metrics = {}

    # 基础指标
    metrics["total_return"] = (equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0]
    metrics["annual_return"] = returns.mean() * 252
    metrics["annual_volatility"] = returns.std() * np.sqrt(252)

    # 风险调整指标
    metrics["sharpe_ratio"] = (
        metrics["annual_return"] / metrics["annual_volatility"]
        if metrics["annual_volatility"] > 0
        else 0
    )
    metrics["sortino_ratio"] = calculate_sortino_ratio(returns)
    metrics["calmar_ratio"] = calculate_calmar_ratio(returns, equity)

    # VaR / CVaR
    metrics["var_95"] = calculate_var(returns, 0.95)
    metrics["var_99"] = calculate_var(returns, 0.99)
    metrics["cvar_95"] = calculate_cvar(returns, 0.95)
    metrics["cvar_99"] = calculate_cvar(returns, 0.99)

    # 回撤
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    metrics["max_drawdown"] = drawdown.min()
    metrics["max_drawdown_duration"] = None  # 可扩展

    # 交易统计
    if trades:
        metrics["win_rate"] = len([t for t in trades if t.pnl > 0]) / len(trades)
        metrics["win_loss_ratio"] = calculate_win_loss_ratio(trades)
        metrics["profit_factor"] = calculate_profit_factor(trades)

    # 信息比率 (如果有基准)
    if benchmark_returns is not None:
        metrics["information_ratio"] = calculate_information_ratio(returns, benchmark_returns)

    return metrics


if __name__ == "__main__":
    # 测试
    import numpy as np

    # 模拟数据
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    equity = (1 + returns).cumprod() * 100000

    # 模拟交易
    class MockTrade:
        def __init__(self, pnl):
            self.pnl = pnl

    trades = [MockTrade(np.random.normal(100, 200)) for _ in range(50)]

    metrics = calculate_all_risk_metrics(equity, returns, trades)

    print("Risk Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            if abs(value) > 10:
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
