"""
QuantMining - 量化交易策略平台
支持多数据源、回测、参数优化
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加 src 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置页面
st.set_page_config(
    page_title="QuantMining",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📈 QuantMining - 量化交易平台")

# 侧边栏 - 配置
st.sidebar.header("⚙️ 配置")

# 数据源选择
data_source = st.sidebar.radio("数据源", ["模拟数据", "真实数据"], index=0)

# 股票选择
default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
tickers = st.sidebar.multiselect(
    "选择股票",
    default_tickers,
    default=default_tickers[:5]
)

# 策略选择
strategies = [
    "sma_crossover",
    "rsi",
    "macd",
    "bollinger",
    "momentum",
    "mean_reversion",
    "breakout",
    "composite",
    "trend_following",
    "adx",
    "cci"
]
strategy = st.sidebar.selectbox("选择策略", strategies)

# 策略参数
st.sidebar.subheader("📌 策略参数")
strategy_params = {}

if strategy == "sma_crossover":
    strategy_params["fast_period"] = st.sidebar.slider("快线周期", 5, 50, 20)
    strategy_params["slow_period"] = st.sidebar.slider("慢线周期", 20, 200, 50)
elif strategy == "rsi":
    strategy_params["period"] = st.sidebar.slider("RSI 周期", 5, 30, 14)
    strategy_params["oversold"] = st.sidebar.slider("超卖阈值", 10, 40, 30)
    strategy_params["overbought"] = st.sidebar.slider("超买阈值", 60, 90, 70)
elif strategy == "macd":
    strategy_params["fast"] = st.sidebar.slider("MACD 快线", 5, 20, 12)
    strategy_params["slow"] = st.sidebar.slider("MACD 慢线", 15, 50, 26)
    strategy_params["signal"] = st.sidebar.slider("MACD 信号线", 5, 15, 9)
elif strategy == "bollinger":
    strategy_params["period"] = st.sidebar.slider("布林带周期", 10, 50, 20)
    strategy_params["std_dev"] = st.sidebar.slider("标准差倍数", 1.0, 3.0, 2.0)
elif strategy == "momentum":
    strategy_params["lookback"] = st.sidebar.slider("回看周期", 5, 50, 20)
    strategy_params["threshold"] = st.sidebar.slider("阈值", 0.01, 0.1, 0.02)

# 回测参数
st.sidebar.subheader("📊 回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 10, 3)
period = st.sidebar.select_slider("数据周期", options=["1mo", "3mo", "6mo", "1y", "2y"], value="2y")

# 主界面
tab1, tab2, tab3 = st.tabs(["📊 回测", "📈 策略优化", "ℹ️ 关于"])

with tab1:
    st.header("策略回测")
    
    if st.button("🚀 运行回测", type="primary", use_container_width=True):
        if not tickers:
            st.error("请选择至少一只股票")
        else:
            with st.spinner("运行回测中..."):
                try:
                    # 导入模块
                    from src.data.mock import generate_multiple_stocks
                    from src.data import add_indicators
                    from src.trading.strategies import create_strategy
                    from src.trading.backtesting import PortfolioBacktester
                    
                    # 准备数据
                    period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    start_date = (datetime.now() - timedelta(days=period_days.get(period, 365))).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    # 运行回测
                    strat = create_strategy(strategy, **strategy_params)
                    backtester = PortfolioBacktester(
                        initial_capital=initial_capital,
                        max_positions=max_positions,
                        position_size=1.0 / max_positions
                    )
                    result = backtester.run(data, strat)
                    
                    # 显示结果
                    st.success("✅ 回测完成!")
                    
                    # 指标卡片
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("总收益率", f"{result['total_return']:.2%}")
                    col2.metric("年化收益率", f"{result['annual_return']:.2%}")
                    col3.metric("夏普比率", f"{result['sharpe_ratio']:.2f}")
                    col4.metric("最大回撤", f"{result['max_drawdown']:.2%}")
                    
                    # 权益曲线
                    st.subheader("📈 权益曲线")
                    equity_df = result['equity_curve']
                    if not equity_df.empty:
                        st.line_chart(equity_df['equity'])
                    
                    # 交易统计
                    col1, col2 = st.columns(2)
                    col1.metric("交易次数", result['total_trades'])
                    col2.metric("买入次数", result['total_buys'])
                    
                except Exception as e:
                    st.error(f"回测失败: {str(e)}")

with tab2:
    st.header("策略参数优化")
    st.info("🎯 选择策略和参数范围，系统将自动搜索最优参数")
    
    opt_strategy = st.selectbox("选择要优化的策略", ["sma_crossover", "rsi", "macd"])
    
    if st.button("开始优化", type="primary"):
        with st.spinner("优化中，请稍候... 这可能需要几分钟"):
            try:
                from src.trading.optimize import StrategyOptimizer
                from src.data.mock import generate_multiple_stocks
                from src.data import add_indicators
                
                # 准备数据
                data = generate_multiple_stocks(tickers[:3], start_date="2024-01-01")
                for ticker in data:
                    data[ticker] = add_indicators(data[ticker])
                
                # 参数网格
                if opt_strategy == "sma_crossover":
                    param_grid = {
                        'fast_period': [10, 15, 20, 25],
                        'slow_period': [30, 40, 50, 60],
                    }
                elif opt_strategy == "rsi":
                    param_grid = {
                        'period': [10, 14, 21],
                        'oversold': [20, 30],
                        'overbought': [70, 80],
                    }
                else:
                    param_grid = {'fast': [10, 12], 'slow': [24, 26]}
                
                optimizer = StrategyOptimizer(data, opt_strategy, metric='sharpe_ratio')
                opt_result = optimizer.optimize(param_grid)
                
                st.success("🎉 优化完成!")
                
                # 显示最佳参数
                st.subheader("🏆 最佳参数")
                st.json(opt_result.best_params)
                
                # 显示 Top 5
                st.subheader("📊 Top 5 结果")
                results_df = pd.DataFrame(opt_result.all_results[:5])
                if not results_df.empty:
                    results_df['total_return'] = results_df['total_return'].apply(lambda x: f"{x:.2%}")
                    results_df['sharpe_ratio'] = results_df['sharpe_ratio'].apply(lambda x: f"{x:.3f}")
                    st.dataframe(results_df, use_container_width=True)
                    
            except Exception as e:
                st.error(f"优化失败: {str(e)}")

with tab3:
    st.header("关于 QuantMining")
    
    st.markdown("""
    ## 📈 QuantMining
    
    量化交易策略研究平台
    
    ### 功能
    - 📊 多策略回测
    - 📈 参数优化
    - 📉 风险指标
    - 🔄 多数据源支持
    
    ### 可用策略
    | 策略 | 描述 |
    |------|------|
    | sma_crossover | 均线交叉 |
    | rsi | RSI 超买超卖 |
    | macd | MACD 金叉死叉 |
    | bollinger | 布林带 |
    | momentum | 动量 |
    | mean_reversion | 均值回归 |
    | breakout | 突破 |
    | composite | 复合 |
    | trend_following | 趋势跟随 |
    
    ### 运行方式
    ```bash
    # 本地运行
    streamlit run app.py
    
    # 或使用 CLI
    python run.py --portfolio --tickers AAPL MSFT --strategy rsi --mock
    ```
    
    ### 数据源
    - 🟡 Yahoo Finance (免费，有限制)
    - 🟢 Alpha Vantage (免费 key 可用)
    - 🟢 Polygon.io (免费 key 可用)
    - 🟢 Finnhub (免费 key 可用)
    """)
    
    st.divider()
    st.caption("Made with ❤️ by Allen AI Agent")

if __name__ == "__main__":
    st.run()
