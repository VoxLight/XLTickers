"""
Performance metrics collection system.

Tracks execution time, API calls, Excel operations, and generates reports.
Provides detailed bottleneck analysis for optimization.

Usage:
    from core.metrics import Metrics, metrics_report
    
    with Metrics('price_update') as m:
        # your operations
        m.record_api_call('AAPL', duration=0.45)
        m.record_excel_write(cell_count=100, duration=1.2)
    
    # Generate report
    report = metrics_report(m)
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of operations being measured."""
    API_CALL = "api_call"
    EXCEL_READ = "excel_read"
    EXCEL_WRITE = "excel_write"
    PARSING = "parsing"
    VALIDATION = "validation"
    ITERATION = "iteration"


@dataclass
class MetricEntry:
    """Single metric data point."""
    operation: str
    duration: float  # seconds
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation': self.operation,
            'duration': round(self.duration, 4),
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }


@dataclass
class Metrics:
    """
    Collects performance metrics during execution.
    
    Can be used as context manager:
        with Metrics('price_update') as m:
            # track operations
            m.record_api_call('AAPL', duration=0.45)
    """
    
    operation_name: str
    entries: List[MetricEntry] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Counters for quick stats
    api_call_count: int = 0
    excel_write_count: int = 0
    excel_read_count: int = 0
    error_count: int = 0
    
    def __enter__(self):
        """Context manager entry."""
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end_time = datetime.now()
        if exc_type:
            logger.error(f"Metrics: Exception in {self.operation_name}: {exc_val}")
    
    def record_api_call(
        self,
        ticker: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Record an API call metric."""
        self.api_call_count += 1
        if not success:
            self.error_count += 1
        
        entry = MetricEntry(
            operation='api_call',
            duration=duration,
            metadata={
                'ticker': ticker,
                'success': success,
                'error': error,
            }
        )
        self.entries.append(entry)
    
    def record_excel_write(
        self,
        cell_count: int,
        duration: float,
        worksheet: str = "Sheet1"
    ) -> None:
        """Record Excel write operation."""
        self.excel_write_count += 1
        entry = MetricEntry(
            operation='excel_write',
            duration=duration,
            metadata={
                'cell_count': cell_count,
                'worksheet': worksheet,
            }
        )
        self.entries.append(entry)
    
    def record_excel_read(
        self,
        cell_count: int,
        duration: float,
        worksheet: str = "Sheet1"
    ) -> None:
        """Record Excel read operation."""
        self.excel_read_count += 1
        entry = MetricEntry(
            operation='excel_read',
            duration=duration,
            metadata={
                'cell_count': cell_count,
                'worksheet': worksheet,
            }
        )
        self.entries.append(entry)
    
    def record_custom(
        self,
        operation: str,
        duration: float,
        **metadata
    ) -> None:
        """Record custom operation metric."""
        entry = MetricEntry(
            operation=operation,
            duration=duration,
            metadata=metadata
        )
        self.entries.append(entry)
    
    def get_total_duration(self) -> float:
        """Get total execution time."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return sum(e.duration for e in self.entries)
    
    def get_duration_by_operation(self) -> Dict[str, float]:
        """Get total duration grouped by operation type."""
        durations = {}
        for entry in self.entries:
            if entry.operation not in durations:
                durations[entry.operation] = 0
            durations[entry.operation] += entry.duration
        return durations
    
    def get_average_api_call_time(self) -> float:
        """Get average API call duration."""
        api_calls = [e for e in self.entries if e.operation == 'api_call']
        if not api_calls:
            return 0
        return sum(e.duration for e in api_calls) / len(api_calls)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'operation_name': self.operation_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_seconds': round(self.get_total_duration(), 2),
            'api_call_count': self.api_call_count,
            'excel_write_count': self.excel_write_count,
            'excel_read_count': self.excel_read_count,
            'error_count': self.error_count,
            'average_api_call_seconds': round(self.get_average_api_call_time(), 4),
            'entries': [e.to_dict() for e in self.entries],
        }


