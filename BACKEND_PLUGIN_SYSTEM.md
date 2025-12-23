# Ticker Data Backend Plugin System

## Overview

XLTickers now has a **modular, pluggable architecture** for ticker data sources. This allows:

- 🔌 **Add new data sources** without modifying core code
- 🔄 **Switch between backends** at runtime
- 🚀 **Fallback chains** for reliability
- 🧩 **Custom implementations** for specialized use cases

## Architecture

### Core Components

```
core/
├── backends.py          # Plugin base classes and manager
├── ticker_fetcher.py    # Current Yahoo Finance implementation
└── (future backends)
    ├── alpha_vantage.py
    ├── polygon_io.py
    └── custom_backend.py
```

### Key Classes

**`TickerBackend`** - Abstract base class
- All data sources extend this class
- Implements consistent interface
- Handles errors gracefully

**`TickerData`** - Standard data format
- Consistent return type from all backends
- Contains: symbol, price, date, source, metadata

**`BackendManager`** - Orchestrates backends
- Registers/unregisters backends
- Sets primary backend
- Implements fallback chains

## How It Works

### 1. Simple Usage (Current)

```python
from core.backends import get_backend_manager

manager = get_backend_manager()
data, error = manager.get_price('AAPL')

if data:
    print(f"{data.symbol}: ${data.price} ({data.source})")
else:
    print(f"Error: {error}")
```

### 2. Multiple Backends

```python
# Register multiple backends
manager.register(yahoo_backend)
manager.register(alpha_vantage_backend)
manager.register(polygon_backend)

# Set primary
manager.set_primary('yahoo_finance')

# Try fallbacks if primary fails
data, error = manager.get_price_with_fallback(
    'AAPL',
    fallback_order=['yahoo_finance', 'alpha_vantage', 'polygon_io']
)
```

### 3. Creating a New Backend

```python
from core.backends import TickerBackend, TickerData
from datetime import date

class AlphaVantageBackend(TickerBackend):
    
    @property
    def name(self) -> str:
        return 'alpha_vantage'
    
    @property
    def description(self) -> str:
        return 'Alpha Vantage API (with API key)'
    
    def initialize(self, config: dict) -> None:
        """Config needs: {'api_key': 'YOUR_KEY'}"""
        if 'api_key' not in config:
            raise ValueError("Alpha Vantage requires 'api_key' in config")
        self.api_key = config['api_key']
    
    def is_available(self) -> bool:
        return hasattr(self, 'api_key') and self.api_key
    
    def get_price(self, symbol: str):
        try:
            # Call Alpha Vantage API
            response = requests.get(
                'https://www.alphavantage.co/query',
                params={
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
            )
            
            data = response.json()
            price = float(data['Global Quote']['05. price'])
            
            return TickerData(
                symbol=symbol,
                price=price,
                date=date.today(),
                source='alpha_vantage'
            ), None
        
        except Exception as e:
            return None, str(e)
```

## Benefits

### For Current Development
- ✅ Cleaner code structure
- ✅ Easy to test individual backends
- ✅ Fallback support for reliability

### For Future Features
- ✅ Add crypto support (Coingecko)
- ✅ Add forex support (OANDA)
- ✅ Add custom API support
- ✅ User-defined backends
- ✅ Backend switching in GUI settings

## Implementation Plan

### Phase 1 (Current)
- ✅ Backend base classes and manager
- ✅ Update ticker_fetcher.py to implement TickerBackend
- ✅ Modular update system (separate concern)

### Phase 2 (GUI Release)
- 🔜 Backend selection UI
- 🔜 Configuration per-backend in settings
- 🔜 Show data source in results
- 🔜 Manual backend switching

### Phase 3 (Future)
- 🔜 Alpha Vantage backend
- 🔜 Polygon.io backend
- 🔜 Custom backend template
- 🔜 Backend performance metrics

## Migration Path

### Current Code
```python
from core.ticker_fetcher import get_ticker_price

success, price, date, error = get_ticker_price('AAPL')
```

### New Code (Same interface!)
```python
from core.ticker_fetcher import get_ticker_price

success, price, date, error = get_ticker_price('AAPL')
# Internally uses backends now, no change needed
```

The migration is **transparent** - existing code continues to work while we build the modular system.

## Testing

Each backend should include tests:

```python
def test_backend_available():
    backend = MyBackend()
    backend.initialize(config)
    assert backend.is_available()

def test_backend_get_price():
    backend = MyBackend()
    backend.initialize(config)
    data, error = backend.get_price('AAPL')
    assert data is not None
    assert error is None
    assert data.price > 0
```

## Configuration

Store backend configuration in `config.ini`:

```ini
[BACKENDS]
primary = yahoo_finance
fallback = alpha_vantage,polygon_io

[TICKER_SOURCES]
yahoo_finance_enabled = true
alpha_vantage_enabled = false
alpha_vantage_api_key = YOUR_KEY_HERE
polygon_io_enabled = false
polygon_io_api_key = YOUR_KEY_HERE
```

## Future Considerations

1. **Rate limiting** - Handle API throttling per backend
2. **Caching** - Cache prices to reduce API calls
3. **Performance** - Parallel requests to multiple backends
4. **Analytics** - Track which backend works best per ticker
5. **User feedback** - Report issues with backends

---

This architecture makes XLTickers flexible and extensible for years to come!
