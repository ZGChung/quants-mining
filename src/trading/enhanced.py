"""
QuantMining - 增强版
添加更多技术指标和高级功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """计算夏普比率"""
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


def calculate_sortino(returns: pd.Series, target: float = 0.0) -> float:
    """计算 Sortino 比率"""
    excess = returns - target / 252
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0
    return np.sqrt(252) * excess.mean() / downside.std()


def calculate_max_drawdown(equity: pd.Series) -> float:
    """计算最大回撤"""
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    return drawdown.min()


def calculate_win_rate(trades: List[Dict]) -> float:
    """计算胜率"""
    if not trades:
        return 0
    wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
    return wins / len(trades)


def calculate_profit_factor(trades: List[Dict]) -> float:
    """计算盈利因子"""
    if not trades:
        return 0
    gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
    gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0
    return gross_profit / gross_loss


def calculate_calmar(returns: pd.Series, equity: pd.Series) -> float:
    """计算 Calmar 比率"""
    annual_return = returns.mean() * 252
    max_dd = abs(calculate_max_drawdown(equity))
    if max_dd == 0:
        return 0
    return annual_return / max_dd


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 VaR (Value at Risk)"""
    return returns.quantile(1 - confidence)


def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 CVaR (Conditional VaR)"""
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def generate_trading_signals(
    data: pd.DataFrame,
    strategy: str = "sma_crossover",
    **params
) -> pd.Series:
    """
    生成交易信号
    
    Args:
        data: OHLCV 数据
        strategy: 策略名称
        **params: 策略参数
        
    Returns:
        信号序列 (1=买入, -1=卖出, 0=持有)
    """
    signals = pd.Series(0, index=data.index)
    
    if strategy == "sma_crossover":
        fast = params.get("fast_period", 20)
        slow = params.get("slow_period", 50)
        
        sma_fast = data['Close'].rolling(fast).mean()
        sma_slow = data['Close'].rolling(slow).mean()
        
        signals[sma_fast > sma_slow] = 1
        signals[sma_fast < sma_slow] = -1
        
    elif strategy == "rsi":
        period = params.get("period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)
        
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals[rsi < oversold] = 1
        signals[rsi > overbought] = -1
        
    elif strategy == "macd":
        fast = params.get("fast", 12)
        slow = params.get("slow", 26)
        signal_period = params.get("signal", 9)
        
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        
        signals[macd > signal] = 1
        signals[macd < signal] = -1
        
    elif strategy == "bollinger":
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2.0)
        
        sma = data['Close'].rolling(period).mean()
        std = data['Close'].rolling(period).std()
        
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        
        signals[data['Close'] < lower] = 1
        signals[data['Close'] > upper] = -1
        
    elif strategy == "momentum":
        lookback = params.get("lookback", 20)
        threshold = params.get("threshold", 0.02)
        
        momentum = data['Close'].pct_change(lookback)
        
        signals[momentum > threshold] = 1
        signals[momentum < -threshold] = -1
        
    elif strategy == "mean_reversion":
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2.0)
        
        sma = data['Close'].rolling(period).mean()
        std = data['Close'].rolling(period).std()
        
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        
        signals[data['Close'] < lower] = 1
        signals[data['Close'] > upper] = -1
        
    elif strategy == "breakout":
        lookback = params.get("lookback", 20)
        
        highest = data['High'].rolling(lookback).max()
        lowest = data['Low'].rolling(lookback).min()
        
        signals[data['Close'] > highest.shift(1)] = 1
        signals[data['Close'] < lowest.shift(1)] = -1
        
    return signals


def run_backtest(
    data: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float = 100000,
    commission: float = 0.001,
    slippage: float = 0.0005
) -> Dict:
    """
    快速回测
    
    Args:
        data: 价格数据
        signals: 交易信号
        initial_capital: 初始资金
        commission: 手续费率
        slippage: 滑点率
        
    Returns:
        回测结果字典
    """
    # 初始化
    cash = initial_capital
    position = 0
    trades = []
    equity = []
    
    prices = data['Close']
    
    for i in range(len(data)):
        price = prices.iloc[i]
        signal = signals.iloc[i] if i < len(signals) else 0
        
        # 买入
        if signal == 1 and position == 0:
            buy_price = price * (1 + slippage + commission)
            shares = int(cash / buy_price)
            if shares > 0:
                cost = shares * buy_price
                cash -= cost
                position = shares
                trades.append({'action': 'BUY', 'price': buy_price, 'shares': shares})
        
        # 卖出
        elif signal == -1 and position > 0:
            sell_price = price * (1 - slippage - commission)
            proceeds = position * sell_price
            cash += proceeds
            trades.append({'action': 'SELL', 'price': sell_price, 'shares': position})
            position = 0
        
        # 记录权益
        equity_value = cash + position * price
        equity.append(equity_value)
    
    # 计算指标
    equity_series = pd.Series(equity, index=data.index[:len(equity)])
    returns = equity_series.pct_change().dropna()
    
    total_return = (equity[-1] - initial_capital) / initial_capital
    sharpe = calculate_sharpe(returns)
    max_dd = calculate_max_drawdown(equity_series)
    win_rate = calculate_win_rate(trades)
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'total_trades': len(trades),
        'equity_curve': equity_series,
        'trades': trades
    }


# 策略注册表
STRATEGIES = {
    'sma_crossover': {
        'name': '均线交叉',
        'params': {
            'fast_period': (5, 50, 20),
            'slow_period': (20, 200, 50)
        }
    },
    'rsi': {
        'name': 'RSI 超买超卖',
        'params': {
            'period': (5, 30, 14),
            'oversold': (10, 40, 30),
            'overbought': (60, 90, 70)
        }
    },
    'macd': {
        'name': 'MACD',
        'params': {
            'fast': (5, 20, 12),
            'slow': (15, 50, 26),
            'signal': (5, 15, 9)
        }
    },
    'bollinger': {
        'name': '布林带',
        'params': {
            'period': (10, 50, 20),
            'std_dev': (1.0, 3.0, 2.0)
        }
    },
    'momentum': {
        'name': '动量',
        'params': {
            'lookback': (5, 50, 20),
            'threshold': (0.01, 0.1, 0.02)
        }
    },
    'mean_reversion': {
        'name': '均值回归',
        'params': {
            'period': (10, 50, 20),
            'std_dev': (1.0, 3.0, 2.0)
        }
    },
    'breakout': {
        'name': '突破',
        'params': {
            'lookback': (10, 50, 20)
        }
    },
}


if __name__ == "__main__":
    # 快速测试
    from src.data.mock import generate_mock_data
    
    data = generate_mock_data("AAPL", start_date="2024-01-01")
    
    signals = generate_trading_signals(data, "sma_crossover", fast_period=20, slow_period=50)
    
    result = run_backtest(data, signals)
    
    print(f"Total Return: {result['total_return']:.2%}")
    print(f"Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"Trades: {result['total_trades']}")
