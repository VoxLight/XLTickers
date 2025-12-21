"""
Excel processing module for updating ticker prices and alerts.

Pure business logic for reading, processing, and writing Excel files.
Returns structured results with detailed error reporting.
No global state, no printing—designed for GUI integration.
"""

import logging
import datetime as dt
from typing import Callable, Dict, List, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils.datetime import to_excel as date_to_excel

from core.config import Config
from core.ticker_fetcher import get_ticker_price


logger = logging.getLogger(__name__)


# ==================== Data Structures ====================

@dataclass
class ProcessingStats:
    """Statistics from a processing run."""
    rows_processed: int = 0
    tickers_updated: int = 0
    rows_skipped: int = 0
    errors_count: int = 0
    processing_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            'rows_processed': self.rows_processed,
            'tickers_updated': self.tickers_updated,
            'rows_skipped': self.rows_skipped,
            'errors_count': self.errors_count,
            'processing_time_seconds': round(self.processing_time_seconds, 2),
        }


@dataclass
class ProcessingError:
    """Represents an error during processing."""
    error_type: str  # e.g., 'INVALID_TICKER', 'FILE_ACCESS', etc.
    message: str
    rows: List[int]  # Row numbers where this error occurred
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.error_type,
            'message': self.message,
            'rows': self.rows,
            'count': len(self.rows),
        }


# ==================== Validation Functions ====================

def _is_valid_cell(cell) -> bool:
    """
    Check if a cell contains valid ticker data.
    
    Valid cells:
    - Are not merged cells
    - Contain strings
    - Are non-empty and not whitespace-only
    """
    if isinstance(cell, MergedCell):
        return False
    
    value = cell.value
    if not isinstance(value, str):
        return False
    
    if len(value.strip()) == 0:
        return False
    
    return True


def _should_process_row(
    cell_value: str,
    start_marker: str,
    stop_marker: str,
    current_touch: bool
) -> Tuple[bool, bool]:
    """
    Determine if a row should be processed.
    
    Returns:
        (should_process: bool, new_touch_state: bool)
    """
    if cell_value == start_marker:
        return False, True
    
    if cell_value == stop_marker:
        return False, False
    
    return current_touch, current_touch


# ==================== Core Processing Functions ====================

def _update_price_cell(
    ticker: str,
    cell,
    config: Config,
) -> Tuple[bool, Optional[str]]:
    """
    Update a single price cell with ticker data.
    
    Args:
        ticker: Stock ticker symbol
        cell: openpyxl Cell to update
        config: Configuration manager
        
    Returns:
        (success: bool, error_msg: Optional[str])
    """
    success, price, fetch_date, fetch_error = get_ticker_price(
        ticker,
        rounding=config.rounding_precision
    )
    
    if not success:
        return False, fetch_error
    
    try:
        cell.value = price
        logger.debug(f"Updated {cell.coordinate} to {price} for {ticker}")
        return True, None
    
    except Exception as e:
        return False, f"Failed to write to cell {cell.coordinate}: {str(e)}"


def _update_date_cell(cell) -> Tuple[bool, Optional[str]]:
    """
    Update a date cell with today's date.
    
    Args:
        cell: openpyxl Cell to update
        
    Returns:
        (success: bool, error_msg: Optional[str])
    """
    try:
        cell.value = date_to_excel(dt.datetime.today())
        return True, None
    except Exception as e:
        return False, f"Failed to write date to cell {cell.coordinate}: {str(e)}"


def _process_single_row(
    ticker: str,
    row_num: int,
    worksheet,
    config: Config,
    action_type: str,
) -> Tuple[bool, Optional[str]]:
    """
    Process a single row: fetch ticker price and update cells.
    
    Args:
        ticker: Stock ticker symbol
        row_num: Row number (1-indexed)
        worksheet: openpyxl Worksheet
        config: Configuration manager
        action_type: Type of action ('price', 'alert', etc.)
        
    Returns:
        (success: bool, error_msg: Optional[str])
    """
    if action_type == 'price':
        # Get cells to update
        price_cell = worksheet[f"{config.price_column}{row_num}"]
        date_cell = worksheet[f"{config.date_column}{row_num}"]
        
        # Update price
        success, error = _update_price_cell(ticker, price_cell, config)
        if not success:
            return False, error
        
        # Update date
        success, error = _update_date_cell(date_cell)
        if not success:
            return False, error
        
        return True, None
    
    elif action_type == 'alert':
        # Update alert cells (similar structure)
        alert_date_cell = worksheet[f"{config.alert_date_column}{row_num}"]
        alert_price_cell = worksheet[f"{config.alert_price_column}{row_num}"]
        
        # Update price
        success, error = _update_price_cell(ticker, alert_price_cell, config)
        if not success:
            return False, error
        
        # Update date
        success, error = _update_date_cell(alert_date_cell)
        if not success:
            return False, error
        
        return True, None
    
    else:
        return False, f"Unknown action type: {action_type}"


# ==================== Main Processing Function ====================

