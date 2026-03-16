# QuantMining — A Personal Showcase for Quantitative Trading

> A quantitative trading research platform serving as a personal portfolio and brand showcase. Demonstrates technical depth in trading strategies, backtesting, and quantum approaches — not a product seeking PMF.

**[Live Demo](https://quants-mining.streamlit.app)** · **[Source Code](https://github.com/ZGChung/quants-mining)**

---

## Strategic Positioning

| Role | Description |
|------|-------------|
| **Showcase** | Personal brand building through technical demonstration |
| **Learning Journey** | Documenting quantitative trading research and experimentation |
| **Portfolio** | Proof of skill for potential collaborators or employers |

This project doesn't aim to be a product with PMF — it's a **technical showcase** for learning and personal branding.

---

## What This Project Demonstrates

### Trading Strategies (19 implemented)

| Category | Strategies |
|----------|-----------|
| Trend following | SMA Crossover, MACD, ADX, Multi-Timeframe MA |
| Mean reversion | RSI, Bollinger Bands, Mean Reversion, CCI, Williams %R |
| Momentum | Momentum, Breakout, OBV |
| Volume-based | VWAP, MFI, Stochastic |

### Backtesting & Risk Management

- Portfolio backtester supporting multiple assets, position sizing, slippage, and commission
- Risk metrics: VaR (95/99%), CVaR, Sharpe ratio, Sortino ratio, Calmar ratio, profit factor
- Paper trading simulator for step-by-step strategy execution
- Parameter optimization via grid search

### Quantum Portfolio Optimization

- **QAOA Circuit** — QUBO formulation for asset selection, classical simulation of 2^n bitstrings
- **Variational Ansatz** — Parameterized Ry rotation + CNOT entanglement, trained via scipy
- **Markowitz Comparison** — Classical mean-variance optimizer with efficient frontier visualization
- **Quantum ML** — Angle encoding feature map, variational classifier for BUY/SELL signals

### Data Pipeline

- Multi-source: Yahoo Finance (free), Alpha Vantage, Finnhub (API keys supported)
- 17 technical indicators (SMA, EMA, RSI, MACD, Bollinger, ATR, Stochastic, ADX, VWAP, etc.)
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

# CLI usage
python run.py --tickers AAPL MSFT GOOGL --strategy rsi --portfolio
```

---

## Project Structure

```
quantmining/
├── app.py              # Streamlit web app
├── src/
│   ├── data/           # Data fetching, indicators, mock data
│   ├── trading/
│   │   ├── strategies/ # Strategy implementations
│   │   ├── backtesting/
│   │   ├── risk.py
│   │   └── portfolio.py
│   └── quantum/        # QAOA, variational circuits, Markowitz
├── tests/
└── requirements.txt
```

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | Streamlit |
| Data | yfinance, Alpha Vantage, Finnhub |
| Computation | NumPy, Pandas, SciPy |
| Quantum | Custom numpy simulation, optional Qiskit |

---

## Related Projects

| Project | Positioning |
|---------|-------------|
| DemandPulse | Product — open-source collaboration |
| TradeSense | Game — entertainment-focused |
| QuantMining | Showcase — personal branding |

---

## License

MIT
