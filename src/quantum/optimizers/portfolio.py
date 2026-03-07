"""
Portfolio optimization using classical and quantum methods.

Implements:
- ClassicalPortfolioOptimizer: Markowitz mean-variance via scipy
- QuantumPortfolioOptimizer: QAOA-based binary portfolio selection
- PortfolioOptimizer: Unified interface routing to either method

Background:
    Markowitz (1952) formulated portfolio selection as:
        min   w^T Sigma w       (minimize risk)
        s.t.  mu^T w >= target  (minimum return)
              sum(w) = 1        (fully invested)
              w >= 0            (long only)

    The quantum approach reformulates this as a QUBO problem
    on binary variables (include asset or not), solved via QAOA.
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
from scipy.optimize import minimize
import logging

logger = logging.getLogger(__name__)

try:
    from qiskit import QuantumCircuit
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class ClassicalPortfolioOptimizer:
    """
    Markowitz mean-variance portfolio optimizer.

    Finds optimal weights on the efficient frontier by minimizing
    portfolio variance for a given target return, or by maximizing
    the Sharpe ratio (return / volatility).
    """

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def optimize(self, expected_returns: np.ndarray,
                 covariance: np.ndarray,
                 target_return: Optional[float] = None) -> np.ndarray:
        """
        Find optimal portfolio weights.

        If target_return is None, maximizes the Sharpe ratio.
        Otherwise, minimizes variance subject to the target return.
        """
        n = len(expected_returns)

        if target_return is None:
            return self._max_sharpe(expected_returns, covariance)

        def portfolio_variance(w):
            return w @ covariance @ w

        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            {'type': 'ineq', 'fun': lambda w: expected_returns @ w - target_return},
        ]
        bounds = [(0, 1)] * n
        x0 = np.ones(n) / n

        result = minimize(portfolio_variance, x0, method='SLSQP',
                          bounds=bounds, constraints=constraints)

        return result.x if result.success else np.ones(n) / n

    def _max_sharpe(self, expected_returns: np.ndarray,
                    covariance: np.ndarray) -> np.ndarray:
        """Maximize Sharpe ratio: (return - rf) / volatility."""
        n = len(expected_returns)

        def neg_sharpe(w):
            port_return = expected_returns @ w
            port_vol = np.sqrt(w @ covariance @ w)
            if port_vol < 1e-10:
                return 0
            return -(port_return - self.risk_free_rate) / port_vol

        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        bounds = [(0, 1)] * n
        x0 = np.ones(n) / n

        result = minimize(neg_sharpe, x0, method='SLSQP',
                          bounds=bounds, constraints=constraints)

        return result.x if result.success else np.ones(n) / n

    def efficient_frontier(self, expected_returns: np.ndarray,
                           covariance: np.ndarray,
                           n_points: int = 50) -> Dict:
        """
        Compute the efficient frontier.

        Returns dict with 'returns', 'volatilities', 'weights' arrays.
        """
        min_ret = expected_returns.min()
        max_ret = expected_returns.max()
        target_returns = np.linspace(min_ret, max_ret, n_points)

        frontier_returns = []
        frontier_vols = []
        frontier_weights = []

        for target in target_returns:
            w = self.optimize(expected_returns, covariance, target_return=target)
            port_return = expected_returns @ w
            port_vol = np.sqrt(w @ covariance @ w)
            frontier_returns.append(port_return)
            frontier_vols.append(port_vol)
            frontier_weights.append(w)

        return {
            'returns': np.array(frontier_returns),
            'volatilities': np.array(frontier_vols),
            'weights': np.array(frontier_weights),
        }


class QuantumPortfolioOptimizer:
    """
    QAOA-based portfolio optimizer for binary asset selection.

    Solves: which assets to include in the portfolio?
    Then allocates equal weight among selected assets.
    """

    def __init__(self, risk_factor: float = 0.5, qaoa_depth: int = 1):
        self.risk_factor = risk_factor
        self.qaoa_depth = qaoa_depth

    def optimize(self, expected_returns: np.ndarray,
                 covariance: np.ndarray) -> np.ndarray:
        """
        Select assets and return weights.

        Uses QAOA circuit (classical simulation) to find optimal
        binary selection, then assigns equal weight to selected assets.
        """
        from src.quantum.circuits import QAOACircuit

        circuit = QAOACircuit(
            expected_returns, covariance,
            risk_factor=self.risk_factor, p=self.qaoa_depth
        )
        selection, cost = circuit.solve()

        n_selected = int(selection.sum())
        if n_selected == 0:
            return np.ones(len(expected_returns)) / len(expected_returns)

        weights = selection / n_selected
        return weights

    def optimize_with_details(self, expected_returns: np.ndarray,
                               covariance: np.ndarray) -> Dict:
        """Return optimization result with details."""
        from src.quantum.circuits import QAOACircuit

        circuit = QAOACircuit(
            expected_returns, covariance,
            risk_factor=self.risk_factor, p=self.qaoa_depth
        )
        selection, cost = circuit.solve()

        n_selected = int(selection.sum())
        weights = selection / n_selected if n_selected > 0 else np.ones(len(expected_returns)) / len(expected_returns)

        port_return = expected_returns @ weights
        port_risk = np.sqrt(weights @ covariance @ weights)

        return {
            'weights': weights,
            'selection': selection,
            'n_selected': n_selected,
            'cost': cost,
            'expected_return': port_return,
            'risk': port_risk,
            'method': 'qaoa_classical_simulation',
        }


class PortfolioOptimizer:
    """
    Unified portfolio optimizer interface.

    Routes to classical (Markowitz) or quantum (QAOA) method.
    """

    def __init__(self, n_assets: int, method: str = "classical",
                 risk_factor: float = 0.5):
        self.n_assets = n_assets
        self.method = method
        self.risk_factor = risk_factor

        if method == "classical":
            self._optimizer = ClassicalPortfolioOptimizer()
        elif method == "quantum":
            self._optimizer = QuantumPortfolioOptimizer(risk_factor=risk_factor)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'classical' or 'quantum'.")

    def optimize(self, returns: np.ndarray, covariance: np.ndarray) -> np.ndarray:
        """Optimize portfolio weights."""
        return self._optimizer.optimize(returns, covariance)
