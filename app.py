"""
QuantMining - Quantitative Trading Research Platform
A personal project exploring trading strategies, technical analysis,
and quantum approaches to portfolio optimization.
"""

import sys
import os
import json

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
st.caption("A personal deep dive into quantitative trading and quantum optimization")

if not src_dir:
    st.error("Cannot find src directory")
    st.stop()

try:
    from data.mock import generate_multiple_stocks
    from data.indicators import add_indicators
    from data.real import DataFetcher
    from trading.strategies import create_strategy, STRATEGIES
    from trading.backtesting import PortfolioBacktester
    from trading.risk import (calculate_var, calculate_cvar,
                              calculate_sortino_ratio, calculate_calmar_ratio)
    from trading.paper import PaperTrader
    from data.realtime import MarketScanner
    IMPORTS_OK = True
except Exception as e:
    IMPORTS_OK = False
    st.error(f"Import failed: {e}")

data_fetcher = DataFetcher()
API_KEYS = {}

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
    ("adx", "ADX", "ADX trend strength"),
    ("vwap", "VWAP", "Volume-weighted avg price"),
    ("obv", "OBV", "On-balance volume"),
    ("cci", "CCI", "Commodity Channel Index"),
    ("mfi", "MFI", "Money Flow Index"),
    ("williams_r", "Williams %R", "Williams %R oscillator"),
    ("stochastic", "Stochastic", "Stochastic oscillator"),
    ("multi_timeframe", "Multi TF", "Multi-timeframe MA"),
]

DATA_SOURCES = {
    "yahoo": {"name": "Yahoo Finance", "free": True, "key_required": False, "rate_limit": "~2000/day"},
    "alpha_vantage": {"name": "Alpha Vantage", "free": True, "key_required": True, "rate_limit": "25/day"},
    "finnhub": {"name": "Finnhub", "free": True, "key_required": True, "rate_limit": "60/min"},
}

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Settings")

    with st.expander("🔑 API Keys"):
        st.info("Get free API keys for premium data sources")
        alpha_key = st.text_input("Alpha Vantage Key", type="password",
                                  help="Get free key at alphavantage.co")
        finnhub_key = st.text_input("Finnhub Key", type="password",
                                   help="Get free key at finnhub.io")
        if alpha_key:
            API_KEYS['alpha_vantage'] = alpha_key
            data_fetcher.api_keys.update(API_KEYS)
            st.success("✅ Alpha Vantage key set")
        if finnhub_key:
            API_KEYS['finnhub'] = finnhub_key
            data_fetcher.api_keys.update(API_KEYS)
            st.success("✅ Finnhub key set")

    pool = st.selectbox("Stock Pool", list(STOCK_POOLS.keys()))
    tickers = st.multiselect("Stocks", STOCK_POOLS[pool], default=STOCK_POOLS[pool][:3])

    st.subheader("🎯 Strategy")
    strategy = st.selectbox("Strategy", [s[0] for s in ALL_STRATEGIES],
                           format_func=lambda x: f"{x} - {[s[1] for s in ALL_STRATEGIES if s[0]==x][0]}")

    params = {}
    if strategy == "sma_crossover":
        params["fast_period"] = st.slider("Fast MA", 5, 50, 20)
        params["slow_period"] = st.slider("Slow MA", 20, 200, 50)
    elif strategy == "rsi":
        params["period"] = st.slider("RSI Period", 5, 30, 14)
        params["oversold"] = st.slider("Oversold", 10, 40, 30)
        params["overbought"] = st.slider("Overbought", 60, 90, 70)
    elif strategy == "macd":
        params["fast"] = st.slider("Fast", 5, 20, 12)
        params["slow"] = st.slider("Slow", 15, 50, 26)
        params["signal"] = st.slider("Signal", 5, 15, 9)
    elif strategy == "bollinger":
        params["period"] = st.slider("Period", 10, 50, 20)
        params["std_dev"] = st.slider("Std Dev", 1.0, 3.0, 2.0)
    elif strategy == "momentum":
        params["lookback"] = st.slider("Lookback", 5, 60, 20)
        params["threshold"] = st.slider("Threshold", 0.01, 0.10, 0.02)
    elif strategy == "adx":
        params["adx_period"] = st.slider("ADX Period", 7, 30, 14)
        params["adx_threshold"] = st.slider("ADX Threshold", 15, 40, 25)
    elif strategy == "vwap":
        params["deviation_threshold"] = st.slider("Deviation", 0.005, 0.05, 0.02)
    elif strategy == "obv":
        params["period"] = st.slider("OBV MA Period", 10, 50, 20)
    elif strategy == "cci":
        params["period"] = st.slider("CCI Period", 10, 40, 20)
        params["oversold"] = st.slider("Oversold", -200, -50, -100)
        params["overbought"] = st.slider("Overbought", 50, 200, 100)
    elif strategy == "mfi":
        params["period"] = st.slider("MFI Period", 7, 30, 14)
        params["oversold"] = st.slider("Oversold", 10, 30, 20)
        params["overbought"] = st.slider("Overbought", 70, 90, 80)
    elif strategy == "williams_r":
        params["period"] = st.slider("Period", 7, 30, 14)
    elif strategy == "stochastic":
        params["k_period"] = st.slider("K Period", 5, 21, 14)
        params["d_period"] = st.slider("D Period", 2, 7, 3)

    st.subheader("📊 Backtest")
    capital = st.number_input("Capital ($)", value=100000, step=10000)
    max_pos = st.slider("Max Positions", 1, 10, 3)
    period = st.select_slider("Period", ["1mo", "3mo", "6mo", "1y", "2y"], value="1y")

