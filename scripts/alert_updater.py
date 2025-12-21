# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# project libs
from libs.cli_adapter import init_config, process_excel_with_callback, print_summary
from libs.common import globals_, _get_valid_input
from scripts.common import _cols


NAME = "Alert Updater"


def _valid_number_of_days(str_num_of_days):
    """Validate that days_ago is reasonable for alert updates"""
    if not str_num_of_days.isdigit():
        print("    ERROR: That is not a number, try again.")
        return False
    elif not int(str_num_of_days) > 5:
        print("    ERROR: That is not far enough into the past to get accurate alert info.")
        return False
    return True


def _get_number_of_days():
    """Get number of days in past for alert price lookup"""
    return _get_valid_input(
        "",
        _valid_number_of_days,
        "Please enter the number of days in the past to check: ",
        int
    )


def run(ws):
    """
    Run alert updater using new core modules (Phase 1.1).
    
    This fetches historical prices from N days ago for alert/baseline tracking.
    
    Args:
        ws: Worksheet (passed by main.py but not used in new implementation)
    """
    print("\n" + "="*50)
    print("ALERT UPDATER - Phase 1.1")
    print("="*50)
    
    # Get number of days in past for historical price
    days_ago = _get_number_of_days()
    globals_.days_ago = days_ago
    print(f"✓ Will fetch prices from {days_ago} days ago")
    
    # Get config
    try:
        config = init_config()
        print(f"✓ Configuration loaded")
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
            print(f"  ✓ {ticker} ({days_ago} days ago): ${price}")
        else:
            print(f"  ✗ {ticker}: {error}")
    
    try:
        result = process_excel_with_callback(
            file_path=file_path,
            config=config,
            action_type='alert',
            on_row_processed=on_row_processed
        )
        
        # Print summary
        print_summary(result)
        
        # Store summary in globals for compatibility
        if result['stats']:
            print(f"Summary: Updated {result['stats'].get('tickers_updated', 0)} alert prices")
    
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    
