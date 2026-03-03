"""
纸交易模拟器
模拟真实交易但不执行真实订单
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PaperOrder:
    """模拟订单"""
    timestamp: datetime
    ticker: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    signal_reason: str = ""


class PaperTrader:
    """纸交易模拟器"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.cash = initial_capital
        self.positions: Dict[str, int] = {}  # {ticker: shares}
        self.orders: List[PaperOrder] = []
        self.portfolio_history: List[Dict] = []
    
    @property
    def portfolio_value(self, prices: Dict[str, float]) -> float:
        """组合市值"""
        positions_value = sum(
            self.positions.get(t, 0) * prices.get(t, 0)
            for t in self.positions
        )
        return self.cash + positions_value
    
    def can_buy(self, ticker: str, quantity: int, price: float) -> bool:
        """检查是否可以买入"""
        cost = quantity * price * (1 + self.slippage + self.commission)
        return self.cash >= cost
    
    def can_sell(self, ticker: str, quantity: int) -> bool:
        """检查是否可以卖出"""
        return self.positions.get(ticker, 0) >= quantity
    
    def buy(
        self,
        ticker: str,
        quantity: int,
        price: float,
        signal_reason: str = ""
    ) -> bool:
        """买入"""
        cost = quantity * price * (1 + self.slippage + self.commission)
        
        if not self.can_buy(ticker, quantity, price):
            logger.warning(f"Cannot buy {ticker}: insufficient funds")
            return False
        
        self.cash -= cost
        self.positions[ticker] = self.positions.get(ticker, 0) + quantity
        
        self.orders.append(PaperOrder(
            timestamp=datetime.now(),
            ticker=ticker,
            action='BUY',
            quantity=quantity,
            price=price * (1 + self.slippage),
            signal_reason=signal_reason
        ))
        
        logger.info(f"BUY {quantity} {ticker} @ ${price:.2f}")
        return True
    
    def sell(
        self,
        ticker: str,
        quantity: int,
        price: float,
        signal_reason: str = ""
    ) -> bool:
        """卖出"""
        if not self.can_sell(ticker, quantity):
            logger.warning(f"Cannot sell {ticker}: insufficient shares")
            return False
        
        proceeds = quantity * price * (1 - self.slippage - self.commission)
        self.cash += proceeds
        self.positions[ticker] -= quantity
        
        if self.positions[ticker] == 0:
            del self.positions[ticker]
        
        self.orders.append(PaperOrder(
            timestamp=datetime.now(),
            ticker=ticker,
            action='SELL',
            quantity=quantity,
            price=price * (1 - self.slippage),
            signal_reason=signal_reason
        ))
        
        logger.info(f"SELL {quantity} {ticker} @ ${price:.2f}")
        return True
    
    def record_state(self, prices: Dict[str, float]):
        """记录当前状态"""
        self.portfolio_history.append({
            'timestamp': datetime.now(),
            'cash': self.cash,
            'positions_value': sum(
                self.positions.get(t, 0) * prices.get(t, 0)
                for t in self.positions
            ),
            'portfolio_value': self.portfolio_value(prices),
            'positions': dict(self.positions),
        })
    
    def get_summary(self) -> Dict:
        """获取摘要"""
        return {
            'initial_capital': self.initial_capital,
            'current_cash': self.cash,
            'total_orders': len(self.orders),
            'total_buys': len([o for o in self.orders if o.action == 'BUY']),
            'total_sells': len([o for o in self.orders if o.action == 'SELL']),
        }
    
    def get_orders_df(self) -> pd.DataFrame:
        """获取订单 DataFrame"""
        if not self.orders:
            return pd.DataFrame()
        
        data = []
        for o in self.orders:
            data.append({
                'timestamp': o.timestamp,
                'ticker': o.ticker,
                'action': o.action,
                'quantity': o.quantity,
                'price': o.price,
                'value': o.quantity * o.price,
                'reason': o.signal_reason,
            })
        
        return pd.DataFrame(data)


class LivePaperTrader(PaperTrader):
    """实时纸交易 - 连接数据源"""
    
    def __init__(
        self,
        data_source,
        strategy,
        initial_capital: float = 100000.0,
        max_positions: int = 3,
        **kwargs
    ):
        super().__init__(initial_capital=initial_capital, **kwargs)
        
        self.data_source = data_source
        self.strategy = strategy
        self.max_positions = max_positions
        
        self.current_data: Dict[str, pd.DataFrame] = {}
    
    def update_data(self, tickers: List[str], period: str = "1d"):
        """更新数据"""
        for ticker in tickers:
            df = self.data_source.fetch(ticker, period=period)
            if not df.empty:
                self.current_data[ticker] = df
    
    def run_signals(self, ticker: str) -> int:
        """运行策略获取信号"""
        if ticker not in self.current_data:
            return 0
        
        df = self.current_data[ticker]
        signals = self.strategy.generate_signals(df)
        
        if signals.empty:
            return 0
        
        return signals.iloc[-1]
    
    def step(self, ticker: str, current_price: float) -> bool:
        """单步执行"""
        signal = self.run_signals(ticker)
        
        if signal == 1:  # BUY
            target_value = self.portfolio_value({ticker: current_price}) / self.max_positions
            shares = int(target_value / (current_price * (1 + self.slippage)))
            
            if shares > 0:
                return self.buy(ticker, shares, current_price, f"Signal: {signal}")
        
        elif signal == -1:  # SELL
            if ticker in self.positions:
                return self.sell(ticker, self.positions[ticker], current_price, f"Signal: {signal}")
        
        return False


if __name__ == "__main__":
    from src.data.mock import generate_mock_data
    from src.data import add_indicators
    from src.trading.strategies import SMACrossover
    
    # 准备数据
    data = generate_mock_data("AAPL", start_date="2024-01-01")
    data = add_indicators(data)
    
    # 创建策略
    strategy = SMACrossover(20, 50)
    
    # 创建纸交易器
    trader = PaperTrader(initial_capital=100000)
    
    # 模拟交易
    for i in range(50, len(data)):
        price = data['Close'].iloc[i]
        
        signal = strategy.generate_signals(data.iloc[:i+1]).iloc[-1]
        
        if signal == 1 and 'AAPL' not in trader.positions:
            trader.buy('AAPL', 100, price, "SMA Crossover")
        elif signal == -1 and 'AAPL' in trader.positions:
            trader.sell('AAPL', trader.positions['AAPL'], price, "SMA Crossover")
    
    # 打印结果
    print("\n📊 Paper Trading Results:")
    print(f"Initial: ${trader.initial_capital:,.2f}")
    print(f"Final Cash: ${trader.cash:,.2f}")
    print(f"Orders: {len(trader.orders)}")