# ---------- HELPER FUNCTIONS ----------

def get_param_ranges(strat_name):
    """Return parameter grid for optimization."""
    ranges = {
        "sma_crossover": {"fast_period": range(10, 35, 5), "slow_period": range(40, 90, 10)},
        "rsi": {"period": range(7, 22, 3), "oversold": range(20, 40, 5), "overbought": range(65, 80, 5)},
        "macd": {"fast": range(8, 16, 2), "slow": range(20, 32, 4), "signal": range(7, 13, 2)},
        "bollinger": {"period": range(15, 30, 5), "std_dev": [1.5, 2.0, 2.5]},
        "momentum": {"lookback": range(10, 35, 5), "threshold": [0.01, 0.02, 0.03, 0.05]},
        "mean_reversion": {"period": range(15, 30, 5), "std_dev": [1.5, 2.0, 2.5]},
        "breakout": {"period": range(10, 30, 5)},
        "adx": {"adx_period": range(10, 22, 4), "adx_threshold": range(20, 35, 5)},
        "vwap": {"deviation_threshold": [0.01, 0.02, 0.03, 0.05]},
        "obv": {"period": range(10, 35, 5)},
        "cci": {"period": range(14, 26, 4), "oversold": [-150, -100, -80], "overbought": [80, 100, 150]},
        "mfi": {"period": range(10, 20, 3), "oversold": [15, 20, 25], "overbought": [75, 80, 85]},
        "williams_r": {"period": range(10, 22, 4)},
        "stochastic": {"k_period": range(10, 20, 3), "d_period": [3, 5]},
        "multi_timeframe": {"short_period": range(5, 15, 3), "long_period": range(30, 60, 10)},
    }
    return ranges.get(strat_name, {})


def run_backtest(ticker_list, strat_name, strat_params, init_capital, max_positions, data_period, use_real=False):
    """Run a backtest and return the result dict."""
    days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = days_map.get(data_period, 365)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    if use_real:
        data = data_fetcher.fetch_all(ticker_list, data_period)
    else:
        data = generate_multiple_stocks(ticker_list, start_date=start_date)

    if not data:
        return None

    for t in data:
        data[t] = add_indicators(data[t])

    strat = create_strategy(strat_name, **strat_params)
    bt = PortfolioBacktester(initial_capital=init_capital, max_positions=max_positions,
                             position_size=1.0 / max_positions)
    result = bt.run(data, strat)
    return result


