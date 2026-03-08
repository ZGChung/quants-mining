"""
Quantum circuits for portfolio optimization.

Implements QAOA and variational ansatz circuits for solving combinatorial
portfolio selection problems. Classical numpy simulation is the default;
Qiskit integration is optional.

Background:
    Portfolio selection can be cast as a Quadratic Unconstrained Binary
    Optimization (QUBO) problem: for n assets, choose a binary vector
    x in {0,1}^n that maximizes expected return minus risk:

        min  x^T Sigma x  -  mu^T x

    where mu = expected returns, Sigma = covariance matrix scaled by
    a risk aversion factor.

    QAOA encodes this into a quantum circuit with alternating cost and
    mixer layers, parameterized by angles (gamma, beta).
"""

import numpy as np
from typing import Optional, Tuple, List
from itertools import product

try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter

    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class QAOACircuit:
    """
    QAOA circuit for binary portfolio selection.

    The cost Hamiltonian is:
        C = sum_i mu_i Z_i  -  risk * sum_{ij} Sigma_{ij} Z_i Z_j

    The mixer is the standard transverse field:
        B = sum_i X_i

    For classical simulation, we evaluate C(x) over all 2^n bitstrings
    directly (exact for small n <= 20).
    """

    def __init__(
        self,
        expected_returns: np.ndarray,
        covariance: np.ndarray,
        risk_factor: float = 0.5,
        p: int = 1,
    ):
        self.mu = np.asarray(expected_returns, dtype=float)
        self.sigma = np.asarray(covariance, dtype=float)
        self.risk_factor = risk_factor
        self.n_assets = len(self.mu)
        self.p = p  # QAOA depth (number of layers)

    def cost_function(self, x: np.ndarray) -> float:
        """Evaluate the QUBO cost for a binary vector x."""
        return float(self.risk_factor * x @ self.sigma @ x - self.mu @ x)

    def solve_classical(self) -> Tuple[np.ndarray, float]:
        """
        Brute-force solve by evaluating all 2^n bitstrings.
        Only practical for n <= 20.
        """
        n = self.n_assets
        best_x = np.zeros(n)
        best_cost = float("inf")

        for bits in product([0, 1], repeat=n):
            x = np.array(bits, dtype=float)
            if x.sum() == 0:
                continue
            cost = self.cost_function(x)
            if cost < best_cost:
                best_cost = cost
                best_x = x.copy()

        return best_x, best_cost

    def build_qiskit_circuit(
        self, gammas: Optional[List[float]] = None, betas: Optional[List[float]] = None
    ) -> "QuantumCircuit":
        """
        Build a Qiskit QuantumCircuit implementing QAOA.

        Args:
            gammas: Cost layer angles (length p). If None, uses Parameters.
            betas: Mixer layer angles (length p). If None, uses Parameters.

        Returns:
            Qiskit QuantumCircuit
        """
        if not HAS_QISKIT:
            raise ImportError("Qiskit required. Install with: pip install qiskit")

        n = self.n_assets
        qc = QuantumCircuit(n, n)

        # Initial superposition
        for i in range(n):
            qc.h(i)

        for layer in range(self.p):
            gamma = gammas[layer] if gammas else Parameter(f"gamma_{layer}")
            beta = betas[layer] if betas else Parameter(f"beta_{layer}")

            # Cost layer: ZZ interactions from covariance
            for i in range(n):
                for j in range(i + 1, n):
                    weight = self.risk_factor * self.sigma[i, j]
                    if abs(weight) > 1e-10:
                        qc.cx(i, j)
                        qc.rz(2 * gamma * weight, j)
                        qc.cx(i, j)

            # Cost layer: Z rotations from returns
            for i in range(n):
                angle = gamma * (self.risk_factor * self.sigma[i, i] - self.mu[i])
                qc.rz(2 * angle, i)

            # Mixer layer: X rotations
            for i in range(n):
                qc.rx(2 * beta, i)

        qc.measure(range(n), range(n))
        return qc

    def solve(self) -> Tuple[np.ndarray, float]:
        """Solve using classical brute-force (default)."""
        return self.solve_classical()


class VariationalAnsatz:
    """
    Parameterized variational circuit for continuous portfolio weight
    optimization using Ry rotations and CNOT entanglement.

    The circuit maps n_params parameters to n_assets qubit states.
    Measurement probabilities are interpreted as portfolio weights.

    Classical simulation computes the state vector directly using
    rotation and CNOT matrix operations.
    """

    def __init__(self, n_assets: int, n_layers: int = 2):
        self.n_assets = n_assets
        self.n_layers = n_layers
        self.n_params = n_assets * n_layers

    def _ry_matrix(self, theta: float) -> np.ndarray:
        """Single-qubit Ry rotation matrix."""
        c, s = np.cos(theta / 2), np.sin(theta / 2)
        return np.array([[c, -s], [s, c]])

    def simulate(self, params: np.ndarray) -> np.ndarray:
        """
        Classical simulation of the variational circuit.

        Args:
            params: Array of rotation angles (length n_params)

        Returns:
            Portfolio weights derived from measurement probabilities
        """
        n = self.n_assets
        dim = 2**n
        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0  # |00...0>

        # Apply Hadamard to create equal superposition
        h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        gate = h
        for _ in range(n - 1):
            gate = np.kron(gate, h)
        state = gate @ state

        param_idx = 0
        for layer in range(self.n_layers):
            # Ry rotations on each qubit
            for qubit in range(n):
                theta = params[param_idx]
                param_idx += 1

                ry = self._ry_matrix(theta)
                # Build full operator: I x ... x Ry x ... x I
                if qubit == 0:
                    op = ry
                else:
                    op = np.eye(2)
                for q in range(1, n):
                    op = np.kron(op, ry if q == qubit else np.eye(2))
                state = op @ state

            # CNOT entanglement: linear chain
            for q in range(n - 1):
                cnot = np.eye(dim)
                for idx in range(dim):
                    bits = list(format(idx, f"0{n}b"))
                    if bits[q] == "1":
                        bits[q + 1] = "0" if bits[q + 1] == "1" else "1"
                        target = int("".join(bits), 2)
                        cnot[idx, idx] = 0
                        cnot[idx, target] = 1
                        cnot[target, target] = 0
                        cnot[target, idx] = 1
                state = cnot @ state

        # Measurement probabilities -> weights
        probs = np.abs(state) ** 2

        # Extract per-qubit marginal probabilities as weights
        weights = np.zeros(n)
        for idx in range(dim):
            bits = format(idx, f"0{n}b")
            for q in range(n):
                if bits[q] == "1":
                    weights[q] += probs[idx]

        # Normalize to sum to 1
        total = weights.sum()
        if total > 0:
            weights /= total
        else:
            weights = np.ones(n) / n

        return weights

    def optimize_weights(
        self, expected_returns: np.ndarray, covariance: np.ndarray, risk_factor: float = 0.5
    ) -> np.ndarray:
        """
        Optimize circuit parameters to find portfolio weights that
        minimize risk-adjusted cost.
        """
        from scipy.optimize import minimize

        def objective(params):
            w = self.simulate(params)
            portfolio_risk = w @ covariance @ w
            portfolio_return = expected_returns @ w
            return risk_factor * portfolio_risk - portfolio_return

        x0 = np.random.randn(self.n_params) * 0.1
        result = minimize(objective, x0, method="COBYLA", options={"maxiter": 500})
        return self.simulate(result.x)
