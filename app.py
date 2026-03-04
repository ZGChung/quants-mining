"""
QuantMining - Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
app_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(app_dir, 'src')
sys.path.insert(0, src_path)

st.set_page_config(page_title="QuantMining", page_icon="📈", layout="wide")
st.title("📈 QuantMining")

# Preset stock pools
STOCK_POOLS = {
    "Tech": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD"],
    "Finance": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
    "Consumer": ["AMZN", "TSLA", "KO", "PEP", "PG", "WMT"],
}

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    pool = st.selectbox("Stock Pool", list(STOCK_POOLS.keys()))
    tickers = st.multiselect("Stocks", STOCK_POOLS[pool], default=STOCK_POOLS[pool][:3])
    
    st.subheader("Strategy")
    strategy = st.selectbox("Strategy", ["sma_crossover", "rsi", "macd", "bollinger", "momentum"])
    
    # Parameters
    params = {}
    if strategy == "sma_crossover":
        params["fast_period"] = st.slider("Fast MA", 5, 50, 20)
        params["slow_period"] = st.slider("Slow MA", 20, 200, 50)
    elif strategy == "rsi":
        params["period"] = st.slider("Period", 5, 30, 14)
        params["oversold"] = st.slider("Oversold", 10, 40, 30)
        params["overbought"] = st.slider("Overbought", 60, 90, 70)
    
    st.subheader("Backtest")
    capital = st.number_input("Capital", value=100000)
    max_pos = st.slider("Max Positions", 1, 10, 3)
    period = st.select_slider("Period", ["3mo", "6mo", "1y", "2y"])

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Backtest", "📈 Optimize", "📉 Compare", "ℹ️ About"])

with tab1:
    st.header("Strategy Backtest")
    
    if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        if not tickers:
            st.error("Please select stocks")
        else:
            with st.spinner("Running backtest..."):
                try:
                    # Test imports first
                    from data.mock import generate_multiple_stocks
                    from data.indicators import add_indicators
                    from trading.strategies import create_strategy
                    from trading.backtesting import PortfolioBacktester
                    
                    # Data
                    days_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    days = days_map.get(period, 365)
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    # Backtest
                    strat = create_strategy(strategy, **params)
                    bt = PortfolioBacktester(capital, max_pos, 1.0/max_pos)
                    result = bt.run(data, strat)
                    
                    st.success("✅ Backtest Complete!")
                    
                    # Metrics
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Return", f"{result['total_return']:.2%}")
                    c2.metric("Annual Return", f"{result['annual_return']:.2%}")
                    c3.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                    c4.metric("Max Drawdown", f"{result['max_drawdown']:.2%}")
                    
                    # Chart
                    if not result['equity_curve'].empty:
                        st.line_chart(result['equity_curve']['equity'])
                    
                    # Trade stats
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Total Trades", result['total_trades'])
                    s2.metric("Buys", result['total_buys'])
                    s3.metric("Sells", result['total_sells'])
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Select strategy and parameter ranges to find optimal settings")
    
    opt_strategy = st.selectbox("Strategy to Optimize", ["sma_crossover", "rsi", "macd"])
    
    if st.button("⚡ Start Optimization"):
        with st.spinner("Optimizing..."):
            st.info("Optimization feature coming soon!")

with tab3:
    st.header("Strategy Comparison")
    st.info("📉 Compare multiple strategies at once")
    
    compare_strategies = st.multiselect(
        "Select Strategies", 
        ["sma_crossover", "rsi", "macd", "bollinger", "momentum"],
        default=["sma_crossover", "rsi"]
    )
    
    if st.button("🔄 Compare") and compare_strategies:
        st.info("Comparison feature coming soon!")

with tab4:
    st.header("About QuantMining")
    
    st.markdown("""
    ## 📈 QuantMining
    
    Quantitative Trading Backtest Platform
    
    ### Features
    - 📊 **Strategy Backtesting** - Test your trading strategies
    - 📈 **Parameter Optimization** - Find optimal parameters
    - 📉 **Multi-Strategy Comparison** - Compare different approaches
    
    ### Supported Strategies
    | Strategy | Description |
    |----------|-------------|
    | sma_crossover | Moving Average Crossover |
    | rsi | Relative Strength Index |
    | macd | MACD |
    | bollinger | Bollinger Bands |
    | momentum | Momentum |
    
    ### Access
    **https://quants-mining.streamlit.app**
    """)
    
    st.divider()
    st.caption("Made with ❤️ by Allen AI")
