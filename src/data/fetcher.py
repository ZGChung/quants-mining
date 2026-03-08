"""
数据获取模块 - 美股数据
使用 Yahoo Finance API 获取股票数据
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataFetcher:
    """美股数据获取器"""

    def __init__(
        self, cache_dir: Optional[str] = None, retry_delay: float = 2.0, max_retries: int = 3
    ):
        """
        初始化数据获取器

        Args:
            cache_dir: 数据缓存目录
            retry_delay: 重试延迟（秒）
            max_retries: 最大重试次数
        """
        self.cache_dir = cache_dir
        self.retry_delay = retry_delay
        self.max_retries = max_retries

    def fetch(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取股票数据

        Args:
            ticker: 股票代码 (如 'AAPL', 'MSFT')
            period: 数据周期 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: 数据频率 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '1wk', '1mo')
            start: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)

        Returns:
            包含 OHLCV 数据的 DataFrame
        """
        for attempt in range(self.max_retries):
            try:
                stock = yf.Ticker(ticker)

                if start and end:
                    df = stock.history(start=start, end=end, interval=interval)
                else:
                    df = stock.history(period=period, interval=interval)

                if df.empty:
                    logger.warning(f"No data found for {ticker}")
                    return df

                # 添加 ticker 列
                df["ticker"] = ticker.upper()

                logger.info(f"Fetched {len(df)} rows for {ticker}")
                return df

            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.warning(
                            f"Rate limited for {ticker}, retrying in {wait_time}s... (attempt {attempt+1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                logger.error(f"Error fetching data for {ticker}: {e}")
                raise

        return pd.DataFrame()

    def fetch_multiple(
        self, tickers: List[str], period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取多只股票数据

        Args:
            tickers: 股票代码列表
            period: 数据周期
            interval: 数据频率

        Returns:
            合并后的 DataFrame
        """
        all_data = []

        for ticker in tickers:
            try:
                df = self.fetch(ticker, period=period, interval=interval)
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")
                continue

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data)

    def get_info(self, ticker: str) -> dict:
        """
        获取股票基本信息

        Args:
            ticker: 股票代码

        Returns:
            股票信息字典
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return {}


def example_usage():
    """示例用法"""
    fetcher = StockDataFetcher()

    # 获取单只股票
    aapl = fetcher.fetch("AAPL", period="6mo")
    print(aapl.head())

    # 获取多只股票
    stocks = fetcher.fetch_multiple(["AAPL", "MSFT", "GOOGL"], period="3mo")
    print(stocks.head())

    # 获取股票信息
    info = fetcher.get_info("AAPL")
    print(f"Current Price: {info.get('currentPrice')}")
    print(f"Market Cap: {info.get('marketCap')}")


if __name__ == "__main__":
    example_usage()
