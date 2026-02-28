"""
投资组合管理模块
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓"""
    ticker: str
    quantity: int
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class Portfolio:
    """投资组合管理器"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.history: List[Dict] = []  # 记录每次调仓
        
    @property
    def total_value(self) -> float:
        """总资产"""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def positions_value(self) -> float:
        """持仓市值"""
        return sum(p.market_value for p in self.positions.values())
    
    def buy(
        self, 
        ticker: str, 
        quantity: int, 
        price: float,
        commission: float = 0.001
    ) -> bool:
        """
        买入
        
        Args:
            ticker: 股票代码
            quantity: 数量
            price: 价格
            commission: 手续费率
            
        Returns:
            是否成功
        """
        cost = quantity * price * (1 + commission)
        
        if cost > self.cash:
            logger.warning(f"Insufficient cash: need {cost}, have {self.cash}")
            return False
        
        self.cash -= cost
        
        if ticker in self.positions:
            # 加仓
            pos = self.positions[ticker]
            total_quantity = pos.quantity + quantity
            avg_price = (pos.quantity * pos.entry_price + quantity * price) / total_quantity
            pos.quantity = total_quantity
            pos.entry_price = avg_price
        else:
            # 新建持仓
            self.positions[ticker] = Position(
                ticker=ticker,
                quantity=quantity,
                entry_price=price,
                current_price=price,
                market_value=quantity * price,
                unrealized_pnl=0,
                unrealized_pnl_pct=0
            )
        
        self._record_action('BUY', ticker, quantity, price)
        return True
    
    def sell(
        self, 
        ticker: str, 
        quantity: int, 
        price: float,
        commission: float = 0.001
    ) -> bool:
        """
        卖出
        
        Args:
            ticker: 股票代码
            quantity: 数量
            price: 价格
            commission: 手续费率
            
        Returns:
            是否成功
        """
        if ticker not in self.positions:
            logger.warning(f"No position for {ticker}")
            return False
        
        pos = self.positions[ticker]
        
        if quantity > pos.quantity:
            logger.warning(f"Cannot sell more than held: {pos.quantity}")
            quantity = pos.quantity
        
        proceeds = quantity * price * (1 - commission)
        self.cash += proceeds
        
        pos.quantity -= quantity
        
        if pos.quantity == 0:
            del self.positions[ticker]
        
        self._record_action('SELL', ticker, quantity, price)
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """
        更新持仓价格
        
        Args:
            prices: 股票价格字典
        """
        for ticker, price in prices.items():
            if ticker in self.positions:
                pos = self.positions[ticker]
                pos.current_price = price
                pos.market_value = pos.quantity * price
                pos.unrealized_pnl = (price - pos.entry_price) * pos.quantity
                pos.unrealized_pnl_pct = (price - pos.entry_price) / pos.entry_price
    
    def get_positions_df(self) -> pd.DataFrame:
        """获取持仓 DataFrame"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for pos in self.positions.values():
            data.append({
                'ticker': pos.ticker,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl_pct,
            })
        
        return pd.DataFrame(data)
    
    def _record_action(self, action: str, ticker: str, quantity: int, price: float):
        """记录操作"""
        self.history.append({
            'action': action,
            'ticker': ticker,
            'quantity': quantity,
            'price': price,
            'total_value': self.total_value,
            'cash': self.cash,
        })
    
    def summary(self) -> Dict:
        """投资组合摘要"""
        return {
            'initial_capital': self.initial_capital,
            'current_value': self.total_value,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'total_return': (self.total_value - self.initial_capital) / self.initial_capital,
            'num_positions': len(self.positions),
        }


class Rebalancer:
    """仓位再平衡器"""
    
    @staticmethod
    def equal_weight(
        portfolio: Portfolio,
        target_prices: Dict[str, float],
        max_positions: int = 10,
        commission: float = 0.001
    ):
        """
        等权重再平衡
        
        Args:
            portfolio: 投资组合
            target_prices: 目标股票价格
            max_positions: 最大持仓数量
            commission: 手续费率
        """
        # 先更新价格
        portfolio.update_prices(target_prices)
        
        # 计算每个仓位的目标价值
        target_value = portfolio.total_value / min(max_positions, len(target_prices))
        
        # 需要持有的股票
        target_tickers = set(target_prices.keys())
        current_tickers = set(portfolio.positions.keys())
        
        # 卖出不在目标中的持仓
        for ticker in current_tickers - target_tickers:
            if ticker in portfolio.positions:
                pos = portfolio.positions[ticker]
                portfolio.sell(ticker, pos.quantity, target_prices.get(ticker, pos.current_price), commission)
        
        # 买入或调仓
        for ticker in target_tickers:
            price = target_prices[ticker]
            
            if ticker in portfolio.positions:
                # 调整现有持仓
                pos = portfolio.positions[ticker]
                target_shares = int(target_value / price)
                diff = target_shares - pos.quantity
                
                if diff > 0:
                    portfolio.buy(ticker, diff, price, commission)
                elif diff < 0:
                    portfolio.sell(ticker, -diff, price, commission)
            else:
                # 新建持仓
                shares = int(target_value / price)
                if shares > 0:
                    portfolio.buy(ticker, shares, price, commission)


if __name__ == "__main__":
    # 测试
    portfolio = Portfolio(100000)
    
    # 买入
    portfolio.buy("AAPL", 100, 150.0)
    portfolio.buy("MSFT", 50, 300.0)
    
    # 更新价格
    portfolio.update_prices({"AAPL": 160.0, "MSFT": 310.0})
    
    print("Portfolio Summary:")
    for key, value in portfolio.summary().items():
        print(f"  {key}: {value}")
    
    print("\nPositions:")
    print(portfolio.get_positions_df())
