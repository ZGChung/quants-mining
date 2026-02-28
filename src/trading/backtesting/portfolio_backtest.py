"""
多股票组合策略回测
同时管理多只股票的仓位
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

from src.data import StockDataFetcher, add_indicators
from src.trading.strategies import Strategy, Signal, create_strategy

logger = logging.getLogger(__name__)


@dataclass
class PortfolioTrade:
    """投资组合交易记录"""
    date: pd.Timestamp
    ticker: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    value: float
    commission: float


class PortfolioBacktester:
    """组合策略回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        max_positions: int = 5,
        position_size: float = 0.2,  # 每只股票分配 20% 资金
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.max_positions = max_positions
        self.position_size = position_size
        
        self.trades: List[PortfolioTrade] = []
        self.equity_curve: Optional[pd.Series] = None
        
    def run(
        self,
        data: Dict[str, pd.DataFrame],
        strategy: Strategy,
    ) -> Dict:
        """
        运行组合回测
        
        Args:
            data: 股票数据字典 {ticker: DataFrame}
            strategy: 交易策略
            
        Returns:
            回测结果字典
        """
        # 获取所有日期
        all_dates = set()
        for df in data.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)
        
        # 初始化
        cash = self.initial_capital
        positions: Dict[str, int] = {}  # {ticker: shares}
        
        equity_history = []
        
        for date in all_dates:
            # 获取当天的信号
            signals = {}
            for ticker, df in data.items():
                if date in df.index:
                    # 获取该日期之前的数据
                    hist = df.loc[:date]
                    if len(hist) > 50:  # 需要足够的历史数据
                        sig = strategy.generate_signals(hist)
                        if date in sig.index:
                            signals[ticker] = sig.loc[date]
            
            # 获取当天价格
            prices = {}
            for ticker, df in data.items():
                if date in df.index:
                    prices[ticker] = df.loc[date, 'Close']
            
            if not prices:
                continue
            
            # 当前持仓市值
            positions_value = sum(
                positions.get(t, 0) * prices.get(t, 0) 
                for t in positions
            )
            total_value = cash + positions_value
            
            # 执行交易
            for ticker, signal in signals.items():
                if ticker not in prices:
                    continue
                    
                price = prices[ticker]
                # 应用滑点和手续费
                buy_price = price * (1 + self.slippage + self.commission)
                sell_price = price * (1 - self.slippage - self.commission)
                
                target_value = total_value * self.position_size
                target_shares = int(target_value / buy_price)
                current_shares = positions.get(ticker, 0)
                
                # 买入信号
                if signal == Signal.BUY:
                    if current_shares == 0 and len(positions) < self.max_positions:
                        # 新建仓
                        shares_to_buy = target_shares
                        cost = shares_to_buy * buy_price
                        if cost <= cash:
                            cash -= cost
                            positions[ticker] = shares_to_buy
                            self.trades.append(PortfolioTrade(
                                date=date, ticker=ticker, action='BUY',
                                quantity=shares_to_buy, price=buy_price,
                                value=cost, commission=cost * self.commission
                            ))
                            
                # 卖出信号
                elif signal == Signal.SELL:
                    if current_shares > 0:
                        proceeds = current_shares * sell_price
                        cash += proceeds
                        self.trades.append(PortfolioTrade(
                            date=date, ticker=ticker, action='SELL',
                            quantity=current_shares, price=sell_price,
                            value=proceeds, commission=proceeds * self.commission
                        ))
                        del positions[ticker]
            
            # 记录权益
            positions_value = sum(
                positions.get(t, 0) * prices.get(t, 0) 
                for t in positions
            )
            equity_history.append({
                'date': date,
                'equity': cash + positions_value,
                'cash': cash,
                'positions_value': positions_value,
                'num_positions': len(positions)
            })
        
        # 构建权益曲线
        equity_df = pd.DataFrame(equity_history)
        equity_df.set_index('date', inplace=True)
        self.equity_curve = equity_df['equity']
        
        # 计算绩效指标
        return self._calculate_metrics(equity_df)
    
    def _calculate_metrics(self, equity_df: pd.DataFrame) -> Dict:
        """计算绩效指标"""
        equity = equity_df['equity']
        
        # 总收益率
        total_return = (equity.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 收益率序列
        returns = equity.pct_change().fillna(0)
        
        # 年化收益率
        days = len(equity)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 交易统计
        buys = [t for t in self.trades if t.action == 'BUY']
        sells = [t for t in self.trades if t.action == 'SELL']
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades),
            'total_buys': len(buys),
            'total_sells': len(sells),
            'equity_curve': equity_df,
            'trades': self.trades,
        }


def run_portfolio_backtest():
    """运行组合回测示例"""
    from src.data.mock import generate_multiple_stocks
    from src.trading.strategies import SMACrossover
    
    # 生成模拟数据
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    data = generate_multiple_stocks(tickers, start_date="2024-01-01")
    
    # 添加技术指标
    for ticker in data:
        data[ticker] = add_indicators(data[ticker])
    
    # 创建策略
    strategy = SMACrossover(20, 50)
    
    # 运行回测
    backtester = PortfolioBacktester(
        initial_capital=100000,
        max_positions=3,
        position_size=0.33,
    )
    
    result = backtester.run(data, strategy)
    
    print("=" * 60)
    print("📊 PORTFOLIO BACKTEST RESULTS")
    print("=" * 60)
    print(f"Strategy: {strategy.name}")
    print(f"Initial Capital: $100,000")
    print("-" * 60)
    print(f"Total Return: {result['total_return']:.2%}")
    print(f"Annual Return: {result['annual_return']:.2%}")
    print(f"Annual Volatility: {result['annual_volatility']:.2%}")
    print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Buys: {result['total_buys']}, Sells: {result['total_sells']}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    run_portfolio_backtest()
