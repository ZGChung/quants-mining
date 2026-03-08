"""
QuantMining 工具函数
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


def format_percentage(value: float) -> str:
    """格式化百分比"""
    return f"{value * 100:.2f}%"


def format_currency(value: float, currency: str = "$") -> str:
    """格式化货币"""
    return f"{currency}{value:,.2f}"


def format_number(value: float, decimals: int = 2) -> str:
    """格式化数字"""
    return f"{value:.{decimals}f}"


def get_trading_days(year: int = None) -> int:
    """获取一年的交易日数"""
    if year is None:
        year = datetime.now().year
    # 简化计算：一年约252个交易日
    return 252


def calculate_annual_return(total_return: float, days: int) -> float:
    """计算年化收益率"""
    years = days / 252
    if years <= 0:
        return 0
    return (1 + total_return) ** (1 / years) - 1


def calculate_annual_volatility(returns: pd.Series) -> float:
    """计算年化波动率"""
    return returns.std() * np.sqrt(252)


def create_price_history(
    start_price: float, days: int, volatility: float = 0.02, trend: float = 0.0001
) -> pd.Series:
    """
    创建模拟价格历史

    Args:
        start_price: 起始价格
        days: 天数
        volatility: 波动率
        trend: 趋势

    Returns:
        价格序列
    """
    returns = np.random.normal(trend, volatility, days)
    prices = start_price * np.exp(np.cumsum(returns))
    return pd.Series(prices)


def get_fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
    """计算斐波那契回撤"""
    diff = high - low
    return {
        "0.0%": high,
        "23.6%": high - diff * 0.236,
        "38.2%": high - diff * 0.382,
        "50.0%": high - diff * 0.5,
        "61.8%": high - diff * 0.618,
        "78.6%": high - diff * 0.786,
        "100.0%": low,
    }


def detect_support_resistance(prices: pd.Series, window: int = 20) -> Dict[str, List[float]]:
    """
    检测支撑位和阻力位

    Args:
        prices: 价格序列
        window: 窗口大小

    Returns:
        支撑位和阻力位字典
    """
    # 简化版本
    rolling_max = prices.rolling(window).max()
    rolling_min = prices.rolling(window).min()

    resistance = rolling_max.dropna().unique()[-5:].tolist()
    support = rolling_min.dropna().unique()[-5:].tolist()

    return {"resistance": resistance, "support": support}


def calculate_ichimoku_cloud(data: pd.DataFrame) -> pd.DataFrame:
    """
    计算一目均衡表

    Args:
        data: OHLCV 数据

    Returns:
        包含 Ichimoku 指标的 DataFrame
    """
    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    # Tenkan-sen (转换线)
    tenkan_sen = (high.rolling(9).max() + low.rolling(9).min()) / 2

    # Kijun-sen (基准线)
    kijun_sen = (high.rolling(26).max() + low.rolling(26).min()) / 2

    # Senkou Span A (先行上线 A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

    # Senkou Span B (先行上线 B)
    senkou_span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)

    # Chikou Span (迟行线)
    chikou_span = close.shift(-26)

    return pd.DataFrame(
        {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_span_a,
            "senkou_span_b": senkou_span_b,
            "chikou_span": chikou_span,
        }
    )


def save_results(result: Dict, filename: str, directory: str = "results") -> str:
    """
    保存回测结果

    Args:
        result: 回测结果
        filename: 文件名
        directory: 目录

    Returns:
        保存路径
    """
    os.makedirs(directory, exist_ok=True)

    filepath = os.path.join(directory, filename)

    # 序列化
    save_data = {
        "total_return": result.get("total_return", 0),
        "sharpe_ratio": result.get("sharpe_ratio", 0),
        "max_drawdown": result.get("max_drawdown", 0),
        "win_rate": result.get("win_rate", 0),
        "total_trades": result.get("total_trades", 0),
        "timestamp": datetime.now().isoformat(),
    }

    with open(filepath + ".json", "w") as f:
        json.dump(save_data, f, indent=2)

    # 保存权益曲线
    if "equity_curve" in result and result["equity_curve"] is not None:
        result["equity_curve"].to_csv(filepath + ".csv")

    return filepath


def load_results(filename: str, directory: str = "results") -> Dict:
    """加载回测结果"""
    filepath = os.path.join(directory, filename)

    with open(filepath + ".json", "r") as f:
        return json.load(f)


# 性能指标颜色
PERFORMANCE_COLORS = {
    "good": "#00CC66",  # 绿色 - 好
    "neutral": "#FFAA00",  # 黄色 - 一般
    "bad": "#FF4444",  # 红色 - 差
    "excellent": "#00FF00",  # 亮绿 - 优秀
}


def get_performance_color(value: float, metric: str = "return") -> str:
    """
    根据指标值返回颜色

    Args:
        value: 指标值
        metric: 指标类型 ('return', 'sharpe', 'drawdown', 'win_rate')

    Returns:
        颜色代码
    """
    if metric == "return":
        if value > 0.2:
            return PERFORMANCE_COLORS["excellent"]
        elif value > 0:
            return PERFORMANCE_COLORS["good"]
        elif value > -0.1:
            return PERFORMANCE_COLORS["neutral"]
        else:
            return PERFORMANCE_COLORS["bad"]

    elif metric == "sharpe":
        if value > 1.5:
            return PERFORMANCE_COLORS["excellent"]
        elif value > 1:
            return PERFORMANCE_COLORS["good"]
        elif value > 0:
            return PERFORMANCE_COLORS["neutral"]
        else:
            return PERFORMANCE_COLORS["bad"]

    elif metric == "drawdown":
        if abs(value) < 0.1:
            return PERFORMANCE_COLORS["excellent"]
        elif abs(value) < 0.2:
            return PERFORMANCE_COLORS["good"]
        elif abs(value) < 0.3:
            return PERFORMANCE_COLORS["neutral"]
        else:
            return PERFORMANCE_COLORS["bad"]

    elif metric == "win_rate":
        if value > 0.6:
            return PERFORMANCE_COLORS["excellent"]
        elif value > 0.5:
            return PERFORMANCE_COLORS["good"]
        elif value > 0.4:
            return PERFORMANCE_COLORS["neutral"]
        else:
            return PERFORMANCE_COLORS["bad"]

    return PERFORMANCE_COLORS["neutral"]


if __name__ == "__main__":
    # 测试
    print(format_percentage(0.1234))
    print(format_currency(12345.67))
    print(get_performance_color(0.15, "return"))
    print(get_performance_color(1.5, "sharpe"))
