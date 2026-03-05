"""
QuantMining - Streamlit App
"""

import sys
import os

# Setup path
def setup_path():
    for base in [os.path.dirname(__file__), os.getcwd()]:
        for src in [os.path.join(base, 'src'), base]:
            if os.path.exists(os.path.join(src, 'data', '__init__.py')) and \
               os.path.exists(os.path.join(src, 'trading', '__init__.py')):
                if src not in sys.path:
                    sys.path.insert(0, src)
                return src
    return None

src_dir = setup_path()

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="QuantMining", page_icon="📈", layout="wide")
st.title("📈 QuantMining")

if not src_dir:
    st.error("Cannot find src directory")
    st.stop()

# Imports
try:
    from data.mock import generate_multiple_stocks
    from data.indicators import add_indicators
    from trading.strategies import create_strategy
    from trading.backtesting import PortfolioBacktester
    IMPORTS_OK = True
except Exception as e:
    IMPORTS_OK = False
    st.error(f"Import failed: {e}")

# Stock pools
STOCK_POOLS = {
    "Tech": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "CRM"],
    "Finance": ["JPM", "BAC", "GS", "MS", "C", "WFC", "V", "MA"],
    "Consumer": ["AMZN", "TSLA", "KO", "PEP", "PG", "WMT", "HD", "MCD"],
    "China": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI"],
}

ALL_STRATEGIES = [
    ("sma_crossover", "SMA Cross", "Fast/Slow MA crossover"),
    ("rsi", "RSI", "Relative Strength Index"),
    ("macd", "MACD", "Moving Average Convergence Divergence"),
    ("bollinger", "Bollinger", "Bollinger Bands"),
    ("momentum", "Momentum", "Price momentum"),
    ("mean_reversion", "Mean Rev", "Mean reversion"),
    ("breakout", "Breakout", "Channel breakout"),
]

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    pool = st.selectbox("Stock Pool", list(STOCK_POOLS.keys()))
    tickers = st.multiselect("Stocks", STOCK_POOLS[pool], default=STOCK_POOLS[pool][:3])
    
    st.subheader("🎯 Strategy")
    strategy = st.selectbox("Strategy", [s[0] for s in ALL_STRATEGIES], 
                           format_func=lambda x: f"{x} - {[s[1] for s in ALL_STRATEGIES if s[0]==x][0]}")
    
    # Strategy params
    params = {}
    if strategy == "sma_crossover":
        params["fast_period"] = st.slider("Fast MA", 5, 50, 20)
        params["slow_period"] = st.slider("Slow MA", 20, 200, 50)
    elif strategy == "rsi":
        params["period"] = st.slider("RSI Period", 5, 30, 14)
        params["oversold"] = st.slider("Oversold", 10, 40, 30)
        params["overbought"] = st.slider("Overbought", 60, 90, 70)
    elif strategy == "macd":
        params["fast_period"] = st.slider("Fast", 5, 20, 12)
        params["slow_period"] = st.slider("Slow", 15, 50, 26)
        params["signal"] = st.slider("Signal", 5, 15, 9)
    elif strategy == "bollinger":
        params["period"] = st.slider("Period", 10, 50, 20)
        params["std"] = st.slider("Std Dev", 1.0, 3.0, 2.0)
    
    st.subheader("📊 Backtest")
    capital = st.number_input("Capital ($)", value=100000, step=10000)
    max_pos = st.slider("Max Positions", 1, 10, 3)
    period = st.select_slider("Period", ["1mo", "3mo", "6mo", "1y", "2y"], value="1y")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Backtest", "📈 Optimize", "📉 Compare", "📡 Real Data", "ℹ️ About"])

# ============== BACKTEST TAB ==============
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
                    days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    days = days_map.get(period, 365)
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    data = generate_multiple_stocks(tickers, start_date=start_date)
                    for ticker in data:
                        data[ticker] = add_indicators(data[ticker])
                    
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
                    
                    # Equity curve
                    if not result['equity_curve'].empty:
                        st.subheader("📈 Equity Curve")
                        st.line_chart(result['equity_curve']['equity'])
                    
                    # Trade stats
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("Total Trades", result.get('total_trades', 0))
                    s2.metric("Win Rate", f"{result.get('win_rate', 0):.1%}")
                    s3.metric("Avg Win", f"${result.get('avg_win', 0):.2f}")
                    s4.metric("Avg Loss", f"${result.get('avg_loss', 0):.2f}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# ============== OPTIMIZE TAB ==============
with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Find optimal parameters for your strategy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        opt_strategy = st.selectbox("Strategy to Optimize", [s[0] for s in ALL_STRATEGIES])
    
    with col2:
        opt_ticker = st.selectbox("Stock", STOCK_POOLS["Tech"] + STOCK_POOLS["Finance"])
    
    # Parameter ranges
    st.subheader("Parameter Ranges")
    
    if opt_strategy == "sma_crossover":
        fast_range = st.slider("Fast MA Range", 5, 50, (10, 30))
        slow_range = st.slider("Slow MA Range", 20, 200, (40, 80))
    
    if st.button("⚡ Start Optimization", type="primary"):
        with st.spinner("Optimizing parameters..."):
            try:
                # Quick grid search
                best_return = -float('inf')
                best_params = {}
                results = []
                
                if opt_strategy == "sma_crossover":
                    for fast in range(fast_range[0], fast_range[1]+1, 5):
                        for slow in range(slow_range[0], slow_range[1]+1, 10):
                            if fast >= slow:
                                continue
                            
                            start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                            data = generate_multiple_stocks([opt_ticker], start_date=start)
                            data[opt_ticker] = add_indicators(data[opt_ticker])
                            
                            strat = create_strategy(opt_strategy, fast_period=fast, slow_period=slow)
                            bt = PortfolioBacktester(100000, 1, 1.0)
                            result = bt.run(data, strat)
                            
                            results.append({
                                'fast': fast,
                                'slow': slow,
                                'return': result['total_return'],
                                'sharpe': result['sharpe_ratio']
                            })
                            
                            if result['total_return'] > best_return:
                                best_return = result['total_return']
                                best_params = {'fast_period': fast, 'slow_period': slow}
                
                # Show results
                if results:
                    df = pd.DataFrame(results).sort_values('return', ascending=False)
                    st.success(f"✅ Best Return: {best_return:.2%}")
                    st.write("**Best Parameters:**", best_params)
                    st.dataframe(df.head(10))
                    
            except Exception as e:
                st.error(f"Error: {e}")

# ============== COMPARE TAB ==============
with tab3:
    st.header("Strategy Comparison")
    st.info("📉 Compare multiple strategies side by side")
    
    compare_ticker = st.selectbox("Stock", STOCK_POOLS["Tech"], index=0)
    compare_strategies = st.multiselect("Strategies", [s[0] for s in ALL_STRATEGIES], 
                                        default=["sma_crossover", "rsi"])
    
    if st.button("🔄 Compare Strategies", type="primary"):
        with st.spinner("Comparing..."):
            try:
                start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                data = generate_multiple_stocks([compare_ticker], start_date=start)
                data[compare_ticker] = add_indicators(data[compare_ticker])
                
                results = []
                for strat_name in compare_strategies:
                    strat = create_strategy(strat_name)
                    bt = PortfolioBacktester(100000, 1, 1.0)
                    result = bt.run(data, strat)
                    
                    results.append({
                        'Strategy': strat_name,
                        'Return': result['total_return'],
                        'Annual': result['annual_return'],
                        'Sharpe': result['sharpe_ratio'],
                        'Drawdown': result['max_drawdown'],
                        'Trades': result.get('total_trades', 0)
                    })
                
                df = pd.DataFrame(results).sort_values('Return', ascending=False)
                
                st.subheader("📊 Comparison Results")
                st.dataframe(df, use_container_width=True)
                
                # Chart
                if not df.empty:
                    st.bar_chart(df.set_index('Strategy')['Return'])
                    
            except Exception as e:
                st.error(f"Error: {e}")

# ============== REAL DATA TAB ==============
with tab4:
    st.header("Real Market Data")
    st.info("📡 Fetch real-time data from Yahoo Finance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        realtime_ticker = st.text_input("Ticker Symbol", "AAPL").upper()
    
    with col2:
        realtime_period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"])
    
    if st.button("📥 Fetch Data", type="primary"):
        with st.spinner("Fetching..."):
            try:
                from data.real import get_real_data
                
                data = get_real_data([realtime_ticker], realtime_period)
                
                if realtime_ticker in data:
                    df = data[realtime_ticker]
                    st.success(f"✅ Got {len(df)} rows for {realtime_ticker}")
                    
                    # Price chart
                    st.subheader(f"📈 {realtime_ticker} Price")
                    st.line_chart(df['Close'])
                    
                    # Data preview
                    with st.expander("Raw Data"):
                        st.dataframe(df.tail(20))
                        
                else:
                    st.error("Failed to fetch data")
                    
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())

# ============== ABOUT TAB ==============
with tab5:
    st.header("About QuantMining")
    
    st.markdown("""
    ## 📈 QuantMining
    
    **Quantitative Trading Backtest Platform**
    
    ### Features
    - 📊 **Strategy Backtesting** - Test your trading strategies
    - 📈 **Parameter Optimization** - Find optimal parameters
    - 📉 **Multi-Strategy Comparison** - Compare different approaches
    - 📡 **Real-time Data** - Fetch live market data
    
    ### Supported Strategies
    | Strategy | Description |
    |----------|-------------|
    | sma_crossover | Moving Average Crossover |
    | rsi | Relative Strength Index |
    | macd | MACD |
    | bollinger | Bollinger Bands |
    | momentum | Price Momentum |
    | mean_reversion | Mean Reversion |
    | breakout | Channel Breakout |
    
    ### Links
    - 🌐 **App**: https://quants-mining.streamlit.app
    - 💻 **GitHub**: https://github.com/ZGChung/quants-mining
    """)
    
    st.divider()
    st.caption("Made with ❤️ by Allen AI")
