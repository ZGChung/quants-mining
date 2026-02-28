"""
回测引擎
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """单笔交易"""
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    quantity: int = 0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    
    
@dataclass
class BacktestResult:
    """回测结果"""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = None
    returns: pd.Series = None
    
    # 绩效指标
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # 每年收益
    annual_return: float = 0.0
    annual_volatility: float = 0.0
    
    def summary(self) -> Dict:
        """返回结果摘要"""
        return {
            'total_return': f"{self.total_return:.2%}",
            'annual_return': f"{self.annual_return:.2%}",
            'annual_volatility': f"{self.annual_volatility:.2%}",
            'sharpe_ratio': f"{self.sharpe_ratio:.2f}",
            'max_drawdown': f"{self.max_drawdown:.2%}",
            'win_rate': f"{self.win_rate:.2%}",
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
        }


class Backtester:
    """回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,  # 0.1% 手续费
        slippage: float = 0.0005,    # 0.05% 滑点
    ):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率
            slippage: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.trades: List[Trade] = []
        self.equity_curve: pd.Series = None
        
    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        position_size: float = 1.0,  # 仓位比例
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: 价格数据 (包含 Close 列)
            signals: 交易信号
            position_size: 每次交易的仓位比例
            
        Returns:
            BacktestResult 对象
        """
        # 清理数据
        data = data.dropna(subset=['Close'])
        signals = signals.reindex(data.index).fillna(0)
        
        # 计算资产曲线
        prices = data['Close']
        
        # 应用滑点和手续费后的价格
        buy_price = prices * (1 + self.slippage + self.commission)
        sell_price = prices * (1 - self.slippage - self.commission)
        
        # 模拟交易
        position = 0  # 当前持仓
        cash = self.initial_capital
        shares = 0
        
        equity = []
        entry_price = 0
        entry_date = None
        
        for i, (date, signal) in enumerate(signals.items()):
            price = prices.iloc[i]
            
            # 买入信号
            if signal == 1 and position == 0:
                # 全仓买入
                shares = int((cash * position_size) / buy_price.iloc[i])
                if shares > 0:
                    cost = shares * buy_price.iloc[i]
                    cash -= cost
                    position = 1
                    entry_price = buy_price.iloc[i]
                    entry_date = date
                    
            # 卖出信号
            elif signal == -1 and position == 1 and shares > 0:
                proceeds = shares * sell_price.iloc[i]
                cash += proceeds
                
                # 记录交易
                pnl = proceeds - (shares * entry_price)
                pnl_pct = pnl / (shares * entry_price)
                
                self.trades.append(Trade(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=date,
                    exit_price=sell_price.iloc[i],
                    quantity=shares,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                ))
                
                shares = 0
                position = 0
            
            # 计算当前权益
            current_equity = cash + shares * price
            equity.append(current_equity)
        
        # 如果还有持仓，最后平仓
        if position == 1 and shares > 0:
            price = prices.iloc[-1]
            proceeds = shares * sell_price.iloc[-1]
            cash += proceeds
            
            pnl = proceeds - (shares * entry_price)
            pnl_pct = pnl / (shares * entry_price)
            
            self.trades.append(Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=prices.index[-1],
                exit_price=sell_price.iloc[-1],
                quantity=shares,
                pnl=pnl,
                pnl_pct=pnl_pct
            ))
            shares = 0
        
        # 构建权益曲线
        equity_curve = pd.Series(equity, index=prices.index[:len(equity)])
        self.equity_curve = equity_curve
        
        # 计算绩效指标
        return self._calculate_metrics(equity_curve, prices)
    
    def _calculate_metrics(
        self, 
        equity: pd.Series, 
        prices: pd.Series
    ) -> BacktestResult:
        """计算绩效指标"""
        # 收益率序列
        returns = equity.pct_change().fillna(0)
        
        # 总收益率
        total_return = (equity.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 年化收益率 (假设252个交易日)
        days = len(equity)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率 (假设无风险利率为0)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 交易统计
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        return BacktestResult(
            trades=self.trades,
            equity_curve=equity,
            returns=returns,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            annual_return=annual_return,
            annual_volatility=annual_volatility,
        )
    
    def plot_results(self, result: BacktestResult):
        """绘制回测结果 (需要在有 matplotlib 的环境中运行)"""
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(3, 1, figsize=(12, 10))
            
            # 权益曲线
            axes[0].plot(result.equity_curve)
            axes[0].axhline(self.initial_capital, color='gray', linestyle='--')
            axes[0].set_title('Equity Curve')
            axes[0].set_ylabel('Portfolio Value ($)')
            axes[0].grid(True)
            
            # 收益率
            axes[1].plot(result.returns.cumsum())
            axes[1].set_title('Cumulative Returns')
            axes[1].set_ylabel('Returns')
            axes[1].grid(True)
            
            # 回撤
            cummax = result.equity_curve.cummax()
            drawdown = (result.equity_curve - cummax) / cummax
            axes[2].fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
            axes[2].set_title('Drawdown')
            axes[2].set_ylabel('Drawdown')
            axes[2].grid(True)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            logger.warning("matplotlib not available, skipping plot")


if __name__ == "__main__":
    # 测试回测
    from data.fetcher import StockDataFetcher
    from data.indicators import add_indicators
    from trading.strategies import SMACrossover
    
    fetcher = StockDataFetcher()
    data = fetcher.fetch("AAPL", period="2y")
    data = add_indicators(data)
    
    strategy = SMACrossover(20, 50)
    signals = strategy.generate_signals(data)
    
    backtester = Backtester(initial_capital=100000)
    result = backtester.run(data, signals)
    
    print("Backtest Results:")
    for key, value in result.summary().items():
        print(f"  {key}: {value}")
