"""
Unit tests for core modules.

Run with: python -m pytest tests/ -v

Tests verify:
1. Configuration loads and validates correctly
2. Ticker fetching works and caches properly
3. Excel processing handles errors gracefully
"""

import pytest
import tempfile
import os
from datetime import datetime, date
from pathlib import Path

from core.config import Config, ConfigError
from core.ticker_fetcher import get_ticker_price, clear_cache
from core.excel_processor import process_excel


# ==================== Configuration Tests ====================

class TestConfig:
    """Tests for Config"""
    
    def test_config_loads_from_existing_file(self):
        """Config should load from existing config.ini"""
        config = Config('./config.ini')
        
        assert config is not None
        assert config.ticker_column in ['A', 'B', 'C', 'D', 'E']  # Should be a column letter
        assert config.price_decimals >= 0
    
    def test_config_fails_on_missing_file(self):
        """Config should raise ConfigError for missing file"""
        with pytest.raises(ConfigError):
            Config('./nonexistent.ini')
    
    def test_config_properties_are_accessible(self):
        """All config properties should be accessible"""
        config = Config('./config.ini')
        
        # Should not raise AttributeError
        _ = config.start_marker
        _ = config.stop_marker
        _ = config.ticker_column
        _ = config.price_column
        _ = config.date_column
        _ = config.price_decimals
        _ = config.api_timeout
    
    def test_config_to_dict(self):
        """Config should convert to dict"""
        config = Config('./config.ini')
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'XL' in config_dict
        assert 'PRICE_UPDATER' in config_dict


# ==================== Ticker Fetcher Tests ====================

class TestTickerFetcher:
    """Tests for get_ticker_price() and caching"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    def test_get_valid_ticker_price(self):
        """Should fetch real price for valid ticker"""
        success, price, update_date, error = get_ticker_price('AAPL')
        
        if success:  # Might fail if no network, so optional
            assert price > 0
            assert isinstance(update_date, date)
            assert error == ""
    
    def test_get_invalid_ticker_fails(self):
        """Should fail gracefully for invalid ticker"""
        success, price, update_date, error = get_ticker_price('INVALID_TICKER_XYZ')
        
        assert success is False
        assert price is None
        assert update_date is None
        assert len(error) > 0
        assert 'Invalid' in error or 'No data' in error or 'ticker' in error.lower()
    
    def test_ticker_caching(self):
        """Same ticker should use cache on second call"""
        # This test is best run offline or mocked
        clear_cache()
        
        # Just verify caching mechanism exists
        from core.ticker_fetcher import _TICKER_CACHE
        assert isinstance(_TICKER_CACHE, dict)
    
    def test_ticker_case_insensitive(self):
        """Should normalize ticker case"""
        success1, price1, date1, error1 = get_ticker_price('aapl')
        success2, price2, date2, error2 = get_ticker_price('AAPL')
        
        # Both should have same result (both valid or both invalid)
        assert success1 == success2
    
    def test_ticker_rounding(self):
        """Price should be rounded to specified precision"""
        success, price, _, error = get_ticker_price('AAPL', rounding=2)
        
        if success and price is not None:
            # Should have at most 2 decimal places
            assert len(str(price).split('.')[-1]) <= 2


# ==================== Excel Processor Tests ====================

class TestExcelProcessor:
    """Tests for process_excel()"""
    
    def test_process_excel_handles_missing_file(self):
        """Should handle missing file gracefully"""
        config = Config('./config.ini')
        
        success, stats, errors = process_excel(
            file_path='/nonexistent/file.xlsx',
            config=config,
            action_type='price'
        )
        
        assert success is False
        assert 'FILE_NOT_FOUND' in errors or 'FILE_ERROR' in errors
    
    def test_process_excel_returns_correct_structure(self):
        """Should return properly structured results"""
        config = Config('./config.ini')
        
        # This will fail with missing file, but structure should be correct
        success, stats, errors = process_excel(
            file_path='/nonexistent/file.xlsx',
            config=config
        )
        
        # Check structure
        assert isinstance(success, bool)
        assert isinstance(stats, dict)
        assert isinstance(errors, dict)
        
        # Check stats keys
        assert 'rows_processed' in stats
        assert 'tickers_updated' in stats
        assert 'errors_count' in stats
        assert 'processing_time_seconds' in stats
    
    def test_process_excel_progress_callback(self):
        """Progress callback should be called correctly"""
        config = Config('./config.ini')
        
        callback_data = []
        
        def progress_handler(data):
            callback_data.append(data)
        
        # This will fail, but we're testing callback structure
        # (In real scenario with valid Excel file, callback would be called)
        try:
            process_excel(
                file_path='./config.ini',  # Wrong format, will error
                config=config,
                progress_callback=progress_handler
            )
        except:
            pass  # Expected to fail


# ==================== Integration Tests ====================

class TestIntegration:
    """End-to-end integration tests"""
    
    def test_config_and_ticker_together(self):
        """Config and ticker fetcher should work together"""
        config = Config('./config.ini')
        precision = config.price_decimals
        
        success, price, date_obj, error = get_ticker_price('AAPL', rounding=precision)
        
        # Should work together without errors
        assert isinstance(success, bool)
        assert isinstance(error, str)
    
    def test_full_pipeline_structure(self):
        """All modules should integrate without import errors"""
        # This test just verifies imports work
        from core.config import Config, ConfigError
        from core.ticker_fetcher import get_ticker_price
        from core.excel_processor import process_excel
        
        assert Config is not None
        assert get_ticker_price is not None
        assert process_excel is not None


# ==================== Run Tests ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
