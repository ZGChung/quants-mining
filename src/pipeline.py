"""
QuantMining Pipeline - 主流程
整合数据获取、策略、回测的投资流程
"""

import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.data import StockDataFetcher, add_indicators
from src.trading.strategies import create_strategy, Signal
from src.trading.backtesting import Backtester, BacktestResult
from src.trading.portfolio import Portfolio


@dataclass
class PipelineConfig:
    """Pipeline 配置"""

    tickers: List[str]  # 股票列表
    strategy_name: str = "sma_crossover"  # 策略名称
    strategy_params: Dict = None  # 策略参数
    initial_capital: float = 100000.0  # 初始资金
    period: str = "1y"  # 数据周期
    commission: float = 0.001  # 手续费
    slippage: float = 0.0005  # 滑点
    use_mock_data: bool = False  # 是否使用模拟数据


class Pipeline:
    """QuantMining 主流程"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.data_fetcher = StockDataFetcher()
        self.strategy = create_strategy(config.strategy_name, **(config.strategy_params or {}))
        self.backtester = Backtester(
            initial_capital=config.initial_capital,
            commission=config.commission,
            slippage=config.slippage,
        )

        self.data: Dict[str, pd.DataFrame] = {}
        self.results: Dict[str, BacktestResult] = {}

    def fetch_data(self) -> Dict[str, pd.DataFrame]:
        """获取所有股票数据"""
        print(f"📥 Fetching data for {len(self.config.tickers)} tickers...")

        if self.config.use_mock_data:
            # 使用模拟数据
            from src.data.mock import generate_multiple_stocks

            period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
            days = period_days.get(self.config.period, 365)
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")

            self.data = generate_multiple_stocks(self.config.tickers, start_date=start_date)
            # 添加技术指标
            for ticker in self.data:
                self.data[ticker] = add_indicators(self.data[ticker])

            for ticker in self.config.tickers:
                print(f"  - {ticker} (mock)")
        else:
            # 使用真实数据
            for ticker in self.config.tickers:
                print(f"  - {ticker}")
                df = self.data_fetcher.fetch(ticker, period=self.config.period)
                df = add_indicators(df)
                self.data[ticker] = df

        print(f"✅ Fetched {len(self.data)} tickers")
        return self.data

    def run_backtest(self) -> Dict[str, BacktestResult]:
        """对所有股票运行回测"""
        print(f"\n🔄 Running backtest with {self.strategy.name}...")

        for ticker, df in self.data.items():
            signals = self.strategy.generate_signals(df)
            result = self.backtester.run(df, signals)
            self.results[ticker] = result

        print(f"✅ Completed backtest for {len(self.results)} tickers")
        return self.results

    def get_top_performers(self, n: int = 5) -> List[tuple]:
        """获取表现最好的 N 只股票"""
        sorted_results = sorted(self.results.items(), key=lambda x: x[1].total_return, reverse=True)
        return sorted_results[:n]

    def summary(self) -> pd.DataFrame:
        """生成汇总报告"""
        data = []
        for ticker, result in self.results.items():
            data.append(
                {
                    "ticker": ticker,
                    "total_return": result.total_return,
                    "annual_return": result.annual_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                }
            )

        df = pd.DataFrame(data)
        df = df.sort_values("total_return", ascending=False)
        return df

    def run_full_pipeline(self) -> Dict[str, BacktestResult]:
        """运行完整流程"""
        self.fetch_data()
        self.run_backtest()

        # 打印汇总
        print("\n" + "=" * 60)
        print("📊 BACKTEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Strategy: {self.strategy.name}")
        print(f"Period: {self.config.period}")
        print(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        print("-" * 60)

        summary_df = self.summary()
        print(summary_df.to_string(index=False))

        print("\n🏆 Top Performers:")
        for ticker, result in self.get_top_performers():
            print(f"  {ticker}: {result.total_return:.2%} (Sharpe: {result.sharpe_ratio:.2f})")

        return self.results


def quick_test():
    """快速测试"""
    config = PipelineConfig(
        tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
        strategy_name="sma_crossover",
        strategy_params={"fast_period": 20, "slow_period": 50},
        initial_capital=100000,
        period="2y",
    )

    pipeline = Pipeline(config)
    results = pipeline.run_full_pipeline()

    return results


if __name__ == "__main__":
    quick_test()
