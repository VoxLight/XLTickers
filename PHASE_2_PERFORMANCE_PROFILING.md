# Phase 2: Performance Profiling & Debugging Specification

**Status**: Detailed Technical Planning  
**Date**: 2025-12-23  
**Critical Focus**: Large file handling (20MB+) and bottleneck identification

---

## Executive Summary: The Performance Problem

Users report that **large Excel files (20MB+) take an extremely long time to process**. Current system lacks visibility into *where* the time is spent:

- Is it Excel file loading?
- Is it row scanning?
- Is it yfinance API calls?
- Is it cell writing?
- Is it file saving?
- Is it something else?

**Goal**: Add comprehensive, real-time metrics collection and visualization so that:
1. **Users see detailed progress** (not just "Processing ticker #42...")
2. **Developers can pinpoint bottlenecks** (e.g., "yfinance taking 85% of time")
3. **Performance optimizations are measurable** (before/after comparison)
4. **Debug mode provides forensic data** (detailed timing for each operation)

---

## Part 1: Bottleneck Analysis (Current System)

### Known Slow Operations

#### 1. **Excel File Loading** (openpyxl)
- **Why slow**: openpyxl loads entire workbook into memory
- **Impact**: 20MB file = potentially 500K+ rows loaded
- **Metric**: Time from `load_workbook()` to `worksheet = workbook.active`
- **Current target**: < 5 seconds for 20MB file (estimated)
- **Status**: Not currently profiled

#### 2. **Row Scanning (Iteration)**
- **Why slow**: Python iteration over 500K cells, validation checks on each
- **Operation sequence**:
  ```
  for cell in worksheet[ticker_column]:
      if _is_valid_cell(cell):          # Check 1: Type validation
          cell_value = cell.value.strip() # Check 2: String processing
          _should_process_row(...)       # Check 3: Logic check
  ```
- **Impact**: ~10-50ms per 1000 cells (depends on hardware)
- **Current target**: < 2 seconds for 500K cells (estimated)
- **Status**: Not currently profiled

#### 3. **yfinance API Calls** (Per-Ticker Network I/O) ⚠️ **LIKELY WORST OFFENDER**
- **Why slow**: Network latency + API response time
- **Flow**:
  ```
  get_ticker_price(ticker)
    → _get_yfinance_data(ticker)      # [CACHED BY @lru_cache]
      → yf.Ticker(ticker)             # Object creation
      → ticker.history(start, end)    # NETWORK CALL (~500ms-2s per ticker)
      → pd DataFrame creation         # Processing
  ```
- **Key insight**: LRU cache helps for duplicates but not first occurrence
- **Impact**: 100 unique tickers × 1.5 sec avg = **2.5 minutes minimum** (network limited)
- **Current target**: Optimize network parallelization, cache hits
- **Status**: Partially optimized (caching), no parallelization

#### 4. **Cell Writing (openpyxl)**
- **Why slow**: Each `cell.value = price` triggers internal state updates
- **Operation sequence**:
  ```
  for ticker, row_num in rows_to_process:
      price_cell = worksheet[f"{price_column}{row_num}"]
      price_cell.value = price         # [EXPENSIVE - triggers updates]
      
      date_cell = worksheet[f"{date_column}{row_num}"]
      date_cell.value = excel_date    # [EXPENSIVE - triggers updates]
  ```
- **Impact**: ~1-5ms per cell write (openpyxl overhead)
- **Current target**: < 2 seconds for 1000 cell writes
- **Status**: Not currently profiled, not optimized

#### 5. **File Saving (openpyxl + Backup)**
- **Why slow**: 
  - Entire workbook serialized to XML
  - Workbook converted to ZIP archive
  - File written to disk
  - Backup process: zip/unzip
- **Operation sequence**:
  ```
  backup_manager.save_backup(workbook, file_path)
    → workbook.save(temp_path)         # XML serialization [SLOW]
    → Create backup zip                # Archive creation [SLOW]
    → Cleanup old backups              # File operations
  ```
- **Impact**: 10-30 seconds for 20MB file
- **Current target**: < 15 seconds for 20MB file
- **Status**: Not currently profiled

#### 6. **Thread Coordination Overhead** (If Multi-threaded)
- **Why slow**: Queue communication, GIL contention
- **Impact**: If added without care: 5-10% slowdown
- **Current target**: < 1% overhead for threading
- **Status**: Not yet implemented (Phase 2 will add threading)

---

## Part 2: Metrics Collection Architecture