def metrics_report(metrics: Metrics) -> str:
    """
    Generate a human-readable performance report.
    
    Args:
        metrics: Metrics instance
        
    Returns:
        Formatted report string
    """
    total_duration = metrics.get_total_duration()
    duration_by_op = metrics.get_duration_by_operation()
    
    # Calculate percentages
    op_percentages = {}
    for op, duration in duration_by_op.items():
        percentage = (duration / total_duration * 100) if total_duration > 0 else 0
        op_percentages[op] = percentage
    
    # Build report
    lines = [
        "\n" + "="*70,
        "PERFORMANCE METRICS REPORT",
        "="*70,
        f"\nOperation: {metrics.operation_name}",
        f"Start: {metrics.start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
        f"End: {metrics.end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if metrics.end_time else 'N/A'}",
        f"\n{'─'*70}",
        f"TOTAL EXECUTION TIME: {total_duration:.2f} seconds",
        f"{'─'*70}",
        "\nOPERATION BREAKDOWN:",
    ]
    
    # Add operation breakdown
    for op in sorted(duration_by_op.keys(), 
                     key=lambda x: duration_by_op[x], reverse=True):
        duration = duration_by_op[op]
        percentage = op_percentages[op]
        bar_length = int(percentage / 5)  # Max 20 chars wide
        bar = "█" * bar_length + "░" * (20 - bar_length)
        lines.append(f"  {op:15} {duration:8.2f}s {bar} {percentage:5.1f}%")
    
    # Add operation counts
    lines.extend([
        f"\n{'─'*70}",
        "OPERATION COUNTS:",
        f"  API Calls:      {metrics.api_call_count}",
        f"  Excel Writes:   {metrics.excel_write_count}",
        f"  Excel Reads:    {metrics.excel_read_count}",
        f"  Errors:         {metrics.error_count}",
    ])
    
    # Add API performance
    if metrics.api_call_count > 0:
        avg_api = metrics.get_average_api_call_time()
        api_total = duration_by_op.get('api_call', 0)
        lines.extend([
            f"\n{'─'*70}",
            "API CALL ANALYSIS:",
            f"  Total API Time:     {api_total:.2f}s",
            f"  Number of Calls:    {metrics.api_call_count}",
            f"  Average per Call:   {avg_api:.4f}s",
            f"  % of Total Time:    {op_percentages.get('api_call', 0):.1f}%",
        ])
    
    # Add Excel performance
    excel_write_total = duration_by_op.get('excel_write', 0)
    excel_read_total = duration_by_op.get('excel_read', 0)
    if metrics.excel_read_count > 0 or metrics.excel_write_count > 0:
        lines.extend([
            f"\n{'─'*70}",
            "EXCEL OPERATION ANALYSIS:",
        ])
        if metrics.excel_read_count > 0:
            lines.append(f"  Read:  {excel_read_total:.2f}s ({metrics.excel_read_count} operations)")
        if metrics.excel_write_count > 0:
            lines.append(f"  Write: {excel_write_total:.2f}s ({metrics.excel_write_count} operations)")
    
    # Bottleneck analysis
    sorted_ops = sorted(op_percentages.items(), key=lambda x: x[1], reverse=True)
    if sorted_ops:
        lines.extend([
            f"\n{'─'*70}",
            "BOTTLENECK ANALYSIS:",
            f"  Top bottleneck: {sorted_ops[0][0]} ({sorted_ops[0][1]:.1f}% of time)",
        ])
        if sorted_ops[0][1] > 70:
            lines.append(f"  ⚠️  This operation dominates execution time!")
        if sorted_ops[0][1] > 90:
            lines.append(f"  🔴 CRITICAL: Optimize this first for maximum gains")
    
    lines.extend([
        "="*70,
        ""
    ])
    
    return "\n".join(lines)
