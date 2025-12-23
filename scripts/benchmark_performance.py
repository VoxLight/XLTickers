"""
Performance benchmark script.

Compare old vs new implementation to measure improvements.

Usage:
    python scripts/benchmark_performance.py
    
    Generates:
    - Comparison report
    - Performance metrics for both versions
    - Recommendations for optimization
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

from core.config import Config
from core.metrics import Metrics, metrics_report
from core.excel_processor import process_excel as process_excel_old
from core.excel_processor_optimized import process_excel_optimized

logger = logging.getLogger(__name__)


def benchmark_old_implementation(
    excel_file: str,
    config: Config,
    action_type: str = 'price'
) -> Tuple[Dict[str, Any], Metrics]:
    """
    Run old implementation with metrics.
    
    Returns:
        (result_dict, metrics)
    """
    metrics = Metrics('old_implementation')
    
    with metrics:
        success, stats, errors = process_excel_old(
            excel_file,
            config,
            action_type=action_type,
            progress_callback=None,
        )
    
    return {'success': success, 'stats': stats, 'errors': errors}, metrics


def benchmark_new_implementation(
    excel_file: str,
    config: Config,
    action_type: str = 'price',
    parallel_workers: int = 5,
) -> Tuple[Dict[str, Any], Metrics]:
    """
    Run new optimized implementation with metrics.
    
    Returns:
        (result_dict, metrics)
    """
    metrics = Metrics('new_implementation')
    
    with metrics:
        success, stats, errors = process_excel_optimized(
            excel_file,
            config,
            action_type=action_type,
            metrics=metrics,
            use_cache=True,
            parallel_workers=parallel_workers,
            batch_size=100,
        )
    
    return {'success': success, 'stats': stats, 'errors': errors}, metrics


def format_benchmark_report(
    old_result: Dict[str, Any],
    old_metrics: Metrics,
    new_result: Dict[str, Any],
    new_metrics: Metrics,
) -> str:
    """
    Generate comparison report.
    
    Returns:
        Formatted report string
    """
    old_time = old_metrics.get_total_duration()
    new_time = new_metrics.get_total_duration()
    improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0
    speedup = old_time / new_time if new_time > 0 else 0
    
    lines = [
        "\n" + "="*70,
        "PERFORMANCE BENCHMARK REPORT",
        "="*70,
        "",
        "OLD IMPLEMENTATION:",
        "-" * 70,
        f"  Total Time: {old_time:.2f} seconds",
        f"  Rows Processed: {old_result['stats'].get('rows_processed', 'N/A')}",
        f"  Tickers Updated: {old_result['stats'].get('tickers_updated', 'N/A')}",
        f"  Errors: {old_result['stats'].get('errors_count', 'N/A')}",
        "",
        "NEW OPTIMIZED IMPLEMENTATION:",
        "-" * 70,
        f"  Total Time: {new_time:.2f} seconds",
        f"  Rows Processed: {new_result['stats'].get('rows_processed', 'N/A')}",
        f"  Tickers Updated: {new_result['stats'].get('tickers_updated', 'N/A')}",
        f"  Errors: {new_result['stats'].get('errors_count', 'N/A')}",
        "",
        "IMPROVEMENT:",
        "-" * 70,
        f"  ⚡ Speedup: {speedup:.1f}x faster",
        f"  📊 Improvement: {improvement:.1f}%",
        f"  ⏱️  Time saved: {old_time - new_time:.2f} seconds",
        "",
    ]
    
    # Add phase breakdown if available
    if 'fetch_duration_seconds' in new_result['stats']:
        lines.extend([
            "NEW IMPLEMENTATION BREAKDOWN:",
            "-" * 70,
            f"  Fetch Phase: {new_result['stats'].get('fetch_duration_seconds', 0):.2f}s",
            f"  Write Phase: {new_result['stats'].get('write_duration_seconds', 0):.2f}s",
            f"  Save Phase: {new_result['stats'].get('save_duration_seconds', 0):.2f}s",
            "",
        ])
    
    # Recommendations
    lines.extend([
        "RECOMMENDATIONS:",
        "-" * 70,
    ])
    
    if improvement < 20:
        lines.append("  ⚠️  Improvement is modest. Check for other bottlenecks.")
    elif improvement < 50:
        lines.append("  ✓ Good improvement. Cache and parallelization working.")
    elif improvement < 80:
        lines.append("  ✨ Excellent improvement! Optimizations are very effective.")
    else:
        lines.append("  🚀 Outstanding improvement! Near maximum potential achieved.")
    
    lines.extend([
        "",
        "="*70,
        ""
    ])
    
    return "\n".join(lines)


if __name__ == '__main__':
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Get Excel file to benchmark
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        print("Usage: python scripts/benchmark_performance.py <excel_file>")
        print("Example: python scripts/benchmark_performance.py data.xlsx")
        sys.exit(1)
    
    # Load config
    config = Config('./config.ini')
    
    print(f"Benchmarking {excel_file}...")
    print("(This will run both implementations and compare performance)")
    print("")
    
    # Run old implementation
    print("Running old implementation (sequential)...")
    old_result, old_metrics = benchmark_old_implementation(excel_file, config)
    print(f"  Done: {old_metrics.get_total_duration():.2f}s\n")
    
    # Run new implementation
    print("Running new optimized implementation (parallel)...")
    new_result, new_metrics = benchmark_new_implementation(
        excel_file, 
        config,
        parallel_workers=5
    )
    print(f"  Done: {new_metrics.get_total_duration():.2f}s\n")
    
    # Generate report
    report = format_benchmark_report(old_result, old_metrics, new_result, new_metrics)
    print(report)
    
    # Detailed metrics
    print("\nDETAILED OLD METRICS:")
    print(metrics_report(old_metrics))
    
    print("\nDETAILED NEW METRICS:")
    print(metrics_report(new_metrics))