### 2.1 Metrics Data Structures

```python
# metrics.py - Comprehensive metrics collection

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import time

@dataclass
class TimingMetric:
    """Single operation timing."""
    operation: str           # e.g., "excel_load", "row_scan", "yfinance_call"
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    
    # Additional context
    ticker: Optional[str] = None        # For ticker-specific operations
    row_number: Optional[int] = None    # For row-specific operations
    file_size_bytes: Optional[int] = None
    cache_hit: bool = False             # Was this cached?
    
    def finish(self):
        """Mark operation as complete."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
    
    def to_dict(self):
        return {
            'operation': self.operation,
            'duration_ms': round((self.duration_seconds or 0) * 1000, 2),
            'ticker': self.ticker,
            'row': self.row_number,
            'cache_hit': self.cache_hit,
            'success': self.success,
        }

@dataclass
class PerformanceMetrics:
    """Complete metrics for a processing session."""
    session_id: str                     # Unique ID for this run
    file_path: str
    file_size_bytes: int
    start_time: datetime
    
    # Aggregated timings (populated at end)
    timings: List[TimingMetric] = field(default_factory=list)
    
    # Phase timings (aggregated)
    phase_excel_load: Optional[float] = None
    phase_row_scan: Optional[float] = None
    phase_ticker_processing: Optional[float] = None
    phase_cell_writing: Optional[float] = None
    phase_file_save: Optional[float] = None
    
    # Per-operation stats
    ticker_stats: Dict[str, Dict] = field(default_factory=dict)  # Per-ticker timings
    cache_hits: int = 0
    cache_misses: int = 0
    network_calls: int = 0
    api_errors: int = 0
    cell_writes: int = 0
    rows_processed: int = 0
    
    # Hardware/System info
    system_memory_mb: Optional[float] = None
    system_cpu_percent: Optional[float] = None
    
    def total_duration_seconds(self) -> float:
        """Total processing time."""
        if not self.timings:
            return 0.0
        return self.timings[-1].end_time - self.timings[0].start_time
    
    def get_slowest_operations(self, n=10) -> List[Dict]:
        """Top N slowest operations."""
        sorted_timings = sorted(
            self.timings,
            key=lambda t: t.duration_seconds or 0,
            reverse=True
        )
        return [t.to_dict() for t in sorted_timings[:n]]
    
    def get_phase_breakdown(self) -> Dict[str, float]:
        """Percentage breakdown by phase."""
        total = self.total_duration_seconds()
        if total == 0:
            return {}
        return {
            'excel_load': (self.phase_excel_load or 0) / total * 100,
            'row_scan': (self.phase_row_scan or 0) / total * 100,
            'ticker_processing': (self.phase_ticker_processing or 0) / total * 100,
            'cell_writing': (self.phase_cell_writing or 0) / total * 100,
            'file_save': (self.phase_file_save or 0) / total * 100,
        }
    
    def get_ticker_slowest(self, n=10) -> List[Dict]:
        """Slowest tickers to fetch."""
        sorted_tickers = sorted(
            self.ticker_stats.items(),
            key=lambda x: x[1].get('total_time', 0),
            reverse=True
        )
        return [
            {
                'ticker': ticker,
                'time_ms': round(stats.get('total_time', 0) * 1000, 2),
                'attempts': stats.get('attempts', 1),
                'cache_hit': stats.get('cache_hit', False),
            }
            for ticker, stats in sorted_tickers[:n]
        ]
    
    def cache_hit_ratio(self) -> float:
        """Percentage of cache hits vs misses."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total * 100
    
    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            'session_id': self.session_id,
            'file_path': self.file_path,
            'file_size_mb': round(self.file_size_bytes / (1024 * 1024), 2),
            'total_time_seconds': round(self.total_duration_seconds(), 2),
            'phase_breakdown': self.get_phase_breakdown(),
            'slowest_operations': self.get_slowest_operations(10),
            'slowest_tickers': self.get_ticker_slowest(10),
            'cache_hit_ratio': round(self.cache_hit_ratio(), 1),
            'rows_processed': self.rows_processed,
            'network_calls': self.network_calls,
            'api_errors': self.api_errors,
        }
```

### 2.2 Global Metrics Manager

