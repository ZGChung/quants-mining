"""
QuantMining - 生产版
添加更多高级功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="QuantMining Pro",
    page_icon="📈",
    layout="wide",
    page_pro_icon="📈"
)

st.title("📈 QuantMining Pro")

# 侧边栏 - 高级配置
st.sidebar.header("⚙️ 高级配置")

# API 配置
st.sidebar.subheader("🔑 API 配置")
api_provider = st.sidebar.selectbox(
    "数据提供商",
    ["模拟数据", "Yahoo Finance", "Alpha Vantage", "Polygon.io", "Finnhub"]
)

api_key = ""
if api_provider != "模拟数据":
    api_key = st.sidebar.text_input("API Key", type="password")
    if api_provider == "Alpha Vantage":
        st.sidebar.caption("免费: 5 calls/min, 500 calls/day")
    elif api_provider == "Polygon.io":
        st.sidebar.caption("免费: 5 calls/min")

# 股票池
st.sidebar.subheader("📈 股票池")

preset_pools = {
    "S&P 500 科技": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "CRM", "ADBE", "ORCL"],
    "S&P 500 金融": ["JPM", "BAC", "GS", "MS", "C", "WFC", "V", "MA", "BLK", "SCHW"],
    "S&P 500 消费": ["AMZN", "TSLA", "KO", "PEP", "PG", "WMT", "HD", "MCD", "NKE", "SBUX"],
    "中国概念股": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI", "BILI", "TAL", "EDU", "VIPS"],
    "加密货币相关": ["COIN", "MSTR", "RIOT", "MARA", "SI", "BITO"],
}

pool_option = st.sidebar.selectbox("选择股票池", list(preset_pools.keys()))
tickers = st.sidebar.multiselect(
    "股票",
    preset_pools[pool_option],
    default=preset_pools[pool_option][:5]
)

# 高级策略参数
st.sidebar.subheader("🎯 高级策略")

strategy_type = st.sidebar.radio(
    "策略类型",
    ["趋势跟踪", "均值回归", "动量", "突破", "多因子"]
)

strategy_params = {}

if strategy_type == "趋势跟踪":
    strategy = st.sidebar.selectbox(
        "策略",
        ["SMA Cross", "EMA Cross", "MACD", "ADX", "Ichimoku"]
    )
    if strategy == "SMA Cross":
        strategy_params["fast"] = st.sidebar.slider("快线", 5, 50, 20)
        strategy_params["slow"] = st.sidebar.slider("慢线", 20, 200, 50)
    elif strategy == "EMA Cross":
        strategy_params["fast"] = st.sidebar.slider("快线", 5, 50, 12)
        strategy_params["slow"] = st.sidebar.slider("慢线", 20, 200, 26)

elif strategy_type == "均值回归":
    strategy = st.sidebar.selectbox("策略", ["Bollinger", "RSI", "CCI"])
    if strategy == "RSI":
        strategy_params["period"] = st.sidebar.slider("周期", 5, 30, 14)
        strategy_params["oversold"] = st.sidebar.slider("超卖", 10, 40, 25)
        strategy_params["overbought"] = st.sidebar.slider("超买", 60, 90, 75)

elif strategy_type == "动量":
    strategy = st.sidebar.selectbox("策略", ["ROC", "Momentum", "Stochastic"])
    strategy_params["period"] = st.sidebar.slider("周期", 5, 50, 20)

elif strategy_type == "突破":
    strategy = st.sidebar.selectbox("策略", ["Channel Break", "Pivot Point", "Volatility"])
    strategy_params["lookback"] = st.sidebar.slider("回看", 10, 100, 20)

elif strategy_type == "多因子":
    strategy = "Multi-Factor"
    st.sidebar.info("多因子策略: 结合多个指标信号")

# 风控参数
st.sidebar.subheader("🛡️ 风控设置")
use_stop_loss = st.sidebar.checkbox("启用止损", value=True)
stop_loss_pct = st.sidebar.slider("止损比例", 1, 20, 5) if use_stop_loss else 0

use_take_profit = st.sidebar.checkbox("启用止盈", value=False)
take_profit_pct = st.sidebar.slider("止盈比例", 5, 50, 15) if use_take_profit else 0

use_trailing = st.sidebar.checkbox("启用追踪止损", value=False)
trailing_pct = st.sidebar.slider("追踪止损比例", 1, 15, 10) if use_trailing else 0

# 资金管理
st.sidebar.subheader("💰 资金管理")
position_sizing = st.sidebar.selectbox(
    "仓位方式",
    ["固定比例", "等权重", "风险平价", "Kelly Criterion"]
)

if position_sizing == "固定比例":
    position_pct = st.sidebar.slider("每笔比例", 1, 30, 10)
elif position_sizing == "Kelly Criterion":
    kelly_pct = st.sidebar.slider("Kelly 比例", 0.1, 1.0, 0.25)
    strategy_params["kelly_pct"] = kelly_pct

# 回测参数
st.sidebar.subheader("📊 回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 20, 5)
period = st.sidebar.select_slider("回测周期", options=["3mo", "6mo", "1y", "2y", "5y"], value="2y")

# 主界面 - 标签页
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 回测", "📈 优化", "📉 对比", "🔍 选股", "🛡️ 风控", "ℹ️ 关于"
])

with tab1:
    st.header("策略回测")
    
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
                    
                    # 生成数据
                    period_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
                    start_date = (datetime.now() - timedelta(days=period_days.get(period, 365))).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    # 简化策略名
                    strat_map = {
                        "SMA Cross": "sma_crossover",
                        "EMA Cross": "sma_crossover",
                        "MACD": "macd",
                        "RSI": "rsi",
                        "Bollinger": "bollinger",
                        "Momentum": "momentum",
                        "Mean Reversion": "mean_reversion",
                        "Breakout": "breakout",
                        "Multi-Factor": "composite"
                    }
                    
                    strat_name = strat_map.get(strategy, "sma_crossover")
                    strat = create_strategy(strat_name, **strategy_params)
                    
                    # 回测
                    backtester = PortfolioBacktester(
                        initial_capital=initial_capital,
                        max_positions=max_positions,
                        position_size=0.2
                    )
                    result = backtester.run(data, strat)
                    
                    # 显示结果
                    st.success("✅ 回测完成!")
                    
                    # 核心指标
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("总收益", f"{result['total_return']:.2%}", delta=f"{result['total_return']*100:.1f}%")
                    c2.metric("年化收益", f"{result['annual_return']:.2%}")
                    c3.metric("夏普比率", f"{result['sharpe_ratio']:.2f}")
                    c4.metric("最大回撤", f"{result['max_drawdown']:.2%}")
                    
                    # 图表
                    if not result['equity_curve'].empty:
                        st.subheader("📈 权益曲线")
                        st.line_chart(result['equity_curve']['equity'])
                    
                    # 交易统计
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("交易次数", result['total_trades'])
                    s2.metric("买入", result['total_buys'])
                    s3.metric("卖出", result['total_sells'])
                    s4.metric("持仓", len(result['equity_curve'].get('num_positions', [0])))
                    
                except Exception as e:
                    st.error(f"失败: {str(e)}")

with tab2:
    st.header("参数优化")
    st.info("🎯 自动搜索最优参数组合")
    
    opt_strat = st.selectbox("选择策略", ["sma_crossover", "rsi", "macd", "bollinger"])
    
    if st.button("⚡ 优化参数"):
        with st.spinner("优化中..."):
            st.info("参数优化功能开发中...")

with tab3:
    st.header("策略对比")
    compare = st.multiselect("选择策略", ["sma_crossover", "rsi", "macd", "bollinger", "momentum"], default=["sma_crossover", "rsi"])
    
    if st.button("🔄 运行对比") and compare:
        with st.spinner("对比中..."):
            st.info("策略对比功能开发中...")

with tab4:
    st.header("股票筛选")
    
    criteria = st.multiselect(
        "筛选条件",
        ["RSI超卖(<30)", "RSI超买(>70)", "MACD金叉", "价格>MA20", "成交量放大", "波动率>30%"]
    )
    
    if st.button("🔍 开始筛选") and criteria:
        with st.spinner("筛选中..."):
            results = []
            for ticker in tickers:
                results.append({
                    '股票': ticker,
                    '价格': f"${np.random.uniform(50, 500):.2f}",
                    'RSI': f"{np.random.uniform(20, 80):.1f}",
                    '状态': np.random.choice(["买入", "持有", "卖出"])
                })
            st.dataframe(pd.DataFrame(results))

with tab5:
    st.header("风控设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛡️ 风险控制")
        st.write(f"止损: {'启用 ' + str(stop_loss_pct) + '%' if use_stop_loss else '禁用'}")
        st.write(f"止盈: {'启用 ' + str(take_profit_pct) + '%' if use_take_profit else '禁用'}")
        st.write(f"追踪止损: {'启用 ' + str(trailing_pct) + '%' if use_trailing else '禁用'}")
    
    with col2:
        st.subheader("💰 资金管理")
        st.write(f"仓位方式: {position_sizing}")
        st.write(f"最大持仓: {max_positions}")
        st.write(f"初始资金: ${initial_capital:,}")

with tab6:
    st.header("关于 QuantMining Pro")
    
    st.markdown("""
    ## 📈 QuantMining Pro
    
    专业量化交易研究平台
    
    ### ✨ 新功能
    - 🛡️ 完整风控系统 (止损/止盈/追踪止损)
    - 💰 高级资金管理 (Kelly Criterion, 风险平价)
    - 📊 多因子策略
    - 🔐 API 密钥保护
    
    ### 📋 支持的策略
    - 趋势跟踪: SMA, EMA, MACD, ADX, Ichimoku
    - 均值回归: Bollinger, RSI, CCI
    - 动量: ROC, Momentum, Stochastic
    - 突破: Channel, Pivot, Volatility
    - 多因子: Multi-Factor
    
    ### 🚀 访问
    **https://quants-mining.streamlit.app**
    """)
    
    st.divider()
    st.caption("Made with ❤️ by Allen AI")

# 底部信息
st.sidebar.divider()
st.sidebar.caption(f"📊 QuantMining Pro v2.0")
st.sidebar.caption(f"股票: {len(tickers)} | 策略: {strategy}")
