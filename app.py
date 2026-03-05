"""
QuantMining - Streamlit App
"""

import sys
import os

# DEBUG: Print what we detect
print("DEBUG: __file__ =", __file__ if '__file__' in dir() else "N/A")
print("DEBUG: cwd =", os.getcwd())

# CRITICAL: Setup path BEFORE importing streamlit
def setup_path():
    # Collect all candidates
    candidates = []
    if '__file__' in dir():
        candidates.append(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.getcwd())
    candidates.append("/mount/src/quants-mining")
    candidates.append("/mount/src")
    
    # Also check parent dirs
    for c in list(candidates):
        candidates.append(os.path.dirname(c))
        candidates.append(os.path.join(c, 'src'))
    
    for src in candidates:
        data_init = os.path.join(src, 'data', '__init__.py')
        trading_init = os.path.join(src, 'trading', '__init__.py')
        if os.path.exists(data_init) and os.path.exists(trading_init):
            if src not in sys.path:
                sys.path.insert(0, src)
            print(f"DEBUG: Found src at {src}")
            return src
    
    print(f"DEBUG: Candidates checked: {candidates[:5]}")
    return None

src_dir = setup_path()

# Now import everything else
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="QuantMining", page_icon="📈", layout="wide")
st.title("📈 QuantMining")

if not src_dir:
    st.error("Cannot find src directory")
    st.info(f"CWD: {os.getcwd()}")
    st.info(f"Files: {os.listdir('.') if os.path.exists('.') else 'N/A'}")
    st.stop()

# Import after path is set
try:
    from data.mock import generate_multiple_stocks
    from data.indicators import add_indicators
    from trading.strategies import create_strategy
    from trading.backtesting import PortfolioBacktester
    IMPORTS_OK = True
    st.success(f"✅ Imports OK! src={src_dir}")
except Exception as e:
    IMPORTS_OK = False
    st.error(f"Import failed: {e}")

STOCK_POOLS = {
    "Tech": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD"],
    "Finance": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
    "Consumer": ["AMZN", "TSLA", "KO", "PEP", "PG", "WMT"],
}

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
    
    st.subheader("Backtest")
    capital = st.number_input("Capital", value=100000)
    max_pos = st.slider("Max Positions", 1, 10, 3)
    period = st.select_slider("Period", ["3mo", "6mo", "1y", "2y"])

tab1, tab2, tab3, tab4 = st.tabs(["📊 Backtest", "📈 Optimize", "📉 Compare", "ℹ️ About"])

with tab1:
    st.header("Strategy Backtest")
    
    if not IMPORTS_OK:
        st.error("⚠️ Import error")
    elif st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        if not tickers:
            st.error("Please select stocks")
        else:
            with st.spinner("Running backtest..."):
                try:
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
                    import traceback
                    st.code(traceback.format_exc())

with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Coming soon!")

with tab3:
    st.header("Strategy Comparison")
    st.info("📉 Coming soon!")

with tab4:
    st.header("About")
    st.markdown("**https://quants-mining.streamlit.app**")
    st.caption("Made with ❤️ by Allen AI")
