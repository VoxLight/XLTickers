"""
Price Updater - Phase 1.1 Implementation

Uses new core modules (config, ticker_fetcher, excel_processor) while maintaining
the original CLI interface and behavior.
"""

# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel
import datetime as dt

# local libs
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# project libs
from libs.cli_adapter import init_config, process_excel_with_callback, print_summary
from libs.common import globals_
from scripts.common import _cols


NAME = "Price Updater"


def run(ws):
    """
    Run price updater using new core modules.
    
    This function:
    1. Loads configuration
    2. Processes Excel file with new robust core logic
    3. Prints results with old interface compatibility
    4. Stores errors in globals_ for old error reporting
    
    Args:
        ws: Worksheet (passed by main.py but not used in Phase 1.1)
    """
    print("\n" + "="*50)
    print("PRICE UPDATER - PHASE 1.1")
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
    
    # Process Excel file with new core module
    def on_row_processed(ticker, success, price, error):
        """Callback for each row processed"""
        if success:
            print(f"  ✓ {ticker}: ${price}")
        else:
            print(f"  ✗ {ticker}: {error}")
    
    try:
        result = process_excel_with_callback(
            file_path=file_path,
            config=config,
            action_type='price',
            on_row_processed=on_row_processed
        )
        
        # Print summary
        print_summary(result)
        
        # Store summary in globals for compatibility
        if result['stats']:
            print(f"Summary: Updated {result['stats'].get('tickers_updated', 0)} tickers")
    
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
