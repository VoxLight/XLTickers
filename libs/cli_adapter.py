"""
CLI Adapter - Bridge between old CLI interface and new core modules.

This module provides compatibility between the original CLI scripts
and the new robust core modules (config, ticker_fetcher, excel_processor).
"""

from collections import defaultdict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config, ConfigError
from core.ticker_fetcher import get_ticker_price
from core.excel_processor import process_excel
from libs.common import globals_


class CliError(Exception):
    """CLI-specific error"""
    pass


def init_config():
    """Initialize and return config object. Store errors in globals_ for old interface."""
    try:
        config = Config()
        return config
    except ConfigError as e:
        raise CliError(f"Configuration Error: {str(e)}")


def fetch_ticker_price(ticker, config=None):
    """
    Fetch price for ticker using new core module.
    Returns price or None (maintains old interface).
    Stores errors in globals_.errors for old error reporting.
    
    Args:
        ticker: Stock ticker symbol
        config: Config object (optional, creates if not provided)
    
    Returns:
        price (float) or None if failed
    """
    if config is None:
        config = init_config()
    
    try:
        success, price, date, error = get_ticker_price(
            ticker,
            days_ago=globals_.days_ago,
            rounding=config.price_decimals
        )
        
        if not success:
            globals_.add_error(ticker, error)
            return None
        
        return price
    
    except Exception as e:
        globals_.add_error(ticker, str(e))
        return None


def process_excel_with_callback(file_path, config, action_type='price', 
                                on_row_processed=None, on_error=None):
    """
    Process Excel file using new core module with progress callbacks.
    
    Args:
        file_path: Path to Excel file
        config: Config object
        action_type: 'price' or 'alert'
        on_row_processed: Callback(ticker, success, value, error) after each row
        on_error: Callback(error_type, error_info) for errors
    
    Returns:
        dict with success, stats, errors from core.excel_processor
    """
    def progress_callback(data):
        """Internal callback from core module to CLI callback"""
        if on_row_processed:
            # data = {'ticker': str, 'row': int, 'price': float, 'date': date, 'error': str}
            ticker = data.get('ticker', '')
            price = data.get('price')
            error = data.get('error', '')
            success = error == ''
            
            on_row_processed(ticker, success, price, error)
    
    try:
        success, stats, errors = process_excel(
            file_path=file_path,
            config=config,
            action_type=action_type,
            progress_callback=progress_callback
        )
        
        # Store stats in globals for old interface compatibility
        globals_.stats = stats
        globals_.core_errors = errors
        
        # Convert core errors to old format for compatibility
        for error_type, error_info in errors.items():
            if on_error:
                on_error(error_type, error_info)
        
        return {
            'success': success,
            'stats': stats,
            'errors': errors
        }
    
    except Exception as e:
        raise CliError(f"Excel processing error: {str(e)}")


def print_summary(result):
    """
    Print summary of Excel processing result.
    
    Args:
        result: Dict returned from process_excel_with_callback
    """
    if not result['success']:
        print("\n❌ Processing failed")
        return
    
    stats = result['stats']
    errors = result['errors']
    
    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    
    # Summary stats
    print(f"✓ Tickers processed: {stats.get('tickers_processed', 0)}")
    print(f"✓ Tickers updated: {stats.get('tickers_updated', 0)}")
    print(f"✓ Rows processed: {stats.get('rows_processed', 0)}")
    
    # Backup location
    backup_path = stats.get('backup_path', '')
    if backup_path:
        print(f"✓ Backup saved: {backup_path}")
    
    # Errors
    if errors:
        print("\n⚠ ERRORS ENCOUNTERED:")
        for error_type, error_info in errors.items():
            print(f"\n  {error_type}:")
            print(f"    Message: {error_info.get('message', 'N/A')}")
            if error_info.get('details'):
                for detail in error_info['details'][:5]:  # Show first 5
                    print(f"      - {detail}")
                if len(error_info['details']) > 5:
                    print(f"      ... and {len(error_info['details']) - 5} more")
    else:
        print("\n✓ No errors")
    
    print("="*50 + "\n")
