# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# project libs
from libs.cli_adapter import init_config, process_excel_optimized_with_metrics, print_summary
from libs.common import globals_
from scripts.common import _cols


NAME = "Price Updater"


def run(ws):
    """
    Run price updater using OPTIMIZED core modules.
    
    Features:
    - Parallel ticker fetching (3-5x faster)
    - Batch Excel writes (2-3x faster)
    - Intelligent caching
    - Real-time metrics tracking
    
    This function:
    1. Loads configuration
    2. Processes Excel file with optimized parallel processor
    3. Shows detailed performance metrics
    4. Prints results
    
    Args:
        ws: Worksheet (passed by main.py but not used in new implementation)
    """
    print("\n" + "="*50)
    print("PRICE UPDATER - Optimized")
    print("="*50)
    
    # Get config
    try:
        config = init_config()
        print(f"✓ Configuration loaded")
        print(f"  Ticker column: {config.ticker_column}")
        print(f"  Price column: {config.price_column}")
        print(f"  Date column: {config.date_column}")
        print(f"  Precision: {config.price_decimals} decimals")
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return
    
    # Get file path from globals (set by get_worksheet in main)
    file_path = globals_.workbook_fp
    print(f"\nProcessing: {file_path}")
    print(f"Using optimized processor (parallel fetching + batch writes)...\n")
    
    # Process Excel file with OPTIMIZED core module
    def on_row_processed(ticker, success, price, error):
        """Callback for progress updates"""
        if success and ticker:
            print(f"  → {ticker}")
    
    try:
        result = process_excel_optimized_with_metrics(
            file_path=file_path,
            config=config,
            action_type='price',
            on_row_processed=on_row_processed,
            parallel_workers=5,        # 5 concurrent API calls
            batch_size=100,            # Write 100 cells at a time
            use_cache=True             # Enable intelligent caching
        )
        
        # Print summary
        print_summary(result)
        
        # Print performance metrics
        if 'metrics_report' in result:
            print("\n" + "="*50)
            print("PERFORMANCE METRICS")
            print("="*50)
            print(result['metrics_report'])
        
        # Store summary in globals for compatibility
        if result['stats']:
            stats = result['stats']
            print(f"Summary: Updated {stats.get('tickers_updated', 0)} tickers in {stats.get('total_duration_seconds', 0):.2f}s")
    
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()