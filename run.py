#!/usr/bin/env python3
"""
QuantMining CLI - 命令行工具
快速运行量化交易策略回测
"""

import argparse
import sys
from src.pipeline import Pipeline, PipelineConfig
from src.trading.backtesting.portfolio_backtest import PortfolioBacktester
from src.data.mock import generate_multiple_stocks
from src.data import add_indicators
from src.trading.strategies import create_strategy, STRATEGIES


def main():
    parser = argparse.ArgumentParser(
        description="QuantMining - 量化交易策略回测工具"
    )
    
    parser.add_argument(
        '--tickers', 
        nargs='+',
        default=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
        help='股票代码列表'
    )
    
    parser.add_argument(
        '--strategy', 
        choices=list(STRATEGIES.keys()),
        default='sma_crossover',
        help='交易策略'
    )
    
    parser.add_argument(
        '--period',
        default='2y',
        help='数据周期 (1mo, 3mo, 6mo, 1y, 2y, 5y)'
    )
    
    parser.add_argument(
        '--capital',
        type=float,
        default=100000,
        help='初始资金'
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='使用模拟数据'
    )
    
    parser.add_argument(
        '--portfolio',
        action='store_true',
        help='运行组合策略回测 (多股票)'
    )
    
    parser.add_argument(
        '--max-positions',
        type=int,
        default=3,
        help='最大持仓数量 (组合模式)'
    )
    
    args = parser.parse_args()
    
    # 策略参数
    strategy_params = {}
    if args.strategy == 'sma_crossover':
        strategy_params = {'fast_period': 20, 'slow_period': 50}
    elif args.strategy == 'rsi':
        strategy_params = {'period': 14, 'oversold': 30, 'overbought': 70}
    elif args.strategy == 'macd':
        strategy_params = {'fast': 12, 'slow': 26, 'signal': 9}
    elif args.strategy == 'bollinger':
        strategy_params = {'period': 20, 'std_dev': 2.0}
    elif args.strategy == 'momentum':
        strategy_params = {'lookback': 20, 'threshold': 0.02}
    
    print("=" * 60)
    print("🚀 QuantMining Pipeline")
    print("=" * 60)
    print(f"Tickers: {', '.join(args.tickers)}")
    print(f"Strategy: {args.strategy}")
    print(f"Period: {args.period}")
    print(f"Capital: ${args.capital:,.2f}")
    print(f"Mode: {'Mock Data' if args.mock else 'Real Data'}")
    print("=" * 60)
    
    if args.portfolio:
        # 组合模式
        period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        days = period_days.get(args.period, 365)
        start_date = f"2024-01-01"
        
        data = generate_multiple_stocks(args.tickers, start_date=start_date)
        for ticker in data:
            data[ticker] = add_indicators(data[ticker])
        
        strategy = create_strategy(args.strategy, **strategy_params)
        
        backtester = PortfolioBacktester(
            initial_capital=args.capital,
            max_positions=args.max_positions,
            position_size=1.0 / args.max_positions,
        )
        
        result = backtester.run(data, strategy)
        
        print("\n📊 PORTFOLIO BACKTEST RESULTS")
        print("-" * 60)
        print(f"Total Return:    {result['total_return']:.2%}")
        print(f"Annual Return:   {result['annual_return']:.2%}")
        print(f"Sharpe Ratio:    {result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:    {result['max_drawdown']:.2%}")
        print(f"Total Trades:    {result['total_trades']}")
        print(f"Buys: {result['total_buys']}, Sells: {result['total_sells']}")
        
    else:
        # 单股票模式
        config = PipelineConfig(
            tickers=args.tickers,
            strategy_name=args.strategy,
            strategy_params=strategy_params,
            initial_capital=args.capital,
            period=args.period,
            use_mock_data=args.mock,
        )
        
        pipeline = Pipeline(config)
        results = pipeline.run_full_pipeline()
        
        print("\n✅ Backtest completed!")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
