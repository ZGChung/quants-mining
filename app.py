"""
QuantMining - Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Try multiple ways to find src directory
possible_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)),  # Same dir as app.py
    os.path.join(os.getcwd(), 'src'),  # Current working dir
    'src',  # Relative
]

# Add all possible paths
for p in possible_paths:
    if p not in sys.path:
        sys.path.insert(0, p)

st.set_page_config(page_title="QuantMining", page_icon="📈", layout="wide")
st.title("📈 QuantMining")

# Check what's available
import_test = None
for p in ['data', 'data.mock']:
    try:
        __import__(p)
        import_test = p
        break
    except:
        pass

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
    
    params = {}
    if strategy == "sma_crossover":
        params["fast_period"] = st.slider("Fast MA", 5, 50, 20)
        params["slow_period"] = st.slider("Slow MA", 20, 200, 50)
    elif strategy == "rsi":
        params["period"] = st.slider("Period", 5, 30, 14)
    
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
                    from data.mock import generate_multiple_stocks
                    from data.indicators import add_indicators
                    from trading.strategies import create_strategy
                    from trading.backtesting import PortfolioBacktester
                    
                    days_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    days = days_map.get(period, 365)
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    strat = create_strategy(strategy, **params)
                    bt = PortfolioBacktester(capital, max_pos, 1.0/max_pos)
                    result = bt.run(data, strat)
                    
                    st.success("✅ Backtest Complete!")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Return", f"{result['total_return']:.2%}")
                    c2.metric("Annual Return", f"{result['annual_return']:.2%}")
                    c3.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                    c4.metric("Max Drawdown", f"{result['max_drawdown']:.2%}")
                    
                    if not result['equity_curve'].empty:
                        st.line_chart(result['equity_curve']['equity'])
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Coming soon!")

with tab3:
    st.header("Strategy Comparison")
    st.info("📉 Coming soon!")

with tab4:
    st.header("About")
    st.markdown("""
    ## 📈 QuantMining
    
    **https://quants-mining.streamlit.app**
    """)
    st.caption("Made with ❤️ by Allen AI")
