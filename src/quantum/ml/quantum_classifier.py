"""
Quantum machine learning for financial signal classification.

Implements a variational quantum classifier (VQC) that encodes financial
features (returns, volatility, RSI) into quantum states and trains a
parameterized circuit to predict BUY/SELL signals.

Background:
    Quantum kernel methods map classical data into a high-dimensional
    Hilbert space via a feature map, then apply trainable rotations
    to classify. The expressiveness comes from entanglement creating
    correlations that are hard to represent classically.

    Feature encoding: angle encoding (Ry rotations proportional to
    feature values) + ZZ entanglement for feature interactions.

    Classifier: trainable Ry layer + measurement of first qubit.
    P(|1>) > 0.5 => BUY, else SELL.

All simulation is done classically via numpy state vector evolution.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Optional
from scipy.optimize import minimize
import logging

logger = logging.getLogger(__name__)


class QuantumFeatureMap:
    """
    Encodes classical feature vectors into quantum states.

    For n features, uses n qubits with:
    1. Ry(feature_i) rotation on qubit i (angle encoding)
    2. RZZ(feature_i * feature_j) on pairs (i,j) for entanglement

    This creates a quantum kernel that captures both individual
    feature magnitudes and pairwise interactions.
    """

    def __init__(self, n_features: int, reps: int = 1):
        self.n_features = n_features
        self.n_qubits = n_features
        self.reps = reps
        self.dim = 2**n_features

    def _ry(self, theta: float) -> np.ndarray:
        c, s = np.cos(theta / 2), np.sin(theta / 2)
        return np.array([[c, -s], [s, c]])

    def _rz(self, theta: float) -> np.ndarray:
        return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]])

    def _apply_single_gate(self, state: np.ndarray, gate: np.ndarray, qubit: int) -> np.ndarray:
        """Apply single-qubit gate to state vector."""
        n = self.n_qubits
        if qubit == 0:
            op = gate
        else:
            op = np.eye(2)
        for q in range(1, n):
            op = np.kron(op, gate if q == qubit else np.eye(2))
        return op @ state

    def _apply_zz(self, state: np.ndarray, theta: float, q1: int, q2: int) -> np.ndarray:
        """Apply RZZ gate: exp(-i * theta/2 * Z_q1 Z_q2)."""
        n = self.n_qubits
        dim = self.dim
        new_state = np.zeros(dim, dtype=complex)
        for idx in range(dim):
            bits = format(idx, f"0{n}b")
            z1 = 1 - 2 * int(bits[q1])
            z2 = 1 - 2 * int(bits[q2])
            phase = np.exp(-1j * theta / 2 * z1 * z2)
            new_state[idx] = phase * state[idx]
        return new_state

    def encode(self, features: np.ndarray) -> np.ndarray:
        """
        Encode a feature vector into a quantum state.

        Args:
            features: Array of shape (n_features,)

        Returns:
            State vector of shape (2^n_features,)
        """
        state = np.zeros(self.dim, dtype=complex)
        state[0] = 1.0

        # Hadamard
        h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        for q in range(self.n_qubits):
            state = self._apply_single_gate(state, h, q)

        for _ in range(self.reps):
            # Angle encoding: Ry(pi * feature_i)
            for q in range(self.n_qubits):
                angle = np.pi * np.clip(features[q], -1, 1)
                state = self._apply_single_gate(state, self._ry(angle), q)

            # Entanglement: RZZ(feature_i * feature_j)
            for q1 in range(self.n_qubits):
                for q2 in range(q1 + 1, self.n_qubits):
                    angle = np.pi * features[q1] * features[q2]
                    state = self._apply_zz(state, angle, q1, q2)

        return state


class QuantumClassifier:
    """
    Variational quantum classifier for BUY/SELL prediction.

    Architecture:
        1. QuantumFeatureMap encodes input features
        2. Trainable Ry rotation layer (one angle per qubit per layer)
        3. CNOT entanglement between adjacent qubits
        4. Measure qubit 0: P(|1>) > 0.5 => class 1 (BUY)

    Trained via classical optimization of cross-entropy loss.
    """

    def __init__(self, n_features: int, n_layers: int = 2):
        self.n_features = n_features
        self.n_qubits = n_features
        self.n_layers = n_layers
        self.feature_map = QuantumFeatureMap(n_features)
        self.n_params = n_features * n_layers
        self.params = np.random.randn(self.n_params) * 0.1
        self.trained = False

    def _apply_variational_layer(self, state: np.ndarray, layer_params: np.ndarray) -> np.ndarray:
        """Apply one layer of trainable rotations + entanglement."""
        n = self.n_qubits
        dim = 2**n

        # Ry rotations
        for q in range(n):
            ry = self.feature_map._ry(layer_params[q])
            state = self.feature_map._apply_single_gate(state, ry, q)

        # CNOT chain
        for q in range(n - 1):
            new_state = np.zeros(dim, dtype=complex)
            for idx in range(dim):
                bits = list(format(idx, f"0{n}b"))
                if bits[q] == "1":
                    bits[q + 1] = "0" if bits[q + 1] == "1" else "1"
                target = int("".join(bits), 2)
                new_state[target] += state[idx]
            state = new_state

        return state

    def predict_proba(self, features: np.ndarray, params: Optional[np.ndarray] = None) -> float:
        """
        Predict P(class=1) for a single feature vector.

        Returns probability of BUY signal.
        """
        if params is None:
            params = self.params

        state = self.feature_map.encode(features)

        for layer in range(self.n_layers):
            start = layer * self.n_qubits
            layer_params = params[start : start + self.n_qubits]
            state = self._apply_variational_layer(state, layer_params)

        # P(qubit 0 = |1>) = sum of |amp|^2 where first bit is 1
        n = self.n_qubits
        prob_one = 0.0
        for idx in range(2**n):
            if format(idx, f"0{n}b")[0] == "1":
                prob_one += abs(state[idx]) ** 2

        return float(prob_one)

    def predict(self, features: np.ndarray) -> int:
        """Predict class: 1 (BUY) or -1 (SELL)."""
        return 1 if self.predict_proba(features) > 0.5 else -1

    def fit(self, X: np.ndarray, y: np.ndarray, max_iter: int = 200) -> dict:
        """
        Train the classifier.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels, 1 for BUY, 0 for SELL
            max_iter: Maximum optimization iterations

        Returns:
            Training info dict
        """

        def loss(params):
            total = 0.0
            for i in range(len(X)):
                p = np.clip(self.predict_proba(X[i], params), 1e-7, 1 - 1e-7)
                total -= y[i] * np.log(p) + (1 - y[i]) * np.log(1 - p)
            return total / len(X)

        result = minimize(loss, self.params, method="COBYLA", options={"maxiter": max_iter})

        self.params = result.x
        self.trained = True

        predictions = np.array([self.predict_proba(x) > 0.5 for x in X])
        accuracy = np.mean(predictions == y)

        return {
            "loss": result.fun,
            "accuracy": accuracy,
            "iterations": result.nfev,
        }


class QuantumEnhancedStrategy:
    """
    Trading strategy that uses a QuantumClassifier to generate signals.

    Extracts features (returns, volatility, RSI) from price data,
    trains the quantum classifier on historical patterns, then
    generates BUY/SELL signals for new data.
    """

    def __init__(self, lookback: int = 20, n_layers: int = 2):
        self.name = f"QuantumML_{lookback}"
        self.lookback = lookback
        self.n_features = 3  # returns, volatility, rsi_normalized
        self.classifier = QuantumClassifier(self.n_features, n_layers)
        self.position = 0

    def _extract_features(self, data) -> np.ndarray:
        """Extract normalized features from price data."""
        import pandas as pd

        close = data["Close"] if isinstance(data, pd.DataFrame) else data

        ret = close.pct_change(self.lookback).fillna(0)
        vol = close.pct_change().rolling(self.lookback).std().fillna(0)
        # Simple RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 1 - (1 / (1 + rs))  # normalized to [0, 1]
        rsi = rsi.fillna(0.5)

        # Normalize to [-1, 1]
        def norm(s):
            std = s.std()
            if std > 0:
                return ((s - s.mean()) / std).clip(-1, 1)
            return s * 0

        features = pd.DataFrame(
            {
                "returns": norm(ret),
                "volatility": norm(vol),
                "rsi": rsi * 2 - 1,  # [0,1] -> [-1,1]
            },
            index=close.index,
        )

        return features

    def generate_signals(self, data) -> Any:
        """Generate trading signals using the quantum classifier."""
        import pandas as pd

        features_df = self._extract_features(data)
        signals = pd.Series(0, index=data.index)

        # Need enough history to extract features
        valid_start = max(self.lookback, 14) + 5
        if len(data) < valid_start + 50:
            return signals

        # Build training data from first 70% of valid data
        valid_features = features_df.iloc[valid_start:]
        future_returns = data["Close"].pct_change(5).shift(-5)

        train_end = int(len(valid_features) * 0.7)
        train_features = valid_features.iloc[:train_end]
        train_returns = future_returns.loc[train_features.index]

        X_train = train_features.dropna().values
        y_raw = train_returns.loc[train_features.dropna().index].dropna()

        common_idx = train_features.dropna().index.intersection(y_raw.index)
        X_train = train_features.loc[common_idx].values
        y_train = (future_returns.loc[common_idx] > 0).astype(int).values

        if len(X_train) < 20:
            return signals

        # Subsample for speed (quantum simulation is expensive)
        if len(X_train) > 100:
            idx = np.random.choice(len(X_train), 100, replace=False)
            X_train = X_train[idx]
            y_train = y_train[idx]

        self.classifier.fit(X_train, y_train, max_iter=100)

        # Generate signals on test portion
        test_features = valid_features.iloc[train_end:]
        for i, (date, row) in enumerate(test_features.iterrows()):
            feat = row.values
            if np.any(np.isnan(feat)):
                continue
            pred = self.classifier.predict(feat)
            signals.loc[date] = pred

        return signals
