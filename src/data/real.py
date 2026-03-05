"""
实时数据获取器
支持 Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time


class RealDataFetcher:
    """真实数据获取器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 60  # 缓存 60 秒
    
    def fetch(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """获取股票数据"""
        cache_key = f"{ticker}_{period}"
        now = time.time()
        
        # 检查缓存
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if now - timestamp < self.cache_duration:
                return data
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if not df.empty:
                df['ticker'] = ticker.upper()
                self.cache[cache_key] = (df, now)
                return df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        
        return None
    
    def fetch_all(self, tickers: List[str], period: str = "1y") -> dict:
        """获取多只股票"""
        data = {}
        for ticker in tickers:
            df = self.fetch(ticker, period)
            if df is not None and not df.empty:
                data[ticker] = df
            time.sleep(0.5)  # 避免请求过快
        return data
    
    def get_quote(self, ticker: str) -> dict:
        """获取实时报价"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'ticker': ticker.upper(),
                'price': info.get('currentPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_pct': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
            }
        except:
            return {'ticker': ticker.upper(), 'error': True}


# 全局实例
real_fetcher = RealDataFetcher()


def get_real_data(tickers: List[str], period: str = "1y") -> dict:
    """获取真实市场数据"""
    return real_fetcher.fetch_all(tickers, period)


if __name__ == "__main__":
    # 测试
    fetcher = RealDataFetcher()
    
    # 获取单只股票
    df = fetcher.fetch("AAPL", "1mo")
    if df is not None:
        print(f"AAPL: {len(df)} rows")
        print(df.tail())
    
    # 获取报价
    quote = fetcher.get_quote("AAPL")
    print(f"\nQuote: {quote}")
