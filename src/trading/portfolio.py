"""Trading portfolio management module."""

from typing import Dict, Optional
import numpy as np


class Portfolio:
    """Portfolio management class for tracking positions and value."""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize portfolio with starting capital.
        
        Args:
            initial_capital: Starting capital amount
        """
        self.initial_capital = initial_capital
        self.current_value = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.cash = initial_capital
        self.history = []
    
    def add_position(self, symbol: str, quantity: int, price: float) -> None:
        """
        Add a position to the portfolio.
        
        Args:
            symbol: Asset symbol/ticker
            quantity: Number of shares
            price: Purchase price per share
        """
        cost = quantity * price
        
        if cost > self.cash:
            raise ValueError(f"Insufficient cash. Need ${cost:.2f}, have ${self.cash:.2f}")
        
        if symbol in self.positions:
            self.positions[symbol]['quantity'] += quantity
            self.positions[symbol]['avg_price'] = (
                (self.positions[symbol]['avg_price'] * self.positions[symbol]['quantity'] + price * quantity) /
                (self.positions[symbol]['quantity'] + quantity)
            )
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_price': price,
                'entry_date': None  # Would track entry date in real implementation
            }
        
        self.cash -= cost
        self._update_value()
    
    def remove_position(self, symbol: str, quantity: int, price: float) -> None:
        """
        Remove/partially close a position.
        
        Args:
            symbol: Asset symbol/ticker
            quantity: Number of shares to sell
            price: Sell price per share
        """
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol}")
        
        if quantity > self.positions[symbol]['quantity']:
            raise ValueError(f"Cannot sell {quantity} shares; position has {self.positions[symbol]['quantity']}")
        
        proceeds = quantity * price
        self.positions[symbol]['quantity'] -= quantity
        self.cash += proceeds
        
        if self.positions[symbol]['quantity'] == 0:
            del self.positions[symbol]
        
        self._update_value()
    
    def _update_value(self) -> None:
        """Update current portfolio value."""
        self.current_value = self.cash
        for symbol, position in self.positions.items():
            # In real implementation, would use current market price
            self.current_value += position['quantity'] * position.get('current_price', position['avg_price'])
    
    def get_position_value(self, symbol: str) -> float:
        """Get current value of a specific position."""
        if symbol not in self.positions:
            return 0.0
        position = self.positions[symbol]
        return position['quantity'] * position.get('current_price', position['avg_price'])
    
    def get_weights(self) -> Dict[str, float]:
        """Get portfolio weights as a dictionary."""
        self._update_value()
        if self.current_value == 0:
            return {}
        return {
            symbol: position.get('current_price', position['avg_price']) * position['quantity'] / self.current_value
            for symbol, position in self.positions.items()
        }
    
    def __repr__(self) -> str:
        return f"Portfolio(capital={self.initial_capital}, value={self.current_value}, positions={len(self.positions)})"