# QuantMining 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行回测

#### 单股票模式
```bash
python run.py --tickers AAPL MSFT --strategy sma_crossover --period 2y --mock
```

#### 组合策略模式 (多股票)
```bash
python run.py --portfolio --tickers AAPL MSFT GOOGL AMZN NVDA --strategy sma_crossover --period 2y --mock
```

## 可用策略

| 策略 | 参数 | 描述 |
|------|------|------|
| `sma_crossover` | fast_period, slow_period | 均线交叉策略 |
| `rsi` | period, oversold, overbought | RSI 超买超卖 |
| `macd` | fast, slow, signal | MACD 金叉死叉 |
| `bollinger` | period, std_dev | 布林带策略 |
| `momentum` | lookback, threshold | 动量策略 |

## 使用示例

### Python API

```python
from src.pipeline import Pipeline, PipelineConfig

config = PipelineConfig(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    strategy_name='sma_crossover',
    strategy_params={'fast_period': 20, 'slow_period': 50},
    initial_capital=100000,
    period='2y',
    use_mock_data=True,  # 使用模拟数据
)

pipeline = Pipeline(config)
results = pipeline.run_full_pipeline()
```

### 组合策略回测

```python
from src.trading.backtesting.portfolio_backtest import PortfolioBacktester
from src.trading.strategies import SMACrossover
from src.data.mock import generate_multiple_stocks
from src.data import add_indicators

# 准备数据
data = generate_multiple_stocks(['AAPL', 'MSFT', 'GOOGL'])
for ticker in data:
    data[ticker] = add_indicators(data[ticker])

# 运行回测
strategy = SMACrossover(20, 50)
backtester = PortfolioBacktester(initial_capital=100000, max_positions=3)
result = backtester.run(data, strategy)

print(f"Total Return: {result['total_return']:.2%}")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
```

## CLI 参数

```
--tickers        股票代码列表
--strategy       策略名称
--period        数据周期 (1mo, 3mo, 6mo, 1y, 2y, 5y)
--capital       初始资金
--mock          使用模拟数据
--portfolio     运行组合策略回测
--max-positions 最大持仓数量
```

## 项目结构

```
quantmining/
├── src/
│   ├── data/
│   │   ├── fetcher.py      # 数据获取
│   │   ├── indicators.py   # 技术指标
│   │   └── mock.py         # 模拟数据
│   ├── trading/
│   │   ├── strategies/     # 交易策略
│   │   ├── backtesting/    # 回测引擎
│   │   └── portfolio.py   # 投资组合
│   └── pipeline.py         # 主流程
├── run.py                  # CLI 入口
└── requirements.txt       # 依赖
```

## 注意

- Yahoo Finance API 有速率限制，建议使用 `--mock` 参数进行测试
- 真实数据获取可能需要等待或配置代理