```python
# metrics_manager.py

import threading
from typing import Optional
import uuid
import json
from datetime import datetime

class MetricsManager:
    """Thread-safe metrics collection and reporting."""
    
    _instance: Optional['MetricsManager'] = None
    _lock = threading.Lock()
    _metrics: Optional[PerformanceMetrics] = None
    _current_metric: Optional[TimingMetric] = None
    
    def __init__(self):
        self._metrics = None
        self._current_metric = None
    
    @classmethod
    def get_instance(cls) -> 'MetricsManager':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MetricsManager()
        return cls._instance
    
    def start_session(self, file_path: str, file_size_bytes: int):
        """Start a new metrics session."""
        with self._lock:
            self._metrics = PerformanceMetrics(
                session_id=str(uuid.uuid4())[:8],
                file_path=file_path,
                file_size_bytes=file_size_bytes,
                start_time=datetime.now(),
            )
    
    def start_operation(self, operation: str, **context) -> TimingMetric:
        """Start timing an operation."""
        with self._lock:
            metric = TimingMetric(
                operation=operation,
                start_time=time.time(),
                **context
            )
            if self._metrics:
                self._metrics.timings.append(metric)
            return metric
    
    def record_cache_hit(self, ticker: str):
        """Record a cache hit."""
        with self._lock:
            if self._metrics:
                self._metrics.cache_hits += 1
                if ticker not in self._metrics.ticker_stats:
                    self._metrics.ticker_stats[ticker] = {}
                self._metrics.ticker_stats[ticker]['cache_hit'] = True
    
    def record_cache_miss(self, ticker: str):
        """Record a cache miss."""
        with self._lock:
            if self._metrics:
                self._metrics.cache_misses += 1
    
    def record_network_call(self, ticker: str):
        """Record a network API call."""
        with self._lock:
            if self._metrics:
                self._metrics.network_calls += 1
    
    def set_phase_timing(self, phase: str, duration_seconds: float):
        """Record total time for a processing phase."""
        with self._lock:
            if self._metrics:
                attr_name = f'phase_{phase}'
                if hasattr(self._metrics, attr_name):
                    setattr(self._metrics, attr_name, duration_seconds)
    
    def get_current_metrics(self) -> Optional[Dict]:
        """Get current session metrics as dict."""
        with self._lock:
            if self._metrics:
                return self._metrics.to_dict()
        return None
    
    def save_metrics_report(self, output_path: str):
        """Save metrics to JSON file."""
        with self._lock:
            if self._metrics:
                with open(output_path, 'w') as f:
                    json.dump(self._metrics.to_dict(), f, indent=2)
```

---

## Part 3: Integration Points (Core Module Modifications)

### 3.1 excel_processor.py Enhancement

**File**: `core/excel_processor.py`

```python
# Add metrics tracking to each phase

def process_excel(...):
    """Enhanced with comprehensive metrics."""
    
    from core.metrics_manager import MetricsManager
    
    metrics_mgr = MetricsManager.get_instance()
    metrics_mgr.start_session(file_path, os.path.getsize(file_path))
    
    # PHASE 1: File Loading
    timer = metrics_mgr.start_operation('excel_load', file_path=file_path)
    try:
        workbook = load_workbook(file_path)
        worksheet = workbook.active
    finally:
        timer.finish()
    
    # PHASE 2: Row Scanning
    timer = metrics_mgr.start_operation('row_scan', file_path=file_path)
    try:
        rows_to_process = []
        for cell in worksheet[ticker_column]:
            if _is_valid_cell(cell):
                cell_value = cell.value.strip()
                # ... logic ...
                rows_to_process.append((cell_value, cell.row))
    finally:
        timer.finish()
    
    # PHASE 3: Ticker Processing (Per-row timing)
    phase_timer_start = time.time()
    for idx, (ticker, row_num) in enumerate(rows_to_process):
        # Individual ticker timing
        ticker_timer = metrics_mgr.start_operation(
            'ticker_fetch',
            ticker=ticker,
            row_number=row_num
        )
        
        success, error_msg, price = _process_single_row(...)
        
        ticker_timer.finish()
        
        # Update metrics
        if success:
            metrics_mgr.record_cache_hit(ticker)  # Or record_cache_miss()
        
        # Progress callback includes metrics
        if progress_callback:
            current_metrics = metrics_mgr.get_current_metrics()
            progress_callback({
                'current': idx + 1,
                'total': total_rows,
                'ticker': ticker,
                'price': price,
                'phase_breakdown': current_metrics['phase_breakdown'],
                'slowest_tickers': current_metrics['slowest_tickers'][:3],
                'cache_hit_ratio': current_metrics['cache_hit_ratio'],
                ...
            })
    
    phase_ticker_processing = time.time() - phase_timer_start
    metrics_mgr.set_phase_timing('ticker_processing', phase_ticker_processing)
    
    # PHASE 4: Cell Writing
    timer = metrics_mgr.start_operation('cell_write', ...)
    # ... cell writing code ...
    timer.finish()
    
    # PHASE 5: File Saving
    timer = metrics_mgr.start_operation('file_save', file_path=file_path)
    try:
        backup_manager.save_backup(workbook, file_path)
    finally:
        timer.finish()
```