def display_risk_metrics(equity_curve):
    """Display risk analysis metrics from an equity curve."""
    equity = equity_curve['equity']
    returns = equity.pct_change().fillna(0)

    var95 = calculate_var(returns, 0.95)
    var99 = calculate_var(returns, 0.99)
    cvar95 = calculate_cvar(returns, 0.95)
    sortino = calculate_sortino_ratio(returns)
    calmar = calculate_calmar_ratio(returns, equity)

    with st.expander("📊 Risk Analysis"):
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("VaR 95%", f"{var95:.2%}")
        r2.metric("VaR 99%", f"{var99:.2%}")
        r3.metric("CVaR 95%", f"{cvar95:.2%}")
        r4.metric("Sortino", f"{sortino:.2f}")
        r5.metric("Calmar", f"{calmar:.2f}")


def display_export_buttons(result, prefix="backtest"):
    """Display CSV/JSON download buttons for a backtest result."""
    col1, col2 = st.columns(2)
    if result.get('equity_curve') is not None and not result['equity_curve'].empty:
        csv = result['equity_curve'].to_csv()
        col1.download_button(f"📥 Download Equity CSV", csv,
                             f"{prefix}_equity.csv", "text/csv")

    export_data = {k: v for k, v in result.items()
                   if k not in ('equity_curve', 'trades') and not isinstance(v, (pd.DataFrame, pd.Series))}
    for k, v in export_data.items():
        if isinstance(v, (np.floating, np.integer)):
            export_data[k] = float(v)
    col2.download_button(f"📥 Download Metrics JSON",
                         json.dumps(export_data, indent=2, default=str),
                         f"{prefix}_metrics.json", "application/json")


# ---------- TABS ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Backtest", "📈 Optimize", "📉 Compare",
    "💹 Paper Trade", "📡 Real Data", "⚛️ Quantum Portfolio", "ℹ️ About"
])

# ============== BACKTEST TAB ==============
with tab1:
    st.header("Strategy Backtest")

    col1, col2 = st.columns([3, 1])
    with col1:
        use_real_data = st.checkbox("Use Real Data (Yahoo)", value=False)
    with col2:
        if use_real_data:
            st.caption("📡 Yahoo Finance")

    if not IMPORTS_OK:
        st.error("⚠️ Import error")
    elif st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        if not tickers:
            st.error("Please select stocks")
        else:
            with st.spinner("Running backtest..."):
                try:
                    result = run_backtest(tickers, strategy, params, capital,
                                         max_pos, period, use_real_data)
                    if result is None:
                        st.error("Failed to fetch data")
                    else:
                        st.success("✅ Backtest Complete!")

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Total Return", f"{result['total_return']:.2%}")
                        c2.metric("Annual Return", f"{result['annual_return']:.2%}")
                        c3.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                        c4.metric("Max Drawdown", f"{result['max_drawdown']:.2%}")

                        if not result['equity_curve'].empty:
                            st.subheader("📈 Equity Curve")
                            st.line_chart(result['equity_curve']['equity'])

                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Total Trades", result.get('total_trades', 0))
                        s2.metric("Win Rate", f"{result.get('win_rate', 0):.1%}")
                        s3.metric("Avg Win", f"${result.get('avg_win', 0):.2f}")
                        s4.metric("Avg Loss", f"${result.get('avg_loss', 0):.2f}")

                        display_risk_metrics(result['equity_curve'])
                        display_export_buttons(result)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# ============== OPTIMIZE TAB ==============
