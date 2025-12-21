import sys
sys.path.insert(0, '.')

from core.config import Config
from core.excel_processor import process_excel

# Test with test_data.xlsx
config = Config()
print('Testing excel_processor with test_data.xlsx (with markers)...')
success, stats, errors = process_excel(
    file_path='test_data.xlsx',
    config=config,
    action_type='price'
)

print(f'✓ Success: {success}')
print(f"  Rows processed: {stats['rows_processed']}")
print(f"  Tickers updated: {stats['tickers_updated']}")
print(f"  Rows skipped: {stats['rows_skipped']}")
if errors:
    print(f'  Errors: {errors}')
else:
    print('  No errors')
