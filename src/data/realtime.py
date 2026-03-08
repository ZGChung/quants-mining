"""
实时数据模块
支持多种数据源
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import logging

logger = logging.getLogger(__name__)


class RealTimeData:
    """实时数据获取器"""

    def __init__(self, source: str = "yahoo"):
        self.source = source
        self.cache = {}
        self.cache_timeout = 60  # 秒

    def fetch(self, ticker: str, period: str = "1d") -> Optional[pd.DataFrame]:
        """获取实时数据"""
        cache_key = f"{ticker}_{period}"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_timeout:
                return cached_data

        # 获取数据
        if self.source == "yahoo":
            data = self._fetch_yahoo(ticker, period)
        else:
            data = self._fetch_mock(ticker, period)

        # 更新缓存
        if data is not None:
            self.cache[cache_key] = (time.time(), data)

        return data

    def _fetch_yahoo(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """从 Yahoo 获取数据"""
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval="1m" if period == "1d" else "1h")

            if not df.empty:
                df["ticker"] = ticker.upper()
                return df
        except Exception as e:
            logger.warning(f"Yahoo fetch failed: {e}")

        return self._fetch_mock(ticker, period)

    def _fetch_mock(self, ticker: str, period: str) -> pd.DataFrame:
        """生成模拟数据"""
        import numpy as np

        minutes = {"1d": 390, "5d": 390 * 5, "1mo": 390 * 22}
        n = minutes.get(period, 390)

        np.random.seed(hash(ticker) % 2**32)
        base_price = 100 + np.random.rand() * 200

        returns = np.random.normal(0.0001, 0.002, n)
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame(
            {
                "Open": prices * (1 + np.random.uniform(-0.001, 0.001, n)),
                "High": prices * (1 + np.abs(np.random.uniform(0, 0.002, n))),
                "Low": prices * (1 - np.abs(np.random.uniform(0, 0.002, n))),
                "Close": prices,
                "Volume": np.random.randint(100000, 10000000, n),
            },
            index=pd.date_range(end=datetime.now(), periods=n, freq="1min"),
        )

        df["ticker"] = ticker.upper()
        return df

    def get_quote(self, ticker: str) -> Dict:
        """获取实时报价"""
        data = self.fetch(ticker, "1d")

        if data is not None and not data.empty:
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest

            return {
                "ticker": ticker.upper(),
                "price": latest["Close"],
                "change": latest["Close"] - prev["Close"],
                "change_pct": ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100,
                "volume": latest["Volume"],
                "high": latest["High"],
                "low": latest["Low"],
                "open": latest["Open"],
                "timestamp": datetime.now().isoformat(),
            }

        return {"ticker": ticker.upper(), "price": 0, "error": "No data"}

    def get_multiple_quotes(self, tickers: List[str]) -> Dict[str, Dict]:
        """获取多只股票报价"""
        quotes = {}
        for ticker in tickers:
            quotes[ticker] = self.get_quote(ticker)
            time.sleep(0.1)  # 避免请求过快
        return quotes


class MarketScanner:
    """市场扫描器"""

    def __init__(self):
        self.data = RealTimeData()

    def scan_momentum(self, tickers: List[str], threshold: float = 0.02) -> List[Dict]:
        """扫描动量股票"""
        results = []

        for ticker in tickers:
            try:
                data = self.data.fetch(ticker, "5d")
                if data is not None and len(data) > 10:
                    returns = (data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1

                    if returns > threshold:
                        results.append(
                            {
                                "ticker": ticker,
                                "momentum": returns,
                                "price": data["Close"].iloc[-1],
                                "volume": data["Volume"].iloc[-1],
                            }
                        )
            except:
                continue

        return sorted(results, key=lambda x: x["momentum"], reverse=True)

    def scan_volatility(self, tickers: List[str], min_vol: float = 0.02) -> List[Dict]:
        """扫描高波动股票"""
        results = []

        for ticker in tickers:
            try:
                data = self.data.fetch(ticker, "5d")
                if data is not None and len(data) > 10:
                    volatility = data["Close"].pct_change().std()

                    if volatility > min_vol:
                        results.append(
                            {
                                "ticker": ticker,
                                "volatility": volatility,
                                "price": data["Close"].iloc[-1],
                            }
                        )
            except:
                continue

        return sorted(results, key=lambda x: x["volatility"], reverse=True)

    def scan_oversold(self, tickers: List[str]) -> List[Dict]:
        """扫描超卖股票 (RSI < 30)"""
        results = []

        for ticker in tickers:
            try:
                data = self.data.fetch(ticker, "1d")
                if data is not None and len(data) > 20:
                    # 简化 RSI 计算
                    delta = data["Close"].diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))

                    current_rsi = rsi.iloc[-1]

                    if current_rsi < 30:
                        results.append(
                            {"ticker": ticker, "rsi": current_rsi, "price": data["Close"].iloc[-1]}
                        )
            except:
                continue

        return sorted(results, key=lambda x: x["rsi"])


# 默认市场扫描器
scanner = MarketScanner()


if __name__ == "__main__":
    # 测试
    rt = RealTimeData()

    # 获取报价
    quotes = rt.get_multiple_quotes(["AAPL", "MSFT", "GOOGL"])
    for ticker, quote in quotes.items():
        print(f"{ticker}: ${quote['price']:.2f} ({quote['change_pct']:+.2f}%)")
