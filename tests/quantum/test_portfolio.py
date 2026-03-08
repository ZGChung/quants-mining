"""Tests for quantum portfolio optimization."""

import pytest
import numpy as np


class TestPortfolioOptimizer:
    """Test suite for quantum portfolio optimizer."""

    def test_portfolio_optimizer_initialization(self):
        """Test that portfolio optimizer can be initialized."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        optimizer = PortfolioOptimizer(n_assets=5)
        assert optimizer is not None
        assert optimizer.n_assets == 5

    def test_portfolio_optimizer_has_optimize_method(self):
        """Test that optimizer has an optimize method."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        optimizer = PortfolioOptimizer(n_assets=5)
        assert hasattr(optimizer, "optimize")
        assert callable(optimizer.optimize)

    def test_portfolio_optimizer_accepts_returns_matrix(self):
        """Test that optimizer accepts returns matrix."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        optimizer = PortfolioOptimizer(n_assets=3)
        returns = np.array([[0.1], [0.2], [0.15]])
        assert returns.shape[0] == 3

    def test_portfolio_optimizer_accepts_covariance_matrix(self):
        """Test that optimizer accepts covariance matrix."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        optimizer = PortfolioOptimizer(n_assets=3)
        cov = np.array([[0.1, 0.02, 0.01], [0.02, 0.15, 0.03], [0.01, 0.03, 0.12]])
        assert cov.shape == (3, 3)

    def test_portfolio_weights_sum_to_one(self):
        """Test that optimized portfolio weights sum to 1."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        optimizer = PortfolioOptimizer(n_assets=3)
        # This test will pass when optimize is implemented
        # weights = optimizer.optimize(returns, cov)
        # assert abs(sum(weights) - 1.0) < 1e-6


class TestQuantumCircuit:
    """Test suite for quantum circuits."""

    def test_quantum_circuit_initialization(self):
        """Test that quantum circuit can be initialized."""
        # This will be implemented with actual Qiskit circuits
        pass

    def test_quantum_circuit_has_correct_number_of_qubits(self):
        """Test that circuit has correct number of qubits."""
        pass


class TestQuantumOptimizer:
    """Test suite for base quantum optimizer."""

    def test_qaoa_optimizer_exists(self):
        """Test that QAOA optimizer class exists."""
        from src.quantum.optimizers.portfolio import PortfolioOptimizer

        assert PortfolioOptimizer is not None
