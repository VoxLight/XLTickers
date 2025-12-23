"""
Ticker data source backend plugin system.

This module defines the interface for pluggable ticker data sources.
New backends can be added by extending the TickerBackend class.

Example implementations:
- YahooFinanceBackend (current, built-in)
- AlphaVantageBackend (future)
- PolygonBackend (future)
- CustomBackend (user-defined)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import date


@dataclass
class TickerData:
    """Standard format for ticker data returned by any backend."""
    
    symbol: str
    price: float
    date: date
    source: str  # Backend name, e.g., 'yahoo_finance'
    metadata: dict = None  # Optional: extra data from source
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TickerBackend(ABC):
    """
    Abstract base class for ticker data sources.
    
    All backends must implement this interface to be compatible with XLTickers.
    
    Design principles:
    - Single responsibility: fetch ticker data
    - Consistent interface: all return TickerData
    - Configurable: backends accept config dict
    - Resilient: handle errors gracefully
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique backend name (e.g., 'yahoo_finance', 'alpha_vantage')."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this backend."""
        pass
    
    @abstractmethod
    def initialize(self, config: dict) -> None:
        """
        Initialize backend with configuration.
        
        Args:
            config: Backend-specific config dict
            
        Raises:
            ValueError: If config is invalid
        """
        pass
    
    @abstractmethod
    def get_price(self, symbol: str) -> Tuple[Optional[TickerData], Optional[str]]:
        """
        Fetch current price for symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            Tuple of (TickerData, error_message)
            - If successful: (TickerData, None)
            - If failed: (None, error_message)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available and configured.
        
        Returns:
            True if backend can be used, False otherwise
        """
        pass


class BackendManager:
    """
    Manages multiple ticker data backends.
    
    Allows switching between backends, fallback chains, and discovery.
    """
    
    def __init__(self):
        """Initialize backend manager."""
        self._backends = {}
        self._primary_backend = None
    
    def register(self, backend: TickerBackend) -> None:
        """
        Register a new backend.
        
        Args:
            backend: Initialized TickerBackend instance
        """
        self._backends[backend.name] = backend
    
    def unregister(self, name: str) -> None:
        """Unregister a backend by name."""
        if name in self._backends:
            del self._backends[name]
    
    def set_primary(self, name: str) -> None:
        """
        Set the primary backend for data fetching.
        
        Args:
            name: Backend name to use as primary
            
        Raises:
            KeyError: If backend not registered
        """
        if name not in self._backends:
            raise KeyError(f"Backend '{name}' not registered")
        self._primary_backend = name
    
    def get_price(self, symbol: str) -> Tuple[Optional[TickerData], Optional[str]]:
        """
        Get price using primary backend.
        
        Returns:
            Tuple of (TickerData, error_message)
        """
        if not self._primary_backend:
            return None, "No primary backend configured"
        
        backend = self._backends[self._primary_backend]
        return backend.get_price(symbol)
    
    def get_price_with_fallback(
        self,
        symbol: str,
        fallback_order: Optional[list] = None
    ) -> Tuple[Optional[TickerData], Optional[str]]:
        """
        Get price using fallback chain.
        
        Tries primary first, then falls back to other backends in order.
        
        Args:
            symbol: Ticker symbol
            fallback_order: List of backend names to try in order (optional)
            
        Returns:
            Tuple of (TickerData, error_message)
        """
        if fallback_order is None:
            fallback_order = list(self._backends.keys())
        
        # Try each backend in order
        for backend_name in fallback_order:
            if backend_name not in self._backends:
                continue
            
            backend = self._backends[backend_name]
            if not backend.is_available():
                continue
            
            data, error = backend.get_price(symbol)
            if data:
                return data, None
        
        return None, "All backends failed or unavailable"
    
    def list_backends(self) -> dict:
        """
        List all registered backends.
        
        Returns:
            Dict mapping backend names to descriptions
        """
        return {
            name: backend.description
            for name, backend in self._backends.items()
        }
    
    def get_backend(self, name: str) -> Optional[TickerBackend]:
        """Get a specific backend by name."""
        return self._backends.get(name)


# Global backend manager instance
_backend_manager = None


def get_backend_manager() -> BackendManager:
    """
    Get or create the global backend manager.
    
    Returns:
        BackendManager singleton instance
    """
    global _backend_manager
    if _backend_manager is None:
        _backend_manager = BackendManager()
    return _backend_manager
