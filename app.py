"""
QuantMining - 生产版
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 设置路径
app_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(app_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

st.set_page_config(
    page_title="QuantMining Pro",
    page_icon="📈",
    layout="wide"
)

st.title("📈 QuantMining Pro")

# 侧边栏
st.sidebar.header("⚙️ 配置")

# 股票池
st.sidebar.subheader("📈 股票池")

preset_pools = {
    "科技": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
    "金融": ["JPM", "BAC", "GS", "MS", "C"],
    "消费": ["AMZN", "TSLA", "KO", "PEP", "PG"],
}

pool_option = st.sidebar.selectbox("选择股票池", list(preset_pools.keys()))
tickers = st.sidebar.multiselect("股票", preset_pools[pool_option], default=preset_pools[pool_option][:3])

# 策略
st.sidebar.subheader("🎯 策略")

strategies_list = [
    ("sma_crossover", "均线交叉"),
    ("rsi", "RSI"),
    ("macd", "MACD"),
    ("bollinger", "布林带"),
    ("momentum", "动量"),
]
strategy_names = [s[0] for s in strategies_list]
strategy_option = st.sidebar.selectbox("选择策略", range(len(strategies_list)), format_func=lambda x: f"{strategies_list[x][0]} - {strategies_list[x][1]}")
strategy = strategies_list[strategy_option][0]

# 策略参数
strategy_params = {}
if strategy == "sma_crossover":
    strategy_params["fast_period"] = st.sidebar.slider("快线", 5, 50, 20)
    strategy_params["slow_period"] = st.sidebar.slider("慢线", 20, 200, 50)
elif strategy == "rsi":
    strategy_params["period"] = st.sidebar.slider("周期", 5, 30, 14)
    strategy_params["oversold"] = st.sidebar.slider("超卖", 10, 40, 30)
    strategy_params["overbought"] = st.sidebar.slider("超买", 60, 90, 70)

# 回测参数
st.sidebar.subheader("📊 回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 10, 3)
period = st.sidebar.select_slider("周期", options=["3mo", "6mo", "1y", "2y"], value="2y")

# 主界面
tab1, tab2, tab3 = st.tabs(["📊 回测", "📈 优化", "ℹ️ 关于"])

with tab1:
    st.header("策略回测")
    
    if st.button("🚀 运行回测", type="primary", use_container_width=True):
        if not tickers:
            st.error("请选择股票")
        else:
            with st.spinner("回测中..."):
                try:
                    # 动态导入
                    from data.mock import generate_multiple_stocks
                    from data.indicators import add_indicators
                    from trading.strategies import create_strategy
                    from trading.backtesting import PortfolioBacktester
                    
                    # 生成数据
                    period_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    days = period_days.get(period, 365)
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    # 策略
                    strat = create_strategy(strategy, **strategy_params)
                    
                    # 回测
                    backtester = PortfolioBacktester(
                        initial_capital=initial_capital,
                        max_positions=max_positions,
                        position_size=0.2
                    )
                    result = backtester.run(data, strat)
                    
                    # 显示
                    st.success("✅ 回测完成!")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("总收益", f"{result['total_return']:.2%}")
                    c2.metric("年化收益", f"{result['annual_return']:.2%}")
                    c3.metric("夏普", f"{result['sharpe_ratio']:.2f}")
                    c4.metric("最大回撤", f"{result['max_drawdown']:.2%}")
                    
                    if not result['equity_curve'].empty:
                        st.line_chart(result['equity_curve']['equity'])
                    
                except Exception as e:
                    st.error(f"失败: {str(e)}")

with tab2:
    st.header("参数优化")
    st.info("🎯 选择策略和参数范围自动搜索最优参数")

with tab3:
    st.header("关于")
    st.markdown("""
    ## 📈 QuantMining Pro
    
    量化交易研究平台
    
    ### 功能
    - 📊 策略回测
    - 📈 参数优化
    - 📉 多策略对比
    
    ### 访问
    **https://quants-mining.streamlit.app**
    """)
    st.caption("Made with ❤️ by Allen AI")

st.sidebar.divider()
st.sidebar.caption(f"📊 QuantMining Pro v2.1")