def process_excel(
    file_path: str,
    config: Config,
    action_type: str = 'price',
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Process an Excel file to update ticker prices or alerts.
    
    This is the main entry point for Excel processing. It:
    1. Validates the file exists and is readable
    2. Loads the worksheet
    3. Iterates through rows between start/stop markers
    4. Fetches ticker data and updates cells
    5. Collects errors without stopping
    6. Saves the file
    7. Returns comprehensive results
    
    Args:
        file_path: Path to Excel file (.xlsx)
        config: Config instance with column mappings
        action_type: 'price' or 'alert' (determines which cells are updated)
        progress_callback: Optional callback for progress updates
                          Called with dict containing:
                          - current: int (rows processed)
                          - total: int (estimated total rows)
                          - ticker: str (current ticker)
                          - status: str (status message)
                          - elapsed: float (seconds elapsed)
    
    Returns:
        Tuple of:
        - success: bool (True if file saved successfully, False otherwise)
        - stats: dict with ProcessingStats.to_dict() format
        - errors: dict mapping error types to lists of affected rows
        
    Example:
        >>> config = Config('./config.ini')
        >>> success, stats, errors = process_excel(
        ...     'data.xlsx',
        ...     config,
        ...     action_type='price'
        ... )
        >>> print(f"Processed {stats['rows_processed']} rows")
        >>> if errors:
        ...     for error_type, error_info in errors.items():
        ...         print(f"{error_type}: {error_info['count']} occurrences")
    """
    
    import time
    start_time = time.time()
    stats = ProcessingStats()
    errors_by_type: Dict[str, ProcessingError] = {}
    
    # ========== PHASE 1: File Validation & Loading ==========
    
    try:
        workbook = load_workbook(file_path)
    except FileNotFoundError:
        return (
            False,
            stats.to_dict(),
            {
                'FILE_NOT_FOUND': {
                    'message': f'File not found: {file_path}',
                    'rows': [],
                }
            }
        )
    except PermissionError:
        return (
            False,
            stats.to_dict(),
            {
                'FILE_ACCESS': {
                    'message': (
                        'Cannot access file. Is it open in Excel? '
                        'Please close it and try again.'
                    ),
                    'rows': [],
                }
            }
        )
    except Exception as e:
        return (
            False,
            stats.to_dict(),
            {
                'FILE_ERROR': {
                    'message': f'Failed to open file: {str(e)}',
                    'rows': [],
                }
            }
        )
    
    try:
        # Use active sheet (first sheet by default)
        worksheet = workbook.active
        
        # ========== PHASE 2: Row Collection ==========
        
        # First pass: collect all valid rows (between markers)
        ticker_column = config.ticker_column
        start_marker = config.start_marker
        stop_marker = config.stop_marker
        
        rows_to_process = []
        currently_processing = False
        
        for cell in worksheet[ticker_column]:
            if not _is_valid_cell(cell):
                continue
            
            cell_value = cell.value.strip()
            should_process, currently_processing = _should_process_row(
                cell_value,
                start_marker,
                stop_marker,
                currently_processing
            )
            
            if should_process:
                rows_to_process.append((cell_value, cell.row))
            elif cell_value == start_marker:
                logger.debug(f"Found start marker at row {cell.row}")
            elif cell_value == stop_marker:
                logger.debug(f"Found stop marker at row {cell.row}")
        
        total_rows = len(rows_to_process)
        
        # ========== PHASE 3: Process Each Row ==========
        
        for idx, (ticker, row_num) in enumerate(rows_to_process):
            # Send progress update
            if progress_callback:
                progress_callback({
                    'current': idx + 1,
                    'total': total_rows,
                    'ticker': ticker,
                    'status': f'Processing {ticker}...',
                    'elapsed': time.time() - start_time,
                })
            
            # Process row
            success, error_msg = _process_single_row(
                ticker,
                row_num,
                worksheet,
                config,
                action_type,
            )
            
            if success:
                stats.tickers_updated += 1
                logger.debug(f"Row {row_num} ({ticker}): SUCCESS")
            else:
                stats.errors_count += 1
                error_type = 'TICKER_ERROR'
                
                # Categorize error
                if 'Invalid ticker' in error_msg or 'No data available' in error_msg:
                    error_type = 'INVALID_TICKER'
                elif 'Network' in error_msg or 'timeout' in error_msg:
                    error_type = 'NETWORK_ERROR'
                
                # Accumulate error
                if error_type not in errors_by_type:
                    errors_by_type[error_type] = ProcessingError(
                        error_type=error_type,
                        message=error_msg,
                        rows=[row_num]
                    )
                else:
                    errors_by_type[error_type].rows.append(row_num)
                
                logger.warning(f"Row {row_num} ({ticker}): {error_type} - {error_msg}")
        
        stats.rows_processed = total_rows
        
        # ========== PHASE 4: Save File ==========
        
        try:
            workbook.save(file_path)
            logger.info(f"Successfully saved {file_path}")
        except PermissionError:
            return (
                False,
                stats.to_dict(),
                {
                    'SAVE_ERROR': {
                        'message': (
                            'Cannot save file. Is it open in Excel? '
                            'Updated data was not saved.'
                        ),
                        'rows': list(range(1, stats.rows_processed + 1)),
                    }
                }
            )
        except Exception as e:
            return (
                False,
                stats.to_dict(),
                {
                    'SAVE_ERROR': {
                        'message': f'Failed to save file: {str(e)}',
                        'rows': list(range(1, stats.rows_processed + 1)),
                    }
                }
            )
        
        finally:
            workbook.close()
        
        # ========== PHASE 5: Return Results ==========
        
        stats.processing_time_seconds = time.time() - start_time
        
        # Convert errors to dict format
        errors_dict = {
            error_type: error.to_dict()
            for error_type, error in errors_by_type.items()
        }
        
        success = len(errors_by_type) == 0 or stats.tickers_updated > 0
        
        return (success, stats.to_dict(), errors_dict)
    
    except Exception as e:
        logger.exception(f"Unexpected error during processing: {e}")
        return (
            False,
            stats.to_dict(),
            {
                'PROCESSING_ERROR': {
                    'message': f'Unexpected error: {str(e)}',
                    'rows': [],
                }
            }
        )