### 3.2 ticker_fetcher.py Enhancement

**File**: `core/ticker_fetcher.py`

```python
def get_ticker_price(ticker: str, ...) -> Tuple[...]:
    """Enhanced with metrics tracking."""
    
    from core.metrics_manager import MetricsManager
    metrics_mgr = MetricsManager.get_instance()
    
    # Check cache first
    if ticker in _TICKER_CACHE:
        metrics_mgr.record_cache_hit(ticker)
        # Return cached value
        ...
    
    # Cache miss - need network call
    metrics_mgr.record_cache_miss(ticker)
    metrics_mgr.record_network_call(ticker)
    
    timer = metrics_mgr.start_operation(
        'yfinance_api_call',
        ticker=ticker
    )
    
    try:
        # Call yfinance
        data = ticker_obj.history(start=start_date, end=end_date)
        # Process data...
        success, price, date, error = (True, price_value, date_value, None)
    except Exception as e:
        metrics_mgr._metrics.api_errors += 1
        success, price, date, error = (False, None, None, str(e))
    finally:
        timer.finish()
    
    return (success, price, date, error)
```

---

## Part 4: Debug Mode & Real-Time Visualization

### 4.1 Debug Mode Configuration

```python
# config.py enhancement

class Config:
    """Configuration with debug mode support."""
    
    # Existing fields...
    
    # New debug fields
    debug_mode: bool = False
    debug_metrics_path: str = './debug/metrics'  # Where to save metrics JSONs
    debug_profiling_enabled: bool = False         # Enable cProfile
    debug_verbose_logging: bool = False           # Verbose console output
    debug_capture_slowest_n: int = 10             # Top N operations to track
    
    def load_from_ini(self, path: str):
        # ... existing code ...
        
        # Debug settings
        if self.parser.has_section('DEBUG'):
            self.debug_mode = self.parser.getboolean('DEBUG', 'enabled', fallback=False)
            self.debug_metrics_path = self.parser.get('DEBUG', 'metrics_path', 
                                                      fallback='./debug/metrics')
            # ... other debug settings ...
```

### 4.2 Real-Time Progress Display (GUI)

**New Widget**: `gui/widgets/progress_detail_panel.py`

