"""
多数据源支持
免费股票 API 集成
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List
import logging
import time

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源基类"""
    
    @abstractmethod
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        pass
    
    @abstractmethod
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        pass


class YahooDataSource(DataSource):
    """Yahoo Finance 数据源"""
    
    def __init__(self):
        self.name = "Yahoo Finance"
    
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        import yfinance as yf
        
        for attempt in range(3):
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period=period, interval=interval)
                
                if not df.empty:
                    df['ticker'] = ticker.upper()
                    return df
                    
            except Exception as e:
                if "rate limit" in str(e).lower():
                    time.sleep(2 * (attempt + 1))
                    continue
                logger.warning(f"Yahoo fetch failed for {ticker}: {e}")
        
        return pd.DataFrame()
    
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        import yfinance as yf
        
        try:
            data = yf.download(tickers, period=period, progress=False)
            if len(tickers) == 1:
                data = data.to_df()
                data['ticker'] = tickers[0].upper()
            return data
        except Exception as e:
            logger.warning(f"Yahoo fetch multiple failed: {e}")
            return pd.DataFrame()


class AlphaVantageDataSource(DataSource):
    """Alpha Vantage 数据源 (免费 API)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Alpha Vantage
        
        免费用户: 5 API calls/min, 500 calls/day
        免费 API key: 'demo' (仅限部分股票)
        """
        self.api_key = api_key or "demo"
        self.base_url = "https://www.alphavantage.co/query"
        self.name = "Alpha Vantage"
        self._rate_limit()
    
    def _rate_limit(self):
        """简单限速"""
        self.last_call = 0
        self.min_interval = 12  # 12秒间隔 (5 calls/min)
    
    def _wait(self):
        """等待间隔"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()
    
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        import requests
        
        self._wait()
        
        # 转换为 Alpha Vantage 参数
        function = "TIME_SERIES_DAILY" if interval == "1d" else "TIME_SERIES_INTRADAY"
        
        params = {
            "function": function,
            "symbol": ticker,
            "outputsize": "full" if period in ["2y", "5y", "10y"] else "compact",
            "apikey": self.api_key
        }
        
        if interval != "1d":
            params["interval"] = interval
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            # 解析数据
            if "Time Series (Daily)" in data:
                ts = data["Time Series (Daily)"]
                df = pd.DataFrame.from_dict(ts, orient="index")
                df.columns = ["open", "high", "low", "close", "volume"]
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df["ticker"] = ticker.upper()
                
                # 过滤日期
                if period:
                    days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days.get(period, 365))
                    df = df[df.index >= cutoff]
                
                return df
            else:
                logger.warning(f"Alpha Vantage no data for {ticker}: {data.get('Note', data.get('Error', 'Unknown'))}")
                
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
        
        return pd.DataFrame()
    
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        all_data = []
        for ticker in tickers:
            df = self.fetch(ticker, period)
            if not df.empty:
                all_data.append(df)
            time.sleep(2)  # 避免太快
        
        if not all_data:
            return pd.DataFrame()
        
        return pd.concat(all_data)


class PolygonDataSource(DataSource):
    """Polygon.io 数据源 (免费 API)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Polygon.io
        
        免费用户: 5 API calls/min
        """
        self.api_key = api_key or "demo"
        self.base_url = "https://api.polygon.io/v2"
        self.name = "Polygon.io"
    
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        import requests
        
        # 转换周期
        multiplier, timespan = {"1d": (1, "day"), "1h": (1, "hour"), "5m": (5, "minute")}.get(interval, (1, "day"))
        
        # 计算日期
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        from_date = pd.Timestamp.now() - pd.Timedelta(days=days.get(period, 365))
        
        url = f"{self.base_url}/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date.strftime('%Y-%m-%d')}/{pd.Timestamp.now().strftime('%Y-%m-%d')}"
        
        params = {"adjusted": "true", "apiKey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if "results" in data:
                df = pd.DataFrame(data["results"])
                df['ticker'] = ticker.upper()
                
                # 重命名列
                df = df.rename(columns={
                    'o': 'Open', 'h': 'High', 'l': 'Low', 
                    'c': 'Close', 'v': 'Volume', 't': 'Date'
                })
                df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                df = df.set_index('Date')
                
                return df[['Open', 'High', 'Low', 'Close', 'Volume', 'ticker']]
                
        except Exception as e:
            logger.warning(f"Polygon failed for {ticker}: {e}")
        
        return pd.DataFrame()
    
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        all_data = []
        for ticker in tickers:
            df = self.fetch(ticker, period)
            if not df.empty:
                all_data.append(df)
        
        return pd.concat(all_data) if all_data else pd.DataFrame()


class FinnhubDataSource(DataSource):
    """Finnhub 数据源 (免费 API)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Finnhub
        
        免费用户: 60 API calls/min
        """
        self.api_key = api_key or "demo"
        self.base_url = "https://finnhub.io/api/v1"
        self.name = "Finnhub"
    
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        import requests
        
        # 转换周期
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        to_date = int(pd.Timestamp.now().timestamp())
        from_date = int((pd.Timestamp.now() - pd.Timedelta(days=days.get(period, 365))).timestamp())
        
        url = f"{self.base_url}/stock/candle"
        params = {
            "symbol": ticker,
            "resolution": "D" if interval == "1d" else "60",
            "from": from_date,
            "to": to_date,
            "token": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("s") == "ok":
                df = pd.DataFrame({
                    "Open": data["o"],
                    "High": data["h"],
                    "Low": data["l"],
                    "Close": data["c"],
                    "Volume": data["v"]
                }, index=pd.to_datetime(data["t"], unit="s"))
                df["ticker"] = ticker.upper()
                
                return df
                
        except Exception as e:
            logger.warning(f"Finnhub failed for {ticker}: {e}")
        
        return pd.DataFrame()
    
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        all_data = []
        for ticker in tickers:
            df = self.fetch(ticker, period)
            if not df.empty:
                all_data.append(df)
        
        return pd.concat(all_data) if all_data else pd.DataFrame()


class MockDataSource(DataSource):
    """模拟数据源 (用于测试)"""
    
    def __init__(self):
        from src.data.mock import generate_mock_data
        self.name = "Mock Data"
        self._generator = generate_mock_data
    
    def fetch(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=days.get(period, 365))).strftime("%Y-%m-%d")
        
        df = self._generator(ticker, start_date=start_date)
        return df
    
    def fetch_multiple(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        from src.data.mock import generate_multiple_stocks
        
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=days.get(period, 365))).strftime("%Y-%m-%d")
        
        return generate_multiple_stocks(tickers, start_date=start_date)


class DataSourceFactory:
    """数据源工厂"""
    
    _sources = {
        'yahoo': YahooDataSource,
        'alphavantage': AlphaVantageDataSource,
        'polygon': PolygonDataSource,
        'finnhub': FinnhubDataSource,
        'mock': MockDataSource,
    }
    
    @classmethod
    def create(cls, source: str = 'mock', **kwargs) -> DataSource:
        """
        创建数据源
        
        Args:
            source: 数据源名称 ('yahoo', 'alphavantage', 'polygon', 'finnhub', 'mock')
            **kwargs: 传递给数据源的参数
            
        Returns:
            DataSource 实例
        """
        if source not in cls._sources:
            raise ValueError(f"Unknown data source: {source}. Available: {list(cls._sources.keys())}")
        
        return cls._sources[source](**kwargs)
    
    @classmethod
    def list_sources(cls) -> List[str]:
        """列出所有可用数据源"""
        return list(cls._sources.keys())


# 默认使用 Mock 数据源
default_source = DataSourceFactory.create('mock')


if __name__ == "__main__":
    # 测试数据源
    print("Available data sources:", DataSourceFactory.list_sources())
    
    # 测试 Mock
    source = DataSourceFactory.create('mock')
    df = source.fetch("AAPL", period="1mo")
    print(f"\nMock data:\n{df.head()}")
