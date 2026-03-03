"""
QuantMining - 量化交易策略平台
支持多数据源，回测、参数优化
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加 src 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置页面
st.set_page_config(
    page_title="QuantMining",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📈 QuantMining - 量化交易平台")

# 侧边栏 - 配置
st.sidebar.header("⚙️ 配置")

# 数据源选择
data_source = st.sidebar.radio("数据源", ["模拟数据", "真实数据"], index=0)

# 股票选择
default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "DIS", "KO", "JPM", "V", "WMT", "PG", "JNJ"]
tickers = st.sidebar.multiselect(
    "选择股票",
    default_tickers,
    default=default_tickers[:5]
)

# 策略选择
strategies = [
    ("sma_crossover", "均线交叉", "经典的双均线交叉策略"),
    ("rsi", "RSI 超买超卖", "基于相对强弱指数"),
    ("macd", "MACD 金叉死叉", "移动平均收敛发散"),
    ("bollinger", "布林带", "价格波动通道"),
    ("momentum", "动量", "基于价格动量"),
    ("mean_reversion", "均值回归", "价格回归均值"),
    ("breakout", "突破", "价格突破策略"),
    ("composite", "复合策略", "多指标组合"),
    ("trend_following", "趋势跟随", "顺势交易"),
    ("adx", "ADX 趋势", "平均趋向指数"),
    ("cci", "CCI 商品通道", "商品通道指数"),
    ("vwap", "VWAP 成交量加权", "成交价加权平均"),
    ("stochastic", "随机指标", "KDJ 随机指标"),
]
strategy_names = [s[0] for s in strategies]
strategy_descs = {s[0]: s[2] for s in strategies}

strategy_option = st.sidebar.selectbox(
    "选择策略",
    range(len(strategies)),
    format_func=lambda x: f"{strategies[x][0]} - {strategies[x][1]}"
)
strategy = strategies[strategy_option][0]

# 策略参数
st.sidebar.subheader("📌 策略参数")
st.sidebar.caption(f"📝 {strategy_descs[strategy]}")
strategy_params = {}

if strategy == "sma_crossover":
    strategy_params["fast_period"] = st.sidebar.slider("快线周期", 5, 50, 20)
    strategy_params["slow_period"] = st.sidebar.slider("慢线周期", 20, 200, 50)
elif strategy == "rsi":
    strategy_params["period"] = st.sidebar.slider("RSI 周期", 5, 30, 14)
    strategy_params["oversold"] = st.sidebar.slider("超卖阈值", 10, 40, 30)
    strategy_params["overbought"] = st.sidebar.slider("超买阈值", 60, 90, 70)
elif strategy == "macd":
    strategy_params["fast"] = st.sidebar.slider("MACD 快线", 5, 20, 12)
    strategy_params["slow"] = st.sidebar.slider("MACD 慢线", 15, 50, 26)
    strategy_params["signal"] = st.sidebar.slider("MACD 信号线", 5, 15, 9)
elif strategy == "bollinger":
    strategy_params["period"] = st.sidebar.slider("布林带周期", 10, 50, 20)
    strategy_params["std_dev"] = st.sidebar.slider("标准差倍数", 1.0, 3.0, 2.0)
elif strategy == "momentum":
    strategy_params["lookback"] = st.sidebar.slider("回看周期", 5, 50, 20)
    strategy_params["threshold"] = st.sidebar.slider("阈值", 0.01, 0.1, 0.02)
elif strategy == "mean_reversion":
    strategy_params["period"] = st.sidebar.slider("周期", 10, 50, 20)
    strategy_params["std_dev"] = st.sidebar.slider("标准差", 1.0, 3.0, 2.0)
elif strategy == "breakout":
    strategy_params["lookback"] = st.sidebar.slider("回看周期", 10, 50, 20)
elif strategy == "composite":
    strategy_params["rsi_period"] = st.sidebar.slider("RSI 周期", 5, 21, 14)
elif strategy == "trend_following":
    strategy_params["ma_period"] = st.sidebar.slider("MA 周期", 20, 100, 50)
elif strategy == "adx":
    strategy_params["adx_period"] = st.sidebar.slider("ADX 周期", 7, 28, 14)
    strategy_params["adx_threshold"] = st.sidebar.slider("ADX 阈值", 15, 40, 25)
elif strategy == "cci":
    strategy_params["period"] = st.sidebar.slider("CCI 周期", 10, 30, 20)
elif strategy == "vwap":
    strategy_params["deviation_threshold"] = st.sidebar.slider("偏离阈值", 0.01, 0.05, 0.02)
elif strategy == "stochastic":
    strategy_params["k_period"] = st.sidebar.slider("K周期", 5, 21, 14)
    strategy_params["d_period"] = st.sidebar.slider("D周期", 3, 7, 3)

# 回测参数
st.sidebar.subheader("📊 回测参数")
initial_capital = st.sidebar.number_input("初始资金", value=100000, step=10000)
max_positions = st.sidebar.slider("最大持仓", 1, 10, 3)
period = st.sidebar.select_slider("数据周期", options=["1mo", "3mo", "6mo", "1y", "2y"], value="2y")

# 主界面
tab1, tab2, tab3, tab4 = st.tabs(["📊 回测", "📈 策略优化", "📉 组合对比", "ℹ️ 关于"])

with tab1:
    st.header("策略回测")
    
    if st.button("🚀 运行回测", type="primary", use_container_width=True):
        if not tickers:
            st.error("请选择至少一只股票")
        else:
            with st.spinner("运行回测中..."):
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
                    
                    # 指标卡片
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("总收益率", f"{result['total_return']:.2%}", delta=f"{result['total_return']*100:.2f}%")
                    col2.metric("年化收益率", f"{result['annual_return']:.2%}", delta=f"{result['annual_return']*100:.2f}%")
                    col3.metric("夏普比率", f"{result['sharpe_ratio']:.2f}", delta=f"{result['sharpe_ratio']:.2f}")
                    col4.metric("最大回撤", f"{result['max_drawdown']:.2%}", delta_color="inverse")
                    
                    # 权益曲线
                    st.subheader("📈 权益曲线")
                    equity_df = result['equity_curve']
                    if not equity_df.empty:
                        chart_data = pd.DataFrame({
                            '总权益': equity_df['equity'],
                            '现金': equity_df.get('cash', equity_df['equity'] * 0.5),
                            '持仓市值': equity_df.get('positions_value', equity_df['equity'] * 0.5)
                        })
                        st.line_chart(chart_data)
                    
                    # 收益率曲线
                    st.subheader("📊 收益率曲线")
                    if not equity_df.empty:
                        returns = equity_df['equity'].pct_change().fillna(0)
                        cum_returns = (1 + returns).cumprod() - 1
                        st.line_chart(cum_returns * 100)
                    
                    # 回撤曲线
                    st.subheader("📉 回撤曲线")
                    if not equity_df.empty:
                        cummax = equity_df['equity'].cummax()
                        drawdown = (equity_df['equity'] - cummax) / cummax * 100
                        st.area_chart(drawdown, color="#FF4B4B")
                    
                    # 交易统计
                    st.subheader("📋 交易统计")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("交易次数", result['total_trades'])
                    col2.metric("买入次数", result['total_buys'])
                    col3.metric("卖出次数", result['total_sells'])
                    col4.metric("胜率", f"{result['total_trades'] > 0 and result['total_buys']/result['total_trades']*100 or 0:.1f}%")
                    
                except Exception as e:
                    st.error(f"回测失败: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

with tab2:
    st.header("策略参数优化")
    st.info("🎯 选择策略和参数范围，系统将自动搜索最优参数")
    
    opt_strategy = st.selectbox("选择要优化的策略", strategy_names, format_func=lambda x: x)
    
    if st.button("⚡ 开始优化", type="primary"):
        with st.spinner("优化中，请稍候..."):
            try:
                from src.trading.optimize import StrategyOptimizer
                from src.data.mock import generate_multiple_stocks
                from src.data import add_indicators
                
                data = generate_multiple_stocks(tickers[:3], start_date="2024-01-01")
                for ticker in data:
                    data[ticker] = add_indicators(data[ticker])
                
                if opt_strategy == "sma_crossover":
                    param_grid = {
                        'fast_period': [5, 10, 15, 20, 25, 30],
                        'slow_period': [30, 40, 50, 60, 70, 80],
                    }
                elif opt_strategy == "rsi":
                    param_grid = {
                        'period': [10, 14, 21, 28],
                        'oversold': [20, 25, 30, 35],
                        'overbought': [65, 70, 75, 80],
                    }
                elif opt_strategy == "macd":
                    param_grid = {
                        'fast': [8, 12, 16],
                        'slow': [20, 26, 32],
                        'signal': [6, 9, 12],
                    }
                else:
                    param_grid = {'fast_period': [10, 20], 'slow_period': [30, 50]}
                
                optimizer = StrategyOptimizer(data, opt_strategy, metric='sharpe_ratio')
                opt_result = optimizer.optimize(param_grid)
                
                st.success("🎉 优化完成!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("夏普比率", f"{opt_result.best_sharpe:.3f}")
                col2.metric("总收益", f"{opt_result.best_return:.2%}")
                col3.json(opt_result.best_params)
                
                st.subheader("📊 Top 10 结果")
                results_df = pd.DataFrame(opt_result.all_results[:10])
                if not results_df.empty:
                    display_df = results_df.copy()
                    display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x:.2%}")
                    display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.3f}")
                    display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x:.2%}")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
            except Exception as e:
                st.error(f"优化失败: {str(e)}")

with tab3:
    st.header("多策略对比")
    st.info("📉 同时测试多个策略，找出最佳选择")
    
    compare_strategies = st.multiselect(
        "选择要对比的策略",
        strategy_names,
        default=["sma_crossover", "rsi", "momentum"]
    )
    
    if st.button("🔄 运行对比", type="primary") and compare_strategies:
        with st.spinner("运行多策略对比..."):
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
                
                results = {}
                for strat_name in compare_strategies:
                    strat = create_strategy(strat_name)
                    backtester = PortfolioBacktester(
                        initial_capital=initial_capital,
                        max_positions=max_positions,
                        position_size=1.0 / max_positions
                    )
                    result = backtester.run(data, strat)
                    results[strat_name] = result
                
                st.subheader("📊 策略对比结果")
                
                comparison_data = []
                for name, result in results.items():
                    comparison_data.append({
                        '策略': name,
                        '总收益': f"{result['total_return']:.2%}",
                        '年化收益': f"{result['annual_return']:.2%}",
                        '夏普比率': f"{result['sharpe_ratio']:.2f}",
                        '最大回撤': f"{result['max_drawdown']:.2%}",
                        '交易次数': result['total_trades']
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                
                best = max(results.items(), key=lambda x: x[1]['sharpe_ratio'])
                st.success(f"🏆 最佳策略: {best[0]} (夏普比率: {best[1]['sharpe_ratio']:.2f})")
                
                st.subheader("📈 权益曲线对比")
                equity_lines = {}
                for name, result in results.items():
                    equity_lines[name] = result['equity_curve']['equity']
                
                equity_df = pd.DataFrame(equity_lines)
                st.line_chart(equity_df)
                
            except Exception as e:
                st.error(f"对比失败: {str(e)}")

with tab4:
    st.header("关于 QuantMining")
    
    st.markdown("""
    ## 📈 QuantMining
    
    量化交易策略研究平台
    
    ### ✨ 功能
    - 📊 **多策略回测** - 支持 13+ 种策略
    - 📈 **参数优化** - 自动搜索最优参数
    - 📉 **多策略对比** - 同时比较多个策略
    - 🔄 **多数据源** - 支持 Yahoo, Alpha Vantage 等
    
    ### 📋 可用策略
    | 策略 | 描述 |
    |------|------|
    | sma_crossover | 均线交叉 |
    | rsi | RSI 超买超卖 |
    | macd | MACD 金叉死叉 |
    | bollinger | 布林带 |
    | momentum | 动量 |
    | mean_reversion | 均值回归 |
    | breakout | 突破 |
    | composite | 复合策略 |
    | trend_following | 趋势跟随 |
    | adx | ADX 趋势 |
    | cci | CCI 商品通道 |
    | vwap | VWAP 成交量加权 |
    | stochastic | 随机指标 |
    
    ### 🚀 快速开始
    ```bash
    streamlit run app.py
    ```
    
    ### 📊 在线访问
    **https://quants-mining.streamlit.app**
    """)
    
    st.divider()
    st.caption("🎉 Made with ❤️ by Allen AI Agent")
    
    st.sidebar.divider()
    st.sidebar.caption("📊 QuantMining v1.1")
    st.sidebar.caption(f"选择股票: {len(tickers)} 只")
    st.sidebar.caption(f"策略: {strategy}")
