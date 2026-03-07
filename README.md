# QuantMining — A Personal Deep Dive into Quantitative Trading

> Built from scratch to study classical trading strategies, technical analysis, backtesting methodology, and quantum approaches to portfolio optimization.

**[Live Demo](https://quants-mining.streamlit.app)** · **[Source Code](https://github.com/ZGChung/quants-mining)**

---

## What This Project Explores

### Classical Trading Strategies (15 implemented)

| Category | Strategies |
|----------|-----------|
| Trend following | SMA Crossover, MACD, ADX, Multi-Timeframe MA |
| Mean reversion | RSI, Bollinger Bands, Mean Reversion, CCI, Williams %R |
| Momentum | Momentum, Breakout, OBV |
| Volume-based | VWAP, MFI, Stochastic |

Each strategy follows the same `Strategy` base class with a `generate_signals()` method, making them composable and testable.

### Backtesting & Risk Management

- Portfolio backtester supporting multiple assets, position sizing, slippage, and commission
- Risk metrics: VaR (95/99%), CVaR, Sharpe ratio, Sortino ratio, Calmar ratio, profit factor
- Paper trading simulator for step-by-step strategy execution on historical data
- Parameter optimization via grid search across any strategy's parameter space

### Quantum Portfolio Optimization

I explored how quantum computing concepts apply to portfolio optimization:

- **QAOA Circuit** — Formulated asset selection as a QUBO (Quadratic Unconstrained Binary Optimization) problem. Implemented the QAOA ansatz with cost and mixer Hamiltonians. Classical simulation evaluates all 2^n bitstrings; optional Qiskit path builds actual quantum circuits.
- **Variational Ansatz** — Parameterized Ry rotation + CNOT entanglement circuit for continuous weight optimization, trained via scipy.
- **Markowitz Comparison** — Classical mean-variance optimizer using scipy SLSQP, with efficient frontier visualization. The app compares Markowitz weights against QAOA selection side-by-side.

### Quantum Machine Learning

- **Quantum Feature Map** — Angle encoding of financial features (returns, volatility, RSI) into qubit rotations with ZZ entanglement for feature interactions
- **Variational Quantum Classifier** — Feature map + trainable rotation layers + measurement, trained via cross-entropy loss to predict BUY/SELL signals
- All quantum simulation runs on numpy state vectors — no quantum hardware required

### Data Pipeline

- Multi-source: Yahoo Finance (free), Alpha Vantage, Finnhub
- 17 technical indicators (SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastic, ADX, VWAP, OBV, CCI, MFI, Williams %R, Ichimoku, etc.)
- Market scanner for momentum, volatility, and oversold screening
- Caching and rate limiting

---

## Quick Start

```bash
# Create environment
conda create -n qm python=3.11 -y
conda activate qm
pip install -r requirements.txt

# Run the web app
streamlit run app.py

# Run from CLI
python run.py --tickers AAPL MSFT GOOGL --strategy rsi --portfolio

# Run tests
pytest tests/ -v
```

## Project Structure

```
src/
├── data/               # Data fetching, indicators, mock data, market scanner
├── trading/
│   ├── strategies/     # 15 strategy implementations (base, advanced, expert)
│   ├── backtesting/    # Portfolio backtester engine
│   ├── paper.py        # Paper trading simulator
│   ├── risk.py         # Risk metrics (VaR, CVaR, Sortino, Calmar)
│   ├── export.py       # CSV/JSON result export
│   └── portfolio.py    # Portfolio management
└── quantum/
    ├── circuits/       # QAOA circuit, variational ansatz
    ├── ml/             # Quantum feature map, variational classifier
    └── optimizers/     # Markowitz + QAOA portfolio optimizers
```

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | Streamlit |
| Data | yfinance, Alpha Vantage API, Finnhub API |
| Computation | NumPy, Pandas, SciPy |
| Quantum | Custom numpy simulation, optional Qiskit |
| CI/CD | GitHub Actions (pytest, black, flake8, mypy) |

## License

MIT
