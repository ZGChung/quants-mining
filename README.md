# QuantMining - 量化交易回测平台

> **Status: Archived / 已归档** — 本项目不再积极维护。代码可正常运行，欢迎 fork。

## 在线体验

https://quants-mining.streamlit.app

## 功能

- **15 个交易策略**：SMA、RSI、MACD、Bollinger、Momentum、Mean Reversion、Breakout、ADX、VWAP、OBV、CCI、MFI、Williams %R、Stochastic、Multi-Timeframe
- **组合回测**：多股票、滑点、手续费、胜率统计
- **参数优化**：网格搜索
- **策略对比**：并排比较收益、夏普、回撤
- **多数据源**：Yahoo Finance (免费)、Alpha Vantage、Finnhub
- **17 个技术指标**

## 快速开始

```bash
conda create -n qm python=3.11 -y
conda activate qm
pip install -r requirements.txt

# Web 界面
streamlit run app.py

# CLI
python run.py --tickers AAPL MSFT GOOGL --strategy rsi --portfolio

# 测试
pytest tests/ -v
```

## 项目结构

```
src/
├── data/           # 数据获取、指标计算、模拟数据
├── trading/        # 策略、回测、组合管理、优化
└── quantum/        # 量子优化 (实验性，需 Qiskit)
```

## 许可证

MIT License
