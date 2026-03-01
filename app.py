"""
QuantMining Web Interface
使用 Streamlit 构建的 Web 界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 配置页面
st.set_page_config(
    page_title="QuantMining",
    page_icon="📈",
    layout="wide"
)

# 标题
st.title("📈 QuantMining - 量化交易策略平台")

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
strategy = st.sidebar.selectbox(
    "选择策略",
    [
        "sma_crossover",
        "rsi",
        "macd",
        "bollinger",
        "momentum",
        "mean_reversion",
        "breakout",
        "composite",
        "trend_following"
    ]
)

# 策略参数
st.sidebar.subheader("策略参数")
if strategy == "sma_crossover":
    fast_period = st.sidebar.slider("快线周期", 5, 50, 20)
    slow_period = st.sidebar.slider("慢线周期", 20, 200, 50)
    strategy_params = {"fast_period": fast_period, "slow_period": slow_period}
elif strategy == "rsi":
    rsi_period = st.sidebar.slider("RSI 周期", 5, 30, 14)
    oversold = st.sidebar.slider("超卖阈值", 10, 40, 30)
    overbought = st.sidebar.slider("超买阈值", 60, 90, 70)
    strategy_params = {"period": rsi_period, "oversold": oversold, "overbought": overbought}
elif strategy == "macd":
    fast = st.sidebar.slider("MACD 快线", 5, 20, 12)
    slow = st.sidebar.slider("MACD 慢线", 15, 50, 26)
    signal = st.sidebar.slider("MACD 信号线", 5, 15, 9)
    strategy_params = {"fast": fast, "slow": slow, "signal": signal}
else:
    strategy_params = {}

# 回测参数
st.sidebar.subheader("回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 10, 3)
period = st.sidebar.select_slider("数据周期", options=["1mo", "3mo", "6mo", "1y", "2y"], value="2y")

# 主界面
tab1, tab2, tab3, tab4 = st.tabs(["📊 回测", "📈 策略优化", "🔧 系统状态", "📖 说明"])

with tab1:
    st.header("策略回测")
    
    if st.button("🚀 运行回测", type="primary"):
        if not tickers:
            st.error("请选择至少一只股票")
        else:
            with st.spinner("运行回测中..."):
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
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("总收益率", f"{result['total_return']:.2%}")
                col2.metric("年化收益率", f"{result['annual_return']:.2%}")
                col3.metric("夏普比率", f"{result['sharpe_ratio']:.2f}")
                col4.metric("最大回撤", f"{result['max_drawdown']:.2%}")
                
                # 权益曲线
                st.subheader("📈 权益曲线")
                equity_df = result['equity_curve']
                st.line_chart(equity_df['equity'])
                
                # 交易统计
                st.subheader("📋 交易统计")
                col1, col2 = st.columns(2)
                col1.metric("交易次数", result['total_trades'])
                col2.metric("买入次数", result['total_buys'])
                
                st.success("回测完成! ✅")

with tab2:
    st.header("策略参数优化")
    st.info("选择策略和参数范围，系统将自动搜索最优参数")
    
    if st.button("开始优化"):
        with st.spinner("优化中，请稍候..."):
            from src.trading.optimize import StrategyOptimizer
            from src.data.mock import generate_multiple_stocks
            from src.data import add_indicators
            
            data = generate_multiple_stocks(tickers[:3], start_date="2024-01-01")
            for ticker in data:
                data[ticker] = add_indicators(data[ticker])
            
            # 参数网格
            param_grid = {
                'fast_period': [10, 20, 30],
                'slow_period': [30, 50, 70],
            }
            
            optimizer = StrategyOptimizer(data, 'sma_crossover', metric='sharpe_ratio')
            opt_result = optimizer.optimize(param_grid)
            
            st.success("优化完成! ✅")
            
            st.subheader("🏆 最佳参数")
            st.json(opt_result.best_params)
            
            st.subheader("📊 Top 5 结果")
            results_df = pd.DataFrame(opt_result.all_results[:5])
            st.dataframe(results_df)

with tab3:
    st.header("系统状态")
    
    if st.button("检查系统状态"):
        with st.spinner("检查中..."):
            from src.heartbeat import Heartbeat
            
            heartbeat = Heartbeat()
            status = heartbeat.check_health()
            
            st.subheader("💓 健康状态")
            if status.status == "healthy":
                st.success(f"状态: {status.status.upper()}")
            else:
                st.warning(f"状态: {status.status.upper()}")
            
            st.write(status.message)
            
            st.subheader("📋 诊断报告")
            report = heartbeat.run_diagnostics()
            for rec in report['recommendations']:
                st.write(f"- {rec}")
    
    st.subheader("📦 已安装模块")
    st.write("- 数据模块: fetcher, indicators, mock")
    st.write("- 策略模块: 11 种策略")
    st.write("- 回测引擎: 单股票 + 组合")
    st.write("- 优化器: 网格搜索")
    st.write("- 可视化: matplotlib")
    st.write("- 心跳机制: Health check")

with tab4:
    st.header("使用说明")
    
    st.markdown("""
    ## QuantMining 使用指南
    
    ### 1. 回测
    - 选择股票代码
    - 选择交易策略
    - 配置策略参数
    - 点击"运行回测"
    
    ### 2. 策略优化
    - 选择要优化的策略
    - 设置参数范围
    - 系统自动搜索最优参数
    
    ### 3. 可用策略
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
    
    ### 4. 运行 Web 应用
    ```bash
    streamlit run app.py
    ```
    """)

# 运行命令
# st.sidebar.markdown("---")
# st.sidebar.code("streamlit run app.py", language="bash")
