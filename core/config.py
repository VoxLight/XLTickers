"""
Configuration management for XLTickers.

Pure configuration module with no side effects.
Loads from INI file, validates, and provides access to settings.
"""

import configparser
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required keys."""
    pass


class Config:
    """
    Manages application configuration loaded from config.ini file.
    
    Design:
    - Immutable after loading (properties only)
    - No side effects (no logging, no printing during normal operation)
    - Validates on load, fails fast
    - Provides sensible defaults for missing values
    """
    
    # Default values for optional configuration
    DEFAULTS = {
        'rounding': 4,
    }
    
    # Required configuration keys
    REQUIRED_SECTIONS = ['XL', 'PRICE_UPDATER', 'ALERT_UPDATER', 'DATA']
    REQUIRED_KEYS = {
        'XL': ['start_word', 'stop_word', 'ticker_column'],
        'PRICE_UPDATER': ['price_column', 'date_column'],
        'ALERT_UPDATER': ['alert_date_column', 'alert_price_column'],
        'DATA': ['rounding'],
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from INI file.
        
        Args:
            config_path: Path to config.ini file. Defaults to project root.
            
        Raises:
            ConfigError: If file not found or configuration is invalid
        """
        if config_path is None:
            config_path = './config.ini'
        
        ini_file = Path(config_path)
        
        if not ini_file.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")
        
        parser = configparser.ConfigParser()
        try:
            parser.read(ini_file)
        except configparser.Error as e:
            raise ConfigError(f"Failed to parse configuration file: {e}")
        
        # Convert to dict and validate
        config_dict = {section: dict(parser[section]) for section in parser.sections()}
        
        # Validate required sections exist
        for section in self.REQUIRED_SECTIONS:
            if section not in config_dict:
                raise ConfigError(f"Missing required section: [{section}]")
        
        # Validate required keys in each section
        for section, keys in self.REQUIRED_KEYS.items():
            for key in keys:
                if key not in config_dict.get(section, {}):
                    raise ConfigError(f"Missing required key '{key}' in section [{section}]")
        
        # Apply defaults
        for key, value in self.DEFAULTS.items():
            if 'DATA' not in config_dict:
                config_dict['DATA'] = {}
            if key not in config_dict.get('DATA', {}):
                config_dict['DATA'][key] = str(value)
        
        self._config = config_dict
    
    # ==================== XL Settings ====================
    
    @property
    def start_marker(self) -> str:
        """Word that marks start of account block."""
        return self._config['XL']['start_word']
    
    @property
    def stop_marker(self) -> str:
        """Word that marks end of account block."""
        return self._config['XL']['stop_word']
    
    @property
    def ticker_column(self) -> str:
        """Excel column letter containing tickers (e.g., 'B')."""
        return self._config['XL']['ticker_column']
    
    # ==================== Price Updater Settings ====================
    
    @property
    def price_column(self) -> str:
        """Excel column letter for stock prices (e.g., 'K')."""
        return self._config['PRICE_UPDATER']['price_column']
    
    @property
    def date_column(self) -> str:
        """Excel column letter for update dates (e.g., 'U')."""
        return self._config['PRICE_UPDATER']['date_column']
    
    @property
    def price_updater_config(self) -> Dict[str, str]:
        """Return price updater configuration as dict."""
        return {
            'price_column': self.price_column,
            'date_column': self.date_column,
        }
    
    # ==================== Alert Updater Settings ====================
    
    @property
    def alert_date_column(self) -> str:
        """Excel column letter for alert dates."""
        return self._config['ALERT_UPDATER']['alert_date_column']
    
    @property
    def alert_price_column(self) -> str:
        """Excel column letter for alert prices."""
        return self._config['ALERT_UPDATER']['alert_price_column']
    
    @property
    def alert_updater_config(self) -> Dict[str, str]:
        """Return alert updater configuration as dict."""
        return {
            'alert_date_column': self.alert_date_column,
            'alert_price_column': self.alert_price_column,
        }
    
    # ==================== Data Settings ====================
    
    @property
    def rounding_precision(self) -> int:
        """Decimal places for rounding prices."""
        try:
            return int(self._config['DATA']['rounding'])
        except (ValueError, KeyError):
            return self.DEFAULTS['rounding']
    
    @property
    def price_decimals(self) -> int:
        """Alias for rounding_precision"""
        return self.rounding_precision
    
    @property
    def cache_enabled(self) -> bool:
        """Whether caching is enabled (always True for now)"""
        return True
    
    @property
    def api_timeout(self) -> int:
        """API timeout in seconds"""
        return 10
    
    @property
    def backup_retention(self) -> int:
        """Number of backup files to keep (0 = keep all)"""
        try:
            return int(self._config.get('DATA', {}).get('backup_retention', 2))
        except (ValueError, KeyError):
            return 2
    
    # ==================== Utility Methods ====================
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return entire configuration as dictionary."""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return (
            f"Config("
            f"ticker_col={self.ticker_column}, "
            f"price_col={self.price_column}, "
            f"rounding={self.rounding_precision}"
            f")"
        )