with tab2:
    st.header("Parameter Optimization")
    st.info("🎯 Grid search across parameter space for any strategy")

    col1, col2 = st.columns(2)
    with col1:
        opt_strategy = st.selectbox("Strategy to Optimize", [s[0] for s in ALL_STRATEGIES],
                                    key="opt_strat")
    with col2:
        opt_ticker = st.selectbox("Stock", STOCK_POOLS["Tech"] + STOCK_POOLS["Finance"],
                                  key="opt_ticker")

    param_ranges = get_param_ranges(opt_strategy)
    if not param_ranges:
        st.warning("No parameter ranges defined for this strategy.")
    else:
        st.subheader("Parameter Space")
        range_info = ", ".join(f"{k}: {len(list(v))} values" for k, v in param_ranges.items())
        st.caption(range_info)

    if st.button("⚡ Start Optimization", type="primary") and param_ranges:
        with st.spinner("Optimizing parameters..."):
            try:
                from itertools import product as iter_product

                keys = list(param_ranges.keys())
                values = [list(v) for v in param_ranges.values()]

                best_return = -float('inf')
                best_params = {}
                results = []

                start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                base_data = generate_multiple_stocks([opt_ticker], start_date=start)
                base_data[opt_ticker] = add_indicators(base_data[opt_ticker])

                combos = list(iter_product(*values))
                progress = st.progress(0)

                for i, combo in enumerate(combos):
                    p = dict(zip(keys, combo))

                    # Skip invalid SMA combos
                    if opt_strategy == "sma_crossover" and p.get("fast_period", 0) >= p.get("slow_period", 999):
                        continue
                    if opt_strategy == "macd" and p.get("fast", 0) >= p.get("slow", 999):
                        continue

                    strat = create_strategy(opt_strategy, **p)
                    bt = PortfolioBacktester(initial_capital=100000, max_positions=1, position_size=1.0)
                    result = bt.run(base_data, strat)

                    row = dict(p)
                    row['return'] = result['total_return']
                    row['sharpe'] = result['sharpe_ratio']
                    results.append(row)

                    if result['total_return'] > best_return:
                        best_return = result['total_return']
                        best_params = p

                    progress.progress((i + 1) / len(combos))

                if results:
                    df = pd.DataFrame(results).sort_values('return', ascending=False)
                    st.success(f"✅ Best Return: {best_return:.2%}")
                    st.write("**Best Parameters:**", best_params)
                    st.dataframe(df.head(15), use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

# ============== COMPARE TAB ==============
with tab3:
    st.header("Strategy Comparison")

    compare_col1, compare_col2 = st.columns(2)
    with compare_col1:
        compare_ticker = st.selectbox("Stock", STOCK_POOLS["Tech"], index=0, key="cmp_ticker")
    with compare_col2:
        use_real_compare = st.checkbox("Use real data", value=False, key="cmp_real")

    compare_strategies = st.multiselect("Strategies", [s[0] for s in ALL_STRATEGIES],
                                        default=["sma_crossover", "rsi", "macd"])

    if st.button("🔄 Compare Strategies", type="primary"):
        with st.spinner("Comparing..."):
            try:
                days = 365
                start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                if use_real_compare:
                    data = data_fetcher.fetch_all([compare_ticker], "1y")
                else:
                    data = generate_multiple_stocks([compare_ticker], start_date=start)
                data[compare_ticker] = add_indicators(data[compare_ticker])

                results = []
                for sn in compare_strategies:
                    strat = create_strategy(sn)
                    bt = PortfolioBacktester(initial_capital=100000, max_positions=1, position_size=1.0)
                    r = bt.run(data, strat)
                    results.append({
                        'Strategy': sn,
                        'Return': r['total_return'],
                        'Annual': r['annual_return'],
                        'Sharpe': r['sharpe_ratio'],
                        'Drawdown': r['max_drawdown'],
                        'Win Rate': r.get('win_rate', 0),
                        'Trades': r.get('total_trades', 0),
                    })

                df = pd.DataFrame(results).sort_values('Return', ascending=False)
                st.subheader("📊 Comparison Results")
                st.dataframe(df, use_container_width=True)

                if not df.empty:
                    st.bar_chart(df.set_index('Strategy')['Return'])

                csv = df.to_csv(index=False)
                st.download_button("📥 Download Comparison CSV", csv,
                                   "strategy_comparison.csv", "text/csv")
            except Exception as e:
                st.error(f"Error: {e}")

# ============== PAPER TRADING TAB ==============
with tab4:
    st.header("Paper Trading Simulator")
    st.info("Simulate trading with a strategy on historical data, step by step")

    pt_col1, pt_col2, pt_col3 = st.columns(3)
    with pt_col1:
        pt_ticker = st.selectbox("Stock", STOCK_POOLS["Tech"][:5], key="pt_ticker")
    with pt_col2:
        pt_strategy = st.selectbox("Strategy", [s[0] for s in ALL_STRATEGIES[:7]], key="pt_strat")
    with pt_col3:
        pt_capital = st.number_input("Capital ($)", value=100000, step=10000, key="pt_cap")

    if st.button("▶️ Run Paper Trading", type="primary"):
        with st.spinner("Simulating trades..."):
            try:
                start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                data = generate_multiple_stocks([pt_ticker], start_date=start)
                data[pt_ticker] = add_indicators(data[pt_ticker])
                df = data[pt_ticker]

                strat = create_strategy(pt_strategy)
                trader = PaperTrader(initial_capital=pt_capital)

                portfolio_values = []
                min_history = 50

                for i in range(min_history, len(df)):
                    hist = df.iloc[:i + 1]
                    price = df['Close'].iloc[i]
                    date = df.index[i]
                    signals = strat.generate_signals(hist)

                    if date in signals.index:
                        sig = signals.loc[date]
                    else:
                        sig = 0

                    shares_held = trader.positions.get(pt_ticker, 0)
                    target_shares = int(pt_capital * 0.95 / price)

                    if sig == 1 and shares_held == 0:
                        trader.buy(pt_ticker, target_shares, price, pt_strategy)
                    elif sig == -1 and shares_held > 0:
                        trader.sell(pt_ticker, shares_held, price, pt_strategy)

                    pv = trader.get_portfolio_value({pt_ticker: price})
                    portfolio_values.append({'date': date, 'value': pv})

                pv_df = pd.DataFrame(portfolio_values).set_index('date')

                st.success(f"✅ Simulation Complete — {len(trader.orders)} orders executed")

                m1, m2, m3 = st.columns(3)
                final_val = pv_df['value'].iloc[-1] if len(pv_df) > 0 else pt_capital
                m1.metric("Final Value", f"${final_val:,.2f}")
                m2.metric("P&L", f"${final_val - pt_capital:,.2f}")
                m3.metric("Return", f"{(final_val - pt_capital) / pt_capital:.2%}")

                st.subheader("📈 Portfolio Value")
                st.line_chart(pv_df['value'])

                orders_df = trader.get_orders_df()
                if not orders_df.empty:
                    st.subheader("📋 Order Log")
                    st.dataframe(orders_df, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())

# ============== REAL DATA TAB ==============
with tab5:
    st.header("Real Market Data")

    source_col1, source_col2 = st.columns(2)
    with source_col1:
        data_source = st.selectbox("Data Source", ["yahoo", "alpha_vantage", "finnhub"],
                                   format_func=lambda x: f"{DATA_SOURCES[x]['name']} {'🔑' if DATA_SOURCES[x]['key_required'] else '✅'}")
    with source_col2:
        if data_source == "yahoo":
            st.success("✅ Free, no key required")
        else:
            st.warning(f"🔑 API key required — Rate limit: {DATA_SOURCES[data_source]['rate_limit']}")

    col1, col2 = st.columns(2)
    with col1:
        realtime_ticker = st.text_input("Ticker Symbol", "AAPL").upper()
    with col2:
        realtime_period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3,
                                       key="rt_period")

    # Quote
    st.subheader("💰 Quote")
    if st.button("📥 Get Quote", type="secondary"):
        with st.spinner("Fetching quote..."):
            try:
                quote = data_fetcher.get_quote(realtime_ticker)
                if 'error' not in quote:
                    q1, q2, q3, q4 = st.columns(4)
                    q1.metric("Price", f"${quote.get('price', 0):.2f}")
                    q2.metric("Change", f"${quote.get('change', 0):.2f}")
                    q3.metric("Change %", f"{quote.get('change_pct', 0):.2f}%")
                    q4.metric("Volume", f"{quote.get('volume', 0):,.0f}")
                else:
                    st.error("Failed to get quote")
            except Exception as e:
                st.error(f"Error: {e}")

    # Historical data
    st.subheader("📊 Historical Data")
    if st.button("📥 Fetch Historical Data", type="primary"):
        with st.spinner("Fetching..."):
            try:
                df = data_fetcher.fetch(realtime_ticker, realtime_period, data_source)
                if df is not None and not df.empty:
                    st.success(f"✅ Got {len(df)} rows for {realtime_ticker}")
                    st.line_chart(df['Close'])
                    with st.expander("Raw Data"):
                        st.dataframe(df.tail(20))
                    csv = df.to_csv()
                    st.download_button("📥 Download CSV", csv, f"{realtime_ticker}.csv", "text/csv")
                else:
                    st.error("Failed to fetch data. Check API key or ticker symbol.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Market Scanner
    st.subheader("🔍 Market Scanner")
    scan_mode = st.selectbox("Scan Mode", ["Momentum", "Volatility", "Oversold"], key="scan_mode")
    scan_pool = st.multiselect("Scan Pool", STOCK_POOLS["Tech"] + STOCK_POOLS["Finance"],
                               default=STOCK_POOLS["Tech"][:4], key="scan_pool")

    if st.button("🔎 Scan", type="secondary"):
        with st.spinner("Scanning..."):
            try:
                scanner = MarketScanner()
                if scan_mode == "Momentum":
                    results = scanner.scan_momentum(scan_pool)
                elif scan_mode == "Volatility":
                    results = scanner.scan_volatility(scan_pool)
                else:
                    results = scanner.scan_oversold(scan_pool)

                if results:
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                else:
                    st.info("No stocks matched the scan criteria.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Market status
    st.subheader("🏛️ Market Status")
    status = data_fetcher.get_market_status()
    if status['open']:
        st.success(f"🟢 Market Open — {status['time']}")
    else:
        st.warning(f"🔴 Market Closed — {status['time']}")

# ============== QUANTUM PORTFOLIO TAB ==============
with tab6:
    st.header("Quantum Portfolio Optimization")
    st.info("Compare classical Markowitz optimization with quantum (QAOA) asset selection")

    qp_tickers = st.multiselect("Assets", STOCK_POOLS["Tech"] + STOCK_POOLS["Finance"],
                                default=["AAPL", "MSFT", "GOOGL", "NVDA"], key="qp_tickers")
    qp_risk = st.slider("Risk Aversion Factor", 0.1, 2.0, 0.5, key="qp_risk")

    if st.button("⚛️ Optimize Portfolio", type="primary") and len(qp_tickers) >= 2:
        with st.spinner("Computing optimal portfolio..."):
            try:
                start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                stock_data = generate_multiple_stocks(qp_tickers, start_date=start)

                # Compute returns and covariance
                closes = pd.DataFrame({t: stock_data[t]['Close'] for t in qp_tickers})
                daily_returns = closes.pct_change().dropna()
                mu = daily_returns.mean().values * 252
                sigma = daily_returns.cov().values * 252

                from quantum.optimizers import ClassicalPortfolioOptimizer, QuantumPortfolioOptimizer

                # Classical: Markowitz
                classical_opt = ClassicalPortfolioOptimizer()
                classical_weights = classical_opt.optimize(mu, sigma)

                # Quantum: QAOA
                quantum_opt = QuantumPortfolioOptimizer(risk_factor=qp_risk)
                quantum_result = quantum_opt.optimize_with_details(mu, sigma)
                quantum_weights = quantum_result['weights']

                st.subheader("📊 Optimal Weights")
                weight_df = pd.DataFrame({
                    'Asset': qp_tickers,
                    'Classical (Markowitz)': np.round(classical_weights, 4),
                    'Quantum (QAOA)': np.round(quantum_weights, 4),
                })
                st.dataframe(weight_df, use_container_width=True)

                # Portfolio metrics comparison
                st.subheader("📈 Portfolio Comparison")
                c_ret = mu @ classical_weights
                c_vol = np.sqrt(classical_weights @ sigma @ classical_weights)
                q_ret = mu @ quantum_weights
                q_vol = np.sqrt(quantum_weights @ sigma @ quantum_weights)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Classical Return", f"{c_ret:.2%}")
                m2.metric("Classical Vol", f"{c_vol:.2%}")
                m3.metric("Quantum Return", f"{q_ret:.2%}")
                m4.metric("Quantum Vol", f"{q_vol:.2%}")

                # Weight charts
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.caption("Classical (Markowitz) Weights")
                    chart_df = pd.DataFrame({'weight': classical_weights}, index=qp_tickers)
                    st.bar_chart(chart_df)
                with chart_col2:
                    st.caption("Quantum (QAOA) Weights")
                    chart_df = pd.DataFrame({'weight': quantum_weights}, index=qp_tickers)
                    st.bar_chart(chart_df)

                # Efficient frontier
                st.subheader("🎯 Efficient Frontier")
                frontier = classical_opt.efficient_frontier(mu, sigma, n_points=30)
                frontier_df = pd.DataFrame({
                    'Volatility': frontier['volatilities'],
                    'Return': frontier['returns'],
                })
                st.line_chart(frontier_df.set_index('Volatility'))

                # QAOA details
                with st.expander("⚛️ QAOA Details"):
                    st.write(f"**Assets selected:** {int(quantum_result['n_selected'])} of {len(qp_tickers)}")
                    st.write(f"**Selection vector:** {quantum_result['selection']}")
                    st.write(f"**QUBO cost:** {quantum_result['cost']:.4f}")
                    st.write(f"**Method:** {quantum_result['method']}")

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())

# ============== ABOUT TAB ==============
with tab7:
    st.header("About QuantMining")

    st.markdown("""
    ## A Personal Deep Dive into Quantitative Trading

    I built QuantMining from scratch as a learning project to deepen my understanding
    of quantitative trading, technical analysis, and quantum computing approaches
    to portfolio optimization.

    ### What I Explored

    **Classical Trading Strategies**
    - Implemented 15 strategies from textbook indicators (SMA, RSI, MACD, Bollinger)
      to more advanced approaches (ADX trend following, VWAP, CCI, MFI, Stochastic)
    - Each strategy follows the same `Strategy` base class with `generate_signals()`

    **Backtesting & Risk Management**
    - Built a portfolio backtester handling multiple assets, position sizing,
      slippage, and commission
    - Implemented risk metrics: VaR, CVaR, Sortino ratio, Calmar ratio,
      profit factor, information ratio

    **Quantum Portfolio Optimization**
    - Formulated portfolio selection as a QUBO problem
    - Implemented QAOA circuit for combinatorial asset selection
      (classical simulation via brute-force enumeration)
    - Built variational ansatz for continuous weight optimization
    - Compared against classical Markowitz mean-variance optimization

    **Quantum Machine Learning**
    - Implemented quantum feature maps (angle encoding + ZZ entanglement)
    - Built variational quantum classifier for BUY/SELL signal prediction
    - All quantum circuits simulated classically via numpy state vectors

    **Data Engineering**
    - Multi-source data pipeline: Yahoo Finance, Alpha Vantage, Finnhub
    - 17 technical indicators with caching and rate limiting
    - Market scanner for momentum, volatility, and oversold screening

    ### Tech Stack
    | Layer | Tools |
    |-------|-------|
    | Frontend | Streamlit |
    | Data | yfinance, Alpha Vantage API, Finnhub API |
    | Computation | NumPy, Pandas, SciPy |
    | Quantum | Custom numpy simulation, optional Qiskit |
    | ML | scikit-learn, SciPy optimize |
    | CI/CD | GitHub Actions (pytest, black, flake8, mypy) |

    ### Links
    - 🌐 **Live Demo**: [quants-mining.streamlit.app](https://quants-mining.streamlit.app)
    - 💻 **Source Code**: [github.com/ZGChung/quants-mining](https://github.com/ZGChung/quants-mining)
    """)

    st.divider()
    st.caption("Built by Jayson as a personal research project")
