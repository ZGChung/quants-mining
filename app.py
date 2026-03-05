"""
QuantMining - Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Get the directory where app.py is located
if '__file__' in globals():
    app_dir = os.path.dirname(os.path.abspath(__file__))
else:
    app_dir = os.getcwd()

# Add src directory to path
src_dir = os.path.join(app_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

st.set_page_config(page_title="QuantMining", page_icon="📈", layout="wide")
st.title("📈 QuantMining")

# Verify path
with st.expander("Debug Info"):
    st.write(f"App dir: {app_dir}")
    st.write(f"src dir: {src_dir}")
    st.write(f"sys.path: {sys.path[:3]}")
    st.write(f"Files in src: {os.listdir(src_dir) if os.path.exists(src_dir) else 'NOT FOUND'}")

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
                    # Debug
                    st.write(f"Importing from: {src_dir}")
                    
                    # Try imports
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
                    
                    # Stats
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Total Trades", result['total_trades'])
                    s2.metric("Buys", result['total_buys'])
                    s3.metric("Sells", result['total_sells'])
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("Full Error"):
                        import traceback
                        st.code(traceback.format_exc())

with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Select strategy and parameter ranges to find optimal settings")

with tab3:
    st.header("Strategy Comparison")
    st.info("📉 Compare multiple strategies at once")

with tab4:
    st.header("About")
    st.markdown("""
    ## 📈 QuantMining
    
    Quantitative Trading Backtest Platform
    
    **https://quants-mining.streamlit.app**
    """)
    st.caption("Made with ❤️ by Allen AI")
