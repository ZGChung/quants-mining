"""
QuantMining - 完整版
支持多数据源，回测、参数优化、选股
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="QuantMining",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 QuantMining - 量化交易平台")

# 侧边栏
st.sidebar.header("⚙️ 配置")

# 股票池
st.sidebar.subheader("📈 股票池")
stock_categories = {
    "科技": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC"],
    "金融": ["JPM", "BAC", "GS", "MS", "C", "WFC", "V", "MA", "PYPL", "SQ"],
    "消费": ["KO", "PEP", "PG", "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "DIS"],
    "医疗": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "DHR", "BMY"],
    "能源": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
}
selected_category = st.sidebar.selectbox("选择行业", list(stock_categories.keys()))
tickers = st.sidebar.multiselect("选择股票", stock_categories[selected_category], default=stock_categories[selected_category][:3])

# 策略选择
strategies = [
    ("sma_crossover", "均线交叉", "经典双均线策略"),
    ("rsi", "RSI 超买超卖", "基于相对强弱指数"),
    ("macd", "MACD 金叉死叉", "移动平均收敛发散"),
    ("bollinger", "布林带", "价格波动通道"),
    ("momentum", "动量", "价格动量策略"),
    ("mean_reversion", "均值回归", "价格回归均值"),
    ("breakout", "突破", "价格突破策略"),
    ("composite", "复合策略", "多指标组合"),
]
strategy_names = [s[0] for s in strategies]
strategy_option = st.sidebar.selectbox("选择策略", range(len(strategies)), format_func=lambda x: f"{strategies[x][0]} - {strategies[x][1]}")
strategy = strategies[strategy_option][0]

# 策略参数
st.sidebar.subheader("📌 策略参数")
strategy_params = {}

if strategy == "sma_crossover":
    strategy_params["fast_period"] = st.sidebar.slider("快线", 5, 50, 20)
    strategy_params["slow_period"] = st.sidebar.slider("慢线", 20, 200, 50)
elif strategy == "rsi":
    strategy_params["period"] = st.sidebar.slider("周期", 5, 30, 14)
    strategy_params["oversold"] = st.sidebar.slider("超卖", 10, 40, 30)
    strategy_params["overbought"] = st.sidebar.slider("超买", 60, 90, 70)
elif strategy == "macd":
    strategy_params["fast"] = st.sidebar.slider("快线", 5, 20, 12)
    strategy_params["slow"] = st.sidebar.slider("慢线", 15, 50, 26)
    strategy_params["signal"] = st.sidebar.slider("信号线", 5, 15, 9)
elif strategy == "bollinger":
    strategy_params["period"] = st.sidebar.slider("周期", 10, 50, 20)
    strategy_params["std_dev"] = st.sidebar.slider("标准差", 1.0, 3.0, 2.0)
elif strategy == "momentum":
    strategy_params["lookback"] = st.sidebar.slider("回看", 5, 50, 20)
    strategy_params["threshold"] = st.sidebar.slider("阈值", 0.01, 0.1, 0.02)
elif strategy == "mean_reversion":
    strategy_params["period"] = st.sidebar.slider("周期", 10, 50, 20)
    strategy_params["std_dev"] = st.sidebar.slider("标准差", 1.0, 3.0, 2.0)
elif strategy == "breakout":
    strategy_params["lookback"] = st.sidebar.slider("回看", 10, 50, 20)

# 回测参数
st.sidebar.subheader("📊 回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 10, 3)
period = st.sidebar.select_slider("周期", options=["1mo", "3mo", "6mo", "1y", "2y"], value="2y")

# 主界面
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 回测", "📈 优化", "📉 对比", "🔍 选股", "ℹ️ 关于"])

with tab1:
    st.header("策略回测")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🚀 运行回测", type="primary", use_container_width=True):
            if not tickers:
                st.error("请选择股票")
            else:
                with st.spinner("回测中..."):
                    try:
                        from src.data.mock import generate_multiple_stocks
                        from src.data import add_indicators
                        from src.trading.strategies import create_strategy
                        from src.trading.backtesting import PortfolioBacktester
                        
                        period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                        start_date = (datetime.now() - timedelta(days=period_days.get(period, 365))).strftime("%Y-%m-%d")
                        
                        data = generate_multiple_stocks(tickers, start_date=start_date)
                        for ticker in data:
                            data[ticker] = add_indicators(data[ticker])
                        
                        strat = create_strategy(strategy, **strategy_params)
                        backtester = PortfolioBacktester(
                            initial_capital=initial_capital,
                            max_positions=max_positions,
                            position_size=1.0 / max_positions
                        )
                        result = backtester.run(data, strat)
                        
                        st.success("✅ 回测完成!")
                        
                        # 指标
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("总收益", f"{result['total_return']:.2%}")
                        m2.metric("年化收益", f"{result['annual_return']:.2%}")
                        m3.metric("夏普", f"{result['sharpe_ratio']:.2f}")
                        m4.metric("最大回撤", f"{result['max_drawdown']:.2%}")
                        
                        # 图表
                        if not result['equity_curve'].empty:
                            st.line_chart(result['equity_curve']['equity'])
                        
                        # 统计
                        s1, s2, s3 = st.columns(3)
                        s1.metric("交易次数", result['total_trades'])
                        s2.metric("买入", result['total_buys'])
                        s3.metric("卖出", result['total_sells'])
                        
                    except Exception as e:
                        st.error(f"失败: {str(e)}")
    
    with col2:
        st.info(f"""
        **当前配置**
        - 股票: {len(tickers)} 只
        - 策略: {strategy}
        - 资金: ${initial_capital:,}
        """)

with tab2:
    st.header("参数优化")
    st.info("🎯 自动搜索最优参数")
    
    opt_strategy = st.selectbox("选择策略", strategy_names)
    
    if st.button("⚡ 开始优化"):
        with st.spinner("优化中..."):
            try:
                from src.trading.optimize import StrategyOptimizer
                from src.data.mock import generate_multiple_stocks
                from src.data import add_indicators
                
                data = generate_multiple_stocks(tickers[:3], start_date="2024-01-01")
                for ticker in data:
                    data[ticker] = add_indicators(data[ticker])
                
                if opt_strategy == "sma_crossover":
                    param_grid = {'fast_period': [10, 15, 20, 25], 'slow_period': [30, 40, 50, 60]}
                elif opt_strategy == "rsi":
                    param_grid = {'period': [10, 14, 21], 'oversold': [20, 30], 'overbought': [70, 80]}
                else:
                    param_grid = {'fast_period': [10, 20], 'slow_period': [30, 50]}
                
                optimizer = StrategyOptimizer(data, opt_strategy)
                result = optimizer.optimize(param_grid)
                
                st.success("✅ 优化完成!")
                st.json(result.best_params)
                st.metric("最佳夏普", f"{result.best_sharpe:.3f}")
                
            except Exception as e:
                st.error(f"失败: {str(e)}")

with tab3:
    st.header("多策略对比")
    
    compare = st.multiselect("选择策略", strategy_names, default=["sma_crossover", "rsi"])
    
    if st.button("🔄 对比") and compare:
        with st.spinner("对比中..."):
            try:
                from src.data.mock import generate_multiple_stocks
                from src.data import add_indicators
                from src.trading.strategies import create_strategy
                from src.trading.backtesting import PortfolioBacktester
                
                period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                start_date = (datetime.now() - timedelta(days=period_days.get(period, 365))).strftime("%Y-%m-%d")
                
                data = generate_multiple_stocks(tickers[:3], start_date=start_date)
                for ticker in data:
                    data[ticker] = add_indicators(data[ticker])
                
                results = []
                for s in compare:
                    strat = create_strategy(s)
                    bt = PortfolioBacktester(initial_capital, max_positions, 1.0/max_positions)
                    r = bt.run(data, strat)
                    results.append({'策略': s, '收益': f"{r['total_return']:.2%}", '夏普': f"{r['sharpe_ratio']:.2f}", '回撤': f"{r['max_drawdown']:.2%}"})
                
                st.dataframe(pd.DataFrame(results), use_container_width=True)
                
            except Exception as e:
                st.error(f"失败: {str(e)}")

with tab4:
    st.header("股票筛选器")
    st.info("🔍 基于技术指标筛选股票")
    
    screener_criteria = st.multiselect(
        "筛选条件",
        ["RSI < 30 (超卖)", "RSI > 70 (超买)", "价格 > MA20", "MA20 > MA50", "MACD 金叉"]
    )
    
    if st.button("🔍 开始筛选") and screener_criteria:
        with st.spinner("筛选中..."):
            try:
                from src.data.mock import generate_multiple_stocks
                from src.data import add_indicators
                from src.trading.strategies import create_strategy
                
                data = generate_multiple_stocks(tickers, start_date="2024-01-01")
                for ticker in data:
                    data[ticker] = add_indicators(data[ticker])
                
                results = []
                for ticker, df in data.items():
                    score = 0
                    signals = []
                    
                    if "RSI < 30 (超卖)" in screener_criteria:
                        rsi = df['rsi_14'].iloc[-1] if 'rsi_14' in df.columns else 50
                        if rsi < 30:
                            score += 1
                            signals.append("RSI超卖")
                    
                    if "RSI > 70 (超买)" in screener_criteria:
                        rsi = df['rsi_14'].iloc[-1] if 'rsi_14' in df.columns else 50
                        if rsi > 70:
                            score += 1
                            signals.append("RSI超买")
                    
                    if "价格 > MA20" in screener_criteria:
                        if 'sma_20' in df.columns and df['Close'].iloc[-1] > df['sma_20'].iloc[-1]:
                            score += 1
                            signals.append("价格>MA20")
                    
                    if score > 0:
                        results.append({
                            '股票': ticker,
                            '分数': score,
                            '信号': ', '.join(signals),
                            '价格': f"${df['Close'].iloc[-1]:.2f}"
                        })
                
                if results:
                    st.dataframe(pd.DataFrame(results).sort_values('分数', ascending=False), use_container_width=True)
                else:
                    st.warning("没有符合条件的股票")
                    
            except Exception as e:
                st.error(f"失败: {str(e)}")

with tab5:
    st.header("关于")
    st.markdown("""
    ## 📈 QuantMining
    
    量化交易研究平台
    
    ### 功能
    - 📊 策略回测
    - 📈 参数优化
    - 📉 多策略对比
    - 🔍 股票筛选
    
    ### 策略
    """)
    for s in strategies:
        st.markdown(f"- **{s[0]}**: {s[2]}")
    
    st.markdown("""
    ### 访问
    **https://quants-mining.streamlit.app**
    """)
    st.caption("Made with ❤️ by Allen AI")

st.sidebar.divider()
st.sidebar.caption(f"📊 QuantMining v1.2 | 股票: {len(tickers)}")