```python
class ProgressDetailPanel(ctk.CTkFrame):
    """
    Shows real-time progress with detailed metrics.
    
    Layout:
    ┌─────────────────────────────────────────┐
    │ Progress: 342/1553 (22.0%) ▮▮▮░░░░░    │
    │ Current: AAPL | Price: $374.23          │
    │ Elapsed: 2m 34s | Est. Remaining: 9m 12s│
    ├─────────────────────────────────────────┤
    │ Phase Breakdown:                         │
    │  Excel Load:        2.1s (2%)           │
    │  Row Scan:          1.4s (1%)           │
    │  Ticker Processing: 147.2s (87%) ⚠️    │
    │  Cell Writing:      15.3s (9%)          │
    ├─────────────────────────────────────────┤
    │ Cache Performance:                       │
    │  Cache Hit Ratio: 62% (212/342 tickers) │
    │  Network Calls: 130 API requests        │
    │  Avg API Time: 1.13 seconds             │
    ├─────────────────────────────────────────┤
    │ Slowest 3 Tickers:                      │
    │  1. TSLA: 2.34s (cache miss)            │
    │  2. MSFT: 1.89s (cache miss)            │
    │  3. AMZN: 1.76s (cache miss)            │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create labels/values
        self.progress_label = ctk.CTkLabel(self, text="Progress: 0/0 (0%)")
        self.progress_bar = ctk.CTkProgressBar(self)
        self.current_ticker = ctk.CTkLabel(self, text="Current: ---")
        
        # Phase breakdown frame
        self.phase_frame = ctk.CTkFrame(self)
        self.phase_labels = {}  # 'excel_load', 'row_scan', etc.
        
        # Cache stats
        self.cache_label = ctk.CTkLabel(self, text="Cache Hit Ratio: ---%")
        
        # Slowest tickers
        self.slowest_frame = ctk.CTkFrame(self)
        self.slowest_labels = []
    
    def update_metrics(self, metrics: Dict):
        """Update display with new metrics."""
        
        # Update progress
        current = metrics.get('current', 0)
        total = metrics.get('total', 0)
        percent = (current / total * 100) if total > 0 else 0
        self.progress_label.configure(
            text=f"Progress: {current}/{total} ({percent:.1f}%)"
        )
        self.progress_bar.set(percent / 100.0)
        
        # Update current ticker
        ticker = metrics.get('ticker', '---')
        price = metrics.get('price', 'N/A')
        self.current_ticker.configure(
            text=f"Current: {ticker} | Price: ${price}"
        )
        
        # Update phase breakdown
        phase_breakdown = metrics.get('phase_breakdown', {})
        for phase, percentage in phase_breakdown.items():
            label = self.phase_labels.get(phase)
            if label:
                label.configure(
                    text=f"{phase}: {percentage:.1f}%"
                )
        
        # Highlight slowest phase
        slowest_phase = max(phase_breakdown, key=phase_breakdown.get)
        # Apply visual warning if >80% in one phase
        if phase_breakdown.get(slowest_phase, 0) > 80:
            self.phase_labels[slowest_phase].configure(text_color="#FF6B6B")
        
        # Update cache stats
        cache_ratio = metrics.get('cache_hit_ratio', 0)
        self.cache_label.configure(
            text=f"Cache Hit Ratio: {cache_ratio:.1f}%"
        )
        
        # Update slowest tickers
        slowest_tickers = metrics.get('slowest_tickers', [])
        for i, ticker_info in enumerate(slowest_tickers[:3]):
            if i < len(self.slowest_labels):
                ticker = ticker_info.get('ticker', '?')
                time_ms = ticker_info.get('time_ms', 0)
                self.slowest_labels[i].configure(
                    text=f"{i+1}. {ticker}: {time_ms}ms"
                )
```

### 4.3 Debug Report Generator

**New Module**: `core/debug_reporter.py`

