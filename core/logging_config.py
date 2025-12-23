"""
Logging configuration module for XLTickers.

Provides robust rotating file logging with:
- Automatic log directory creation
- Rotating file handler (max 1MB per file, keeps 5 backups)
- Consistent timestamp formatting
- Both file and optional console output
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_dir: str = './logs',
    max_bytes: int = 1024 * 1024,  # 1MB
    backup_count: int = 5,
    level: int = logging.DEBUG,
    console_output: bool = False
) -> logging.Logger:
    """
    Configure rotating file logging for the application.
    
    Args:
        log_dir: Directory to store log files (created if doesn't exist)
        max_bytes: Maximum size of a log file before rotation (default 1MB)
        backup_count: Number of backup log files to keep (default 5)
        level: Logging level (default DEBUG)
        console_output: Also output to console if True
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging()
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('XLTickers')
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler
    log_file = log_path / 'xltickers.log'
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Optionally add console output
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Only INFO and above to console
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = 'XLTickers') -> logging.Logger:
    """
    Get the configured logger instance.
    
    Args:
        name: Logger name (default 'XLTickers')
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger()
        >>> logger.debug("Debug message")
    """
    return logging.getLogger(name)


def get_log_directory(log_dir: str = './logs') -> Path:
    """
    Get the log directory path (creates if doesn't exist).
    
    Args:
        log_dir: Log directory path
    
    Returns:
        Path object for log directory
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def get_latest_log(log_dir: str = './logs') -> Path:
    """
    Get the path to the latest/current log file.
    
    Args:
        log_dir: Log directory path
    
    Returns:
        Path to the current log file
    """
    log_path = get_log_directory(log_dir)
    return log_path / 'xltickers.log'


def list_log_files(log_dir: str = './logs') -> list:
    """
    List all log files in the log directory.
    
    Args:
        log_dir: Log directory path
    
    Returns:
        List of log file paths, sorted by modification time (newest first)
    """
    log_path = get_log_directory(log_dir)
    log_files = sorted(
        log_path.glob('xltickers.log*'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return log_files


def get_log_stats(log_dir: str = './logs') -> dict:
    """
    Get statistics about log files.
    
    Args:
        log_dir: Log directory path
    
    Returns:
        Dictionary with log file counts and sizes
    """
    log_files = list_log_files(log_dir)
    total_size = sum(f.stat().st_size for f in log_files)
    
    return {
        'log_count': len(log_files),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'log_files': [
            {
                'name': f.name,
                'size_bytes': f.stat().st_size,
                'size_kb': round(f.stat().st_size / 1024, 2),
                'modified': datetime.fromtimestamp(f.stat().st_mtime)
            }
            for f in log_files
        ]
    }


# Module-level logger (initialized on first use)
_default_logger = None


def initialize_default_logger(**kwargs):
    """Initialize the module-level default logger."""
    global _default_logger
    _default_logger = setup_logging(**kwargs)
    return _default_logger


if __name__ == '__main__':
    # Example usage
    logger = setup_logging(console_output=True)
    
    logger.debug("This is a debug message")
    logger.info("Application started")
    logger.warning("This is a warning")
    logger.error("This is an error message")
    
    # Show log statistics
    stats = get_log_stats()
    print(f"\nLog Statistics:")
    print(f"  Total log files: {stats['log_count']}")
    print(f"  Total size: {stats['total_size_mb']} MB")
    print(f"  Log files:")
    for log_info in stats['log_files']:
        print(f"    - {log_info['name']}: {log_info['size_kb']} KB")
