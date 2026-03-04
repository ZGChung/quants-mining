"""
QuantMining - Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
    
    st.subheader("Backtest")
    capital = st.number_input("Capital", value=100000)
    max_pos = st.slider("Max Positions", 1, 10, 3)
    period = st.select_slider("Period", ["3mo", "6mo", "1y", "2y"])

# Main tabs
tab1, tab2 = st.tabs(["Backtest", "About"])

with tab1:
    st.header("Strategy Backtest")
    
    if st.button("Run Backtest", type="primary"):
        if not tickers:
            st.error("Please select stocks")
        else:
            with st.spinner("Running..."):
                try:
                    # Imports
                    from src.data.mock import generate_multiple_stocks
                    from src.data.indicators import add_indicators
                    from src.trading.strategies import create_strategy
                    from src.trading.backtesting import PortfolioBacktester
                    
                    # Data
                    days_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    start_date = (datetime.now() - timedelta(days=days_map.get(period, 365))).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
                    # Backtest
                    strat = create_strategy(strategy, **params)
                    bt = PortfolioBacktester(capital, max_pos, 1.0/max_pos)
                    result = bt.run(data, strat)
                    
                    st.success("Done!")
                    
                    # Metrics
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Return", f"{result['total_return']:.2%}")
                    c2.metric("Annual", f"{result['annual_return']:.2%}")
                    c3.metric("Sharpe", f"{result['sharpe_ratio']:.2f}")
                    c4.metric("Drawdown", f"{result['max_drawdown']:.2%}")
                    
                    # Chart
                    if not result['equity_curve'].empty:
                        st.line_chart(result['equity_curve']['equity'])
                        
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.markdown("""
    ## QuantMining
    
    Quantitative Trading Backtest Platform
    
    **https://quants-mining.streamlit.app**
    """)