```python
def generate_debug_report(metrics: PerformanceMetrics) -> str:
    """
    Generate human-readable debug report.
    
    Example output:
    
    ╔════════════════════════════════════════════════════════════════╗
    ║            XLTickers - Performance Debug Report                ║
    ║                    Session: a1b2c3d4                           ║
    ╚════════════════════════════════════════════════════════════════╝
    
    FILE INFORMATION
    ────────────────────────────────────────────────────────────────
    Path:               D:\Portfolio\Tech Stocks.xlsx
    Size:               22.4 MB
    Rows Processed:     1553
    Unique Tickers:     342
    Duplicates:         1211 (78.1% of rows)
    
    OVERALL PERFORMANCE
    ────────────────────────────────────────────────────────────────
    Total Time:         10m 42s (642 seconds)
    
    PHASE BREAKDOWN (Where Time Was Spent)
    ────────────────────────────────────────────────────────────────
    Phase                  Time      % of Total   Status
    ──────────────────────────────────────────────────────────────
    Excel File Load        2.1s      0.3%         ✓ Fast
    Row Scanning           1.4s      0.2%         ✓ Fast
    Ticker Processing      559.3s    87.0%        ⚠️  BOTTLENECK
    Cell Writing           78.2s     12.2%        ⚠️  Slow
    File Saving            1.0s      0.2%         ✓ Fast
    ──────────────────────────────────────────────────────────────
    
    TICKER PROCESSING DETAILS (87% of time)
    ────────────────────────────────────────────────────────────────
    Network Calls:        130 API requests
    Cache Hits:           212 (62.0%)
    Cache Misses:         130 (38.0%)
    API Errors:           0
    Avg API Response:     4.3 seconds
    Median API Response:  1.5 seconds
    
    Top 5 SLOWEST API CALLS:
     1. TSLA: 23.4s (network timeout? retried?)
     2. NVDA: 8.9s
     3. MSFT: 7.4s
     4. AMZN: 7.1s
     5. GOOGL: 6.8s
    
    💡 Optimization Hint: TSLA took 23.4s - was this a network issue?
       Consider implementing request timeout + retry logic.
    
    CACHE PERFORMANCE ANALYSIS
    ────────────────────────────────────────────────────────────────
    Your file has 1553 rows but only 342 unique tickers.
    This means 1211 duplicate tickers (78.1%).
    
    With current caching:
      - 212 tickers were cached (saved ~318 seconds of API calls)
      - Each duplicate saved ~1.5 seconds on average
      
    ✓ Cache is working effectively!
    
    CELL WRITING PERFORMANCE (12% of time)
    ────────────────────────────────────────────────────────────────
    Total Cells Written:  1553 prices + 1553 dates = 3106 cells
    Time Per Cell:        25.2 ms (78.2s / 3106)
    
    ⚠️ Optimization Hint: openpyxl cell writing is known to be slow.
       Consider batch writing or using other libraries.
    
    HARDWARE INFORMATION
    ────────────────────────────────────────────────────────────────
    CPU:                  Intel Core i5-7400 @ 3.00GHz
    RAM:                  8 GB
    Memory During Run:    ~450 MB (peak)
    CPU Utilization:      45% average
    
    RECOMMENDATIONS
    ════════════════════════════════════════════════════════════════
    
    1. CRITICAL (87% time in Ticker Processing):
       → Problem: yfinance API calls are bottleneck
       → Current: 130 API calls × 4.3s avg = 559s
       → Solution A: Implement parallel API requests (3-5 workers)
          Potential gain: 2-3x faster (from 559s to 180-280s)
       → Solution B: Pre-cache all tickers at startup
          Potential gain: Future runs 62% faster (if tickers repeat)
       → Solution C: Implement request batching (if API supports)
          Potential gain: Depends on API
    
    2. IMPORTANT (12% time in Cell Writing):
       → Problem: openpyxl is slow for large writes
       → Solution A: Batch cell updates (group by 100, write together)
          Potential gain: 20-30% faster
       → Solution B: Switch to xlsxwriter (if read-modify-write allows)
          Potential gain: 40-50% faster
    
    3. MONITORING (0.3% time in Excel Load):
       → Your file size (22.4 MB) loaded in 2.1s
       → This is reasonable for openpyxl
       → Monitor with larger files (>50MB)
    
    ESTIMATED IMPROVEMENTS IF ALL OPTIMIZATIONS APPLIED:
    ════════════════════════════════════════════════════════════════
    
    Baseline:                      642 seconds (10m 42s)
    
    With Parallel API (3-worker):  ~250 seconds (4m 10s) [61% faster]
    With Cell Batching:            ~180 seconds (3m 00s) [72% faster]
    Both Combined:                 ~70 seconds (1m 10s) [89% faster]
    
    """
    
    report = []
    report.append("╔" + "═" * 62 + "╗")
    report.append("║" + " XLTickers - Performance Debug Report".ljust(63) + "║")
    report.append("╚" + "═" * 62 + "╝")
    
    # ... Generate report sections ...
    
    return "\n".join(report)
```

---

## Part 5: Implementation Details for Performance Optimization

### 5.1 Parallel yfinance Calls (Worker Pool)

**New Module**: `core/parallel_ticker_fetcher.py`

```python
"""
Parallel yfinance fetching using ThreadPoolExecutor.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import logging

class ParallelTickerFetcher:
    """Fetch multiple ticker prices in parallel."""
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize with worker pool.
        
        Args:
            max_workers: Number of parallel API requests (3-5 recommended)
                        More workers = faster but more API rate limiting risk
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def fetch_batch(
        self,
        tickers: List[str],
        rounding: int = 4
    ) -> Dict[str, Tuple[bool, float, date, str]]:
        """
        Fetch prices for multiple tickers in parallel.
        
        Args:
            tickers: List of unique ticker symbols
            rounding: Decimal precision
        
        Returns:
            Dict mapping ticker → (success, price, date, error)
        
        Performance:
            - Sequential (1 worker): 130 tickers × 4.3s = 559s
            - Parallel (3 workers): 130 tickers / 3 × 4.3s ≈ 186s (71% faster)
            - Parallel (5 workers): 130 tickers / 5 × 4.3s ≈ 112s (80% faster)
        """
        results = {}
        
        # Submit all jobs
        futures = {
            self.executor.submit(
                get_ticker_price,
                ticker,
                rounding=rounding
            ): ticker
            for ticker in tickers
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                success, price, fetch_date, error = future.result()
                results[ticker] = (success, price, fetch_date, error)
            except Exception as e:
                results[ticker] = (False, None, None, str(e))
        
        return results
```

### 5.2 Batch Cell Writing Optimization

**Enhancement**: `core/excel_processor.py`

