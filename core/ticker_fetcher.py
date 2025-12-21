"""
Ticker data fetching module using yfinance.

Pure business logic for fetching stock prices with caching.
Returns structured results instead of printing or modifying global state.
"""

import datetime as dt
import logging
from functools import lru_cache
from typing import Tuple, Optional, Dict, Any
from datetime import date

import yfinance as yf
import pandas as pd


logger = logging.getLogger(__name__)


class TickerError(Exception):
    """Raised when ticker operations fail."""
    pass


# Global cache for ticker data (session-level)
_TICKER_CACHE: Dict[Tuple[str, int], Tuple[float, date]] = {}


def clear_cache() -> None:
    """Clear the ticker cache. Useful for testing and manual refresh."""
    global _TICKER_CACHE
    _TICKER_CACHE.clear()
    _get_yfinance_data.cache_clear()


@lru_cache(maxsize=256)
def _get_yfinance_data(ticker: str, days_ago: int) -> Optional[pd.DataFrame]:
    """
    Fetch data from yfinance with LRU cache.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        days_ago: Number of days back to fetch from
        
    Returns:
        DataFrame with OHLC data, or None if fetch failed
    """
    try:
        # Ensure minimum of 7 days for reliable data
        fetch_days = max(days_ago, 7) if days_ago > 0 else 7
        
        start_date = dt.datetime.today() - dt.timedelta(days=fetch_days)
        end_date = dt.datetime.today()
        
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(start=start_date, end=end_date)
        
        if data.empty:
            logger.warning(f"No data returned for ticker: {ticker}")
            return None
        
        return data
    
    except Exception as e:
        logger.error(f"yfinance error for {ticker}: {e}")
        return None



def _extract_close_price(data: pd.DataFrame, rounding: int) -> float:
    """
    Extract and round closing price from DataFrame.
    
    Args:
        data: Historical price data
        rounding: Decimal places to round to
        
    Returns:
        Rounded closing price
    """
    close_price = data["Close"].iloc[0]
    return round(close_price, rounding)


def _extract_date(data: pd.DataFrame) -> date:
    """Extract date from DataFrame index."""
    return data.index.date[0]


def get_ticker_price(
    ticker: str,
    days_ago: int = 0,
    rounding: int = 4,
) -> Tuple[bool, Optional[float], Optional[date], str]:
    """
    Fetch current (or historical) stock price for a ticker.
    
    This function implements caching to avoid repeated API calls for the same
    ticker within a session. Perfect for Excel files with duplicate tickers.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days_ago: Number of days back to fetch price from. 
                 0 = today's close, 7 = 7 days ago, etc.
        rounding: Decimal places to round price to (default 4)
        
    Returns:
        Tuple of (success: bool, price: float, date: date, error_msg: str)
        
        On success: (True, 123.45, date(2025, 12, 21), "")
        On failure: (False, None, None, "Error message explaining why")
        
    Example:
        >>> success, price, update_date, error = get_ticker_price('AAPL')
        >>> if success:
        ...     print(f"AAPL is ${price} as of {update_date}")
        ... else:
        ...     print(f"Failed to fetch AAPL: {error}")
    """
    
    # Normalize ticker to uppercase
    ticker = ticker.upper().strip()
    
    # Check basic validity
    if not ticker or len(ticker) > 5:
        return (
            False,
            None,
            None,
            f"Invalid ticker format: '{ticker}' (must be 1-5 characters)"
        )
    
    # Check cache first
    cache_key = (ticker, days_ago)
    if cache_key in _TICKER_CACHE:
        cached_price, cached_date = _TICKER_CACHE[cache_key]
        logger.debug(f"Cache hit for {ticker}")
        return (True, cached_price, cached_date, "")
    
    # Fetch from yfinance
    try:
        data = _get_yfinance_data(ticker, days_ago)
        
        if data is None or data.empty:
            msg = f"No data available for ticker '{ticker}'"
            logger.warning(msg)
            return (False, None, None, msg)
        
        # Extract price and date
        price = _extract_close_price(data, rounding)
        update_date = _extract_date(data)
        
        # Store in cache
        _TICKER_CACHE[cache_key] = (price, update_date)
        
        logger.debug(f"Fetched {ticker}: ${price} on {update_date}")
        return (True, price, update_date, "")
    
    except ValueError as e:
        msg = f"Invalid ticker symbol '{ticker}': {str(e)}"
        logger.error(msg)
        return (False, None, None, msg)
    
    except TimeoutError:
        msg = f"Network timeout fetching ticker '{ticker}'"
        logger.error(msg)
        return (False, None, None, msg)
    
    except Exception as e:
        msg = f"Unexpected error fetching '{ticker}': {str(e)}"
        logger.error(msg)
        return (False, None, None, msg)


def get_multiple_ticker_prices(
    tickers: list,
    days_ago: int = 0,
    rounding: int = 4,
) -> Dict[str, Tuple[bool, Optional[float], Optional[date], str]]:
    """
    Fetch prices for multiple tickers in one call.
    
    Args:
        tickers: List of ticker symbols
        days_ago: Number of days back to fetch
        rounding: Decimal places for rounding
        
    Returns:
        Dict mapping ticker → (success, price, date, error)
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_ticker_price(ticker, days_ago, rounding)
    return results
