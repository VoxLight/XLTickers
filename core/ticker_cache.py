"""
Intelligent ticker cache with TTL (time-to-live).

Reduces redundant API calls by caching prices.
- In-memory cache for current session
- SQLite cache for persistence across runs
- TTL support (default 1 hour for prices)

Performance improvement: Huge for repeated tickers.

Usage:
    from core.ticker_cache import TickerCache
    
    cache = TickerCache(db_path='./cache/tickers.db')
    
    # Get from cache (or fetch if expired)
    price = cache.get('AAPL', fetch_func=lambda: 150.25)
    
    # Store in cache
    cache.set('AAPL', 150.25)
    
    # Check if cached
    if cache.is_cached('AAPL'):
        price = cache.get_cached('AAPL')
"""

import logging
import sqlite3
import json
from pathlib import Path
from typing import Optional, Callable, Tuple, Any
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class TickerCache:
    """
    Multi-layer ticker cache with persistence.
    
    Layers:
    1. In-memory cache (fast, session-only)
    2. SQLite cache (persistent, slower)
    """
    
    def __init__(self, db_path: str = './cache/tickers.db', ttl_hours: int = 1):
        """
        Initialize cache.
        
        Args:
            db_path: Path to SQLite database
            ttl_hours: Time-to-live for cached prices (hours)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        # In-memory cache
        self._memory_cache: dict = {}
        self._cache_lock = threading.Lock()
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ticker_prices (
                        symbol TEXT PRIMARY KEY,
                        price REAL NOT NULL,
                        date TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing cache database: {e}")
    
    def get(
        self,
        symbol: str,
        fetch_func: Optional[Callable[[], float]] = None,
        force_refresh: bool = False
    ) -> Optional[float]:
        """
        Get price from cache or fetch if expired.
        
        Args:
            symbol: Ticker symbol
            fetch_func: Function to call if cache miss
            force_refresh: Ignore cache, always fetch fresh
            
        Returns:
            Price or None if not found
        """
        # Check memory cache first
        if not force_refresh:
            price = self._get_memory(symbol)
            if price is not None:
                logger.debug(f"Cache hit (memory): {symbol}")
                return price
            
            # Check persistent cache
            price = self._get_disk(symbol)
            if price is not None:
                logger.debug(f"Cache hit (disk): {symbol}")
                self._set_memory(symbol, price)
                return price
        
        # Cache miss or force refresh - fetch new data
        if fetch_func:
            try:
                price = fetch_func()
                if price is not None:
                    self.set(symbol, price)
                return price
            except Exception as e:
                logger.error(f"Error in fetch function for {symbol}: {e}")
                return None
        
        return None
    
    def set(self, symbol: str, price: float) -> None:
        """
        Store price in cache.
        
        Args:
            symbol: Ticker symbol
            price: Price to cache
        """
        self._set_memory(symbol, price)
        self._set_disk(symbol, price)
    
    def _get_memory(self, symbol: str) -> Optional[float]:
        """Get from in-memory cache."""
        with self._cache_lock:
            return self._memory_cache.get(symbol)
    
    def _set_memory(self, symbol: str, price: float) -> None:
        """Store in in-memory cache."""
        with self._cache_lock:
            self._memory_cache[symbol] = price
    
    def _get_disk(self, symbol: str) -> Optional[float]:
        """Get from SQLite cache if not expired."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT price, expires_at FROM ticker_prices WHERE symbol = ?',
                    (symbol,)
                )
                row = cursor.fetchone()
                
                if row:
                    price, expires_at = row
                    # Check if expired
                    if datetime.fromisoformat(expires_at) > datetime.now():
                        return price
                    else:
                        # Delete expired entry
                        conn.execute('DELETE FROM ticker_prices WHERE symbol = ?', (symbol,))
                        conn.commit()
                
                return None
        except Exception as e:
            logger.error(f"Error reading from cache database: {e}")
            return None
    
    def _set_disk(self, symbol: str, price: float) -> None:
        """Store in SQLite cache with TTL."""
        try:
            now = datetime.now()
            expires_at = now + self.ttl
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO ticker_prices
                    (symbol, price, date, fetched_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    price,
                    now.strftime('%Y-%m-%d'),
                    now.isoformat(),
                    expires_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error writing to cache database: {e}")
    
    def is_cached(self, symbol: str) -> bool:
        """Check if symbol has valid cached price."""
        return self._get_memory(symbol) is not None or self._get_disk(symbol) is not None
    
    def get_cached(self, symbol: str) -> Optional[float]:
        """Get cached price without fetching."""
        return self._get_memory(symbol) or self._get_disk(symbol)
    
    def clear_memory(self) -> None:
        """Clear in-memory cache."""
        with self._cache_lock:
            self._memory_cache.clear()
    
    def clear_disk(self) -> None:
        """Clear persistent cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM ticker_prices')
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")
    
    def clear_all(self) -> None:
        """Clear both memory and disk cache."""
        self.clear_memory()
        self.clear_disk()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._cache_lock:
            memory_count = len(self._memory_cache)
        
        disk_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM ticker_prices')
                disk_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return {
            'memory_cached': memory_count,
            'disk_cached': disk_count,
            'total_cached': memory_count + disk_count,
            'db_path': str(self.db_path),
        }