```python
def _batch_cell_writes(worksheet, updates: List[Tuple[str, int, float, date]]):
    """
    Write multiple cells at once instead of individually.
    
    Args:
        worksheet: openpyxl Worksheet
        updates: List of (cell_address, row, price, date) tuples
    
    Performance:
        - Individual writes: 3106 cells × 25ms = 78s
        - Batch writes: 31 batches × 2.5s = 78s (similar but better for memory)
        - With optimization: 31 batches × 1.5s = 47s (40% faster)
    """
    
    BATCH_SIZE = 100
    
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        
        # Start batch transaction
        worksheet.enable_write_only = False  # Ensure normal mode
        
        # Write all cells in batch
        for price_cell_addr, date_cell_addr, price, date_val in batch:
            worksheet[price_cell_addr].value = price
            worksheet[date_cell_addr].value = date_val
        
        # Batch complete - system will optimize
```

### 5.3 Advanced Caching Strategy

**Enhancement**: `core/ticker_fetcher.py`

```python
class SmartTickerCache:
    """
    Advanced caching with multiple strategies:
    1. Session cache (current run)
    2. File-based cache (between runs)
    3. Invalidation based on time
    """
    
    def __init__(self, cache_dir: str = './cache/tickers', ttl_hours: int = 24):
        """
        Args:
            cache_dir: Where to store persistent cache files
            ttl_hours: Time-to-live for cached prices (24 hours default)
        """
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.session_cache = {}  # In-memory cache for current run
    
    def get_price(self, ticker: str) -> Optional[Tuple[float, date]]:
        """
        Get cached price from multiple sources:
        1. Session cache (fastest)
        2. Disk cache (if fresh)
        3. Return None (needs API call)
        """
        
        # Check session cache first (O(1) lookup)
        if ticker in self.session_cache:
            return self.session_cache[ticker]
        
        # Check disk cache
        cached_price, cached_date = self._load_from_disk(ticker)
        if cached_price and not self._is_expired(cached_date):
            # Add back to session cache for faster lookup
            self.session_cache[ticker] = (cached_price, cached_date)
            return (cached_price, cached_date)
        
        return None  # Not cached, need API call
    
    def cache_price(self, ticker: str, price: float, date_val: date):
        """Cache price in both session and disk."""
        self.session_cache[ticker] = (price, date_val)
        self._save_to_disk(ticker, price, date_val)
    
    def _load_from_disk(self, ticker: str) -> Tuple[Optional[float], Optional[date]]:
        """Load cached price from disk cache file."""
        # Implementation: load from JSON/SQLite cache
        pass
    
    def _save_to_disk(self, ticker: str, price: float, date_val: date):
        """Save price to disk cache for future runs."""
        # Implementation: persist to cache storage
        pass
    
    def _is_expired(self, date_val: date) -> bool:
        """Check if cached price is too old."""
        age_hours = (dt.datetime.now().date() - date_val).days * 24
        return age_hours > self.ttl_hours
```

---

## Part 6: Performance Targets & Success Criteria

### 6.1 Performance Targets by File Size

| File Size | Target Time | Status |
|-----------|------------|--------|
| 1 MB (25 tickers) | < 30 seconds | TBD |
| 5 MB (125 tickers) | < 2 minutes | TBD |
| 20 MB (500 tickers) | < 8 minutes | TBD (Current: 10-12m) |
| 50 MB (1250 tickers) | < 18 minutes | TBD |

**Optimization roadmap**:
1. Baseline (Phase 2.0): Current performance (~642s for 1553 rows, 342 unique)
2. Parallel API (Phase 2.1): 3-worker pool → 186s (71% faster)
3. Batch writing (Phase 2.2): 47s (40% faster on cell writes)
4. Smart caching (Phase 2.3): 62% faster on duplicate-heavy files
5. Combined optimizations: **Potential 85% improvement** (from 642s to ~95s)

### 6.2 Memory Usage Targets

| File Size | Memory Budget | Target Peak |
|-----------|--------------|------------|
| 20 MB file | 512 MB | < 300 MB |
| 50 MB file | 512 MB | < 350 MB |
| 100 MB file | 1 GB | < 500 MB |

**Monitoring**: Real-time memory display in debug panel

### 6.3 Debug Metrics Success Criteria

✅ **Must have** (Phase 2.0):
- [ ] Per-phase timing breakdown
- [ ] Per-ticker timing tracking
- [ ] Cache hit/miss ratio display
- [ ] API error counting
- [ ] Real-time progress with metrics

✅ **Should have** (Phase 2.1):
- [ ] Slowest ticker identification
- [ ] Network bottleneck detection
- [ ] Disk I/O profiling
- [ ] Memory usage tracking
- [ ] CPU utilization display

