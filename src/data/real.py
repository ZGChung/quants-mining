"""
Multi-source Data Fetcher
Supports: Yahoo Finance, Alpha Vantage, Finnhub
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Unified data fetcher with multiple source support"""

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.cache: dict = {}
        self.cache_duration = 60  # seconds

    def fetch(
        self, ticker: str, period: str = "1y", source: str = "auto"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from specified source

        Args:
            ticker: Stock symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            source: Data source (yahoo, alpha_vantage, finnhub, auto)
        """
        cache_key = f"{ticker}_{period}_{source}"

        # Check cache
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return data

        # Fetch from source
        if source == "auto":
            source = self._select_best_source(ticker)

        try:
            if source == "yahoo":
                data = self._fetch_yahoo(ticker, period)
            elif source == "alpha_vantage":
                data = self._fetch_alpha_vantage(ticker, period)
            elif source == "finnhub":
                data = self._fetch_finnhub(ticker, period)
            else:
                logger.error(f"Unknown source: {source}")
                return None

            if data is not None and not data.empty:
                data["ticker"] = ticker.upper()
                self.cache[cache_key] = (data, time.time())
                return data
        except Exception as e:
            logger.error(f"Error fetching {ticker} from {source}: {e}")

        return None

    def _select_best_source(self, ticker: str) -> str:
        """Select best available source"""
        if self.api_keys.get("alpha_vantage"):
            return "alpha_vantage"
        if self.api_keys.get("finnhub"):
            return "finnhub"
        return "yahoo"

    def _fetch_yahoo(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            return df if not df.empty else None
        except Exception as e:
            logger.error(f"Yahoo fetch error: {e}")
            return None

    def _fetch_alpha_vantage(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch from Alpha Vantage"""
        try:
            import requests

            api_key = self.api_keys.get("alpha_vantage")
            if not api_key:
                logger.warning("No Alpha Vantage API key")
                return None

            # Map period to Alpha Vantage output size
            output_size = "compact" if period in ["1d", "5d", "1mo"] else "full"

            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "outputsize": output_size,
                "apikey": api_key,
            }

            response = requests.get(url, params=params, timeout=10)  # type: ignore[arg-type]
            data = response.json()

            if "Error Message" in data or "Note" in data:
                return None

            ts_key = "Time Series (Daily)"
            if ts_key not in data:
                return None

            df = pd.DataFrame.from_dict(data[ts_key], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Alpha Vantage returns columns like "1. open"
            rename_map = {}
            for c in df.columns:
                name = c.split(". ")[-1] if ". " in c else c
                rename_map[c] = name.capitalize()
            df.rename(columns=rename_map, inplace=True)

            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col])

            # Limit to period
            days = self._period_to_days(period)
            if days:
                df = df.tail(days)

            return df

        except Exception as e:
            logger.error(f"Alpha Vantage fetch error: {e}")
            return None

    def _fetch_finnhub(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch from Finnhub"""
        try:
            import requests

            api_key = self.api_keys.get("finnhub")
            if not api_key:
                logger.warning("No Finnhub API key")
                return None

            days = self._period_to_days(period)
            end_ts = int(datetime.now().timestamp())
            start_ts = int((datetime.now() - timedelta(days=days or 365)).timestamp())

            url = f"https://finnhub.io/api/v1/stock/candle"
            params = {
                "symbol": ticker,
                "resolution": "D",  # Daily
                "from": start_ts,
                "to": end_ts,
                "token": api_key,
            }

            response = requests.get(url, params=params, timeout=10)  # type: ignore[arg-type]
            data = response.json()

            if data.get("s") != "ok":
                return None

            df = pd.DataFrame(
                {
                    "Open": data["o"],
                    "High": data["h"],
                    "Low": data["l"],
                    "Close": data["c"],
                    "Volume": data["v"],
                },
                index=pd.to_datetime(data["t"], unit="s"),
            )

            return df

        except Exception as e:
            logger.error(f"Finnhub fetch error: {e}")
            return None

    def _period_to_days(self, period: str) -> int:
        """Convert period string to days"""
        mapping = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "ytd": 365,
            "max": 3650,
        }
        return mapping.get(period, 365)

    def fetch_all(
        self, tickers: List[str], period: str = "1y", source: str = "auto"
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple tickers"""
        data = {}
        for ticker in tickers:
            df = self.fetch(ticker, period, source)
            if df is not None:
                data[ticker] = df
            time.sleep(0.5)  # Rate limiting
        return data

    def get_quote(self, ticker: str) -> Dict:
        """Get real-time quote"""
        # Try Yahoo first (most reliable for quotes)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "ticker": ticker.upper(),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "source": "yahoo",
            }
        except:
            return {"ticker": ticker.upper(), "error": True}

    def get_market_status(self) -> Dict:
        """Get US market status"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour

        # NYSE hours: 9:30 AM - 4:00 PM ET
        is_weekday = weekday < 5
        is_market_hours = 9 <= hour < 16

        return {
            "open": is_weekday and is_market_hours,
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "next_open": "09:30 ET" if not is_market_hours else "Closed",
        }


# Global instance
data_fetcher = DataFetcher()


def get_data(
    tickers: List[str], period: str = "1y", source: str = "auto"
) -> Dict[str, pd.DataFrame]:
    """Convenience function"""
    return data_fetcher.fetch_all(tickers, period, source)


def set_api_keys(api_keys: Dict[str, str]):
    """Set API keys for premium sources"""
    data_fetcher.api_keys.update(api_keys)


if __name__ == "__main__":
    # Test
    fetcher = DataFetcher()

    # Yahoo (no key needed)
    print("=== Yahoo ===")
    df = fetcher.fetch("AAPL", "1mo", "yahoo")
    print(f"AAPL: {len(df) if df is not None else 0} rows")

    # Quote
    print("\n=== Quote ===")
    quote = fetcher.get_quote("AAPL")
    print(quote)

    # Market status
    print("\n=== Market Status ===")
    status = fetcher.get_market_status()
    print(status)
