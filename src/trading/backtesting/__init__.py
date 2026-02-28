"""
Backtesting Module

Provides backtesting functionality for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .strategies import BaseStrategy


class Backtester:
    """
    Simple backtesting engine for trading strategies
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission: float = 0.001,
                 slippage: float = 0.0005):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade
            slippage: Slippage rate
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.results = None
        
    def run(self, 
            data: pd.DataFrame, 
            strategy: BaseStrategy,
            position_size: float = 1.0) -> Dict[str, Any]:
        """
        Run backtest
        
        Args:
            data: Market data with OHLCV
            strategy: Trading strategy
            position_size: Position size as fraction of capital
            
        Returns:
            Dictionary with backtest results
        """
        # Generate signals
        signals = strategy.generate_signals(data)
        
        # Initialize tracking variables
        capital = self.initial_capital
        position = 0  # 0: no position, 1: long, -1: short
        entry_price = 0
        
        trades = []
        portfolio_values = []
        
        for i in range(len(signals)):
            if pd.isna(signals.iloc[i]['price']):
                continue
                
            price = signals.iloc[i]['price']
            signal = signals.iloc[i].get('signal', 0)
            
            # Calculate current portfolio value
            if position != 0:
                if position == 1:
                    pnl = (price - entry_price) * (capital * position_size) / entry_price
                else:
                    pnl = (entry_price - price) * (capital * position_size) / entry_price
                current_value = capital + pnl
            else:
                current_value = capital
                
            portfolio_values.append(current_value)
            
            # Execute trades based on signals
            if signal == 1 and position == 0:  # Buy signal, no position
                # Apply slippage for buy
                buy_price = price * (1 + self.slippage)
                cost = capital * position_size * self.commission
                capital -= cost
                position = 1
                entry_price = buy_price
                trades.append({
                    'date': signals.index[i],
                    'type': 'BUY',
                    'price': buy_price,
                    'cost': cost
                })
                
            elif signal == -1 and position == 1:  # Sell signal, have long position
                # Apply slippage for sell
                sell_price = price * (1 - self.slippage)
                pnl = (sell_price - entry_price) * (capital * position_size) / entry_price
                capital += (capital * position_size) + pnl
                cost = capital * position_size * self.commission
                capital -= cost
                trades.append({
                    'date': signals.index[i],
                    'type': 'SELL',
                    'price': sell_price,
                    'pnl': pnl,
                    'cost': cost
                })
                position = 0
                entry_price = 0
                
        # Close any remaining position
        if position != 0:
            final_price = signals.iloc[-1]['price']
            if position == 1:
                pnl = (final_price - entry_price) * (capital * position_size) / entry_price
            else:
                pnl = (entry_price - final_price) * (capital * position_size) / entry_price
            capital += pnl
            
        # Calculate metrics
        portfolio_values = pd.Series(portfolio_values, index=signals.index[:len(portfolio_values)])
        returns = portfolio_values.pct_change().dropna()
        
        results = {
            'final_value': capital,
            'total_return': (capital - self.initial_capital) / self.initial_capital,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'returns': returns,
            'sharpe_ratio': self._sharpe_ratio(returns),
            'max_drawdown': self._max_drawdown(portfolio_values),
            'win_rate': self._win_rate(trades)
        }
        
        self.results = results
        return results
    
    def _sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def _max_drawdown(self, portfolio_values: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(portfolio_values) == 0:
            return 0.0
        cummax = portfolio_values.cummax()
        drawdown = (portfolio_values - cummax) / cummax
        return drawdown.min()
    
    def _win_rate(self, trades: list) -> float:
        """Calculate win rate"""
        if len(trades) == 0:
            return 0.0
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return winning_trades / len(trades)
    
    def print_summary(self):
        """Print backtest summary"""
        if self.results is None:
            print("No backtest results. Run backtest first.")
            return
            
        print("\n" + "="*50)
        print("BACKTEST SUMMARY")
        print("="*50)
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Value: ${self.results['final_value']:,.2f}")
        print(f"Total Return: {self.results['total_return']*100:.2f}%")
        print(f"Sharpe Ratio: {self.results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {self.results['max_drawdown']*100:.2f}%")
        print(f"Win Rate: {self.results['win_rate']*100:.1f}%")
        print(f"Total Trades: {len(self.results['trades'])}")
        print("="*50 + "\n")