✅ **Nice to have** (Phase 2.2+):
- [ ] Flame graph visualization
- [ ] Timeline view of operations
- [ ] Comparative analysis (before/after optimization)
- [ ] Predictive time estimation

---

## Part 7: GUI Debug Panel Layout

```
╔══════════════════════════════════════════════════════════════════════╗
║ Price Update Progress                              [✓ Debug Mode ON] ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Progress: 342/1553 (22.0%)  ▮▮▮▮▮░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ║
║  Current:  AAPL              Time: 2m 34s          ETA: 9m 12s       ║
║                                                                      ║
╠═ PHASE BREAKDOWN ════════════════════════════════════════════════════╣
║                                                                      ║
║  Excel Load         2.1s  (0%)   ████                  Status: ✓ OK  ║
║  Row Scan           1.4s  (0%)   ████                  Status: ✓ OK  ║
║  Ticker Processing  147s  (87%)  ███████████████████  Status: ⚠️ HOT║
║  Cell Writing       15.3s (9%)   ████                  Status: ⚠️ WARM║
║  File Saving        TBD   (%)    [pending]            Status: ⏳...  ║
║                                                                      ║
║  💡 Bottleneck Identified: 87% time in Ticker Processing             ║
║     → Consider enabling parallel API fetching in settings             ║
║                                                                      ║
╠═ CACHE PERFORMANCE ══════════════════════════════════════════════════╣
║                                                                      ║
║  Cache Hit Ratio:   62% (212 / 342 tickers)                         ║
║  Network Calls:     130 API requests completed                      ║
║  API Errors:        0                                               ║
║  Avg API Time:      1.13 seconds                                    ║
║                                                                      ║
║  💡 Duplicates saved: 1211 rows reused cached prices                 ║
║     Estimated saved time: 318 seconds                                ║
║                                                                      ║
╠═ SLOWEST 3 TICKERS ══════════════════════════════════════════════════╣
║                                                                      ║
║  1. TSLA:   2.34s  (network timeout detected)                       ║
║  2. MSFT:   1.89s  (2nd API call)                                   ║
║  3. AMZN:   1.76s  (2nd API call)                                   ║
║                                                                      ║
╠═ SYSTEM INFO ════════════════════════════════════════════════════════╣
║                                                                      ║
║  RAM Usage:   450 MB / 7.8 GB (5.8%)    ████░░░░░░░░░░░░░░░░░░░   ║
║  CPU Usage:   45% average                ██████░░░░░░░░░░░░░░░░░   ║
║  Disk I/O:    2.3 MB/s                                              ║
║                                                                      ║
║  [ ] Save Metrics Report    [ ] Export as CSV    [ ] Close Debug ]  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Part 8: Implementation Schedule

### Week 1: Metrics Foundation
- [ ] Create `core/metrics.py` with data structures
- [ ] Create `core/metrics_manager.py` with singleton pattern
- [ ] Add metric collection to `excel_processor.py` phases
- [ ] Add metric collection to `ticker_fetcher.py`
- [ ] Create `core/debug_reporter.py`

### Week 2: GUI Integration
- [ ] Create `gui/widgets/progress_detail_panel.py`
- [ ] Integrate metrics into progress callback
- [ ] Add real-time chart visualization
- [ ] Create debug report viewer widget
- [ ] Add "Debug Mode" toggle to Settings tab

### Week 3: Optimization Implementation
- [ ] Create `core/parallel_ticker_fetcher.py`
- [ ] Implement batch cell writing
- [ ] Create `SmartTickerCache` with persistence
- [ ] A/B test each optimization
- [ ] Document performance improvements

### Week 4: Polish & Documentation
- [ ] Finalize metrics visualization
- [ ] Create performance tuning guide
- [ ] Document bottlenecks and solutions
- [ ] User-facing help text in GUI
- [ ] Create example debug reports

---

## Summary

**The Goal**: Transform a "black box" processing system into a **transparent, measurable, optimizable** pipeline.

**Key Metrics**:
- Phase breakdown (where is time spent?)
- Per-ticker timing (which tickers are slow?)
- Cache effectiveness (how many duplicates?)
- Network performance (API latency?)
- System resources (RAM, CPU usage?)

**Expected Outcomes**:
- Users see exactly what's happening during processing
- Developers can identify bottlenecks with precision
- Performance improvements are measurable and documented
- Large files (20MB+) process 50-85% faster after optimizations
