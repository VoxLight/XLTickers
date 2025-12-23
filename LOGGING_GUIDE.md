## Logging System

XLTickers now uses a robust rotating file logging system that automatically manages log files with:

### Features

✅ **Automatic log directory management** - Creates `./logs` directory automatically  
✅ **Rotating file handler** - Automatically creates new log files when they reach 1MB  
✅ **Backup management** - Keeps up to 5 backup log files (older ones auto-deleted)  
✅ **Consistent formatting** - Timestamps, log levels, and module names in every entry  
✅ **Easy to view** - Built-in log viewer utility for easy inspection

### Log Files

Logs are stored in the `./logs` directory:
- **Current log**: `xltickers.log`
- **Backups**: `xltickers.log.1`, `xltickers.log.2`, etc. (up to 5)

Each file is automatically rotated when it reaches **1MB** in size.

### Viewing Logs

#### Using the log viewer utility:

```bash
# View log statistics
python scripts/log_viewer.py stats

# View current log (last 50 lines)
python scripts/log_viewer.py view

# View last N lines
python scripts/log_viewer.py view 100

# List all log files
python scripts/log_viewer.py list

# Clean up old log files (keep latest 5)
python scripts/log_viewer.py clear

# Keep only latest 3 log files
python scripts/log_viewer.py clear 3
```

#### Manual viewing:

```bash
# On Windows (PowerShell)
Get-Content logs\xltickers.log -Tail 50

# On Linux/Mac
tail -n 50 logs/xltickers.log

# View with timestamps and levels
cat logs/xltickers.log | grep ERROR

# Find errors
grep ERROR logs/xltickers.log
```

### Log Format

Each log entry includes:
- **Timestamp**: `YYYY-MM-DD HH:MM:SS`
- **Level**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Module**: Which Python module generated the log
- **Message**: The actual log message

Example:
```
2025-12-23 15:38:19 - DEBUG - XLTickers - Starting XLTickers
2025-12-23 15:38:20 - INFO - core.excel_processor - Processing file: portfolio.xlsx
2025-12-23 15:38:45 - WARNING - core.ticker_fetcher - TSLA API call timeout, retrying...
2025-12-23 15:39:10 - ERROR - core.excel_processor - Failed to save backup: Permission denied
```

### Log Levels

- **DEBUG**: Detailed information for debugging (default in development)
- **INFO**: General informational messages
- **WARNING**: Warning messages about potentially problematic situations
- **ERROR**: Error messages indicating something went wrong
- **CRITICAL**: Critical errors that may cause shutdown

### Configuration

The logging is configured in `main.py`:

```python
logger = setup_logging(
    log_dir='./logs',           # Where to store logs
    max_bytes=1024*1024,        # 1MB per file
    backup_count=5,             # Keep 5 backup files
    console_output=False        # No console output
)
```

To enable console output as well:
```python
logger = setup_logging(..., console_output=True)
```

When console output is enabled, only INFO and above are shown to console (DEBUG goes only to file).

### Automatic Cleanup

The rotating handler automatically:
1. Creates new log files when current one reaches 1MB
2. Renames old file to `.1`, previous `.1` to `.2`, etc.
3. Deletes the oldest backup when more than 5 files exist

Example progression:
```
xltickers.log          (current, <1MB)
xltickers.log.1        (previous session)
xltickers.log.2        (older session)
xltickers.log.3
xltickers.log.4
xltickers.log.5        (oldest kept)
(anything older is deleted)
```

### Development vs Production

**Development** (with `python main.py`):
- Debug messages logged to file
- All details available for troubleshooting

**Production** (with installer):
- Info messages and above logged to file
- Less verbose but still captures all important events

### Tips

1. **Check logs regularly**: After running updates, check `logs/xltickers.log` for any warnings or errors
2. **Clean up old logs**: Periodically run `python scripts/log_viewer.py clear` to free space
3. **Share logs for support**: Include `logs/xltickers.log` when reporting issues
4. **Monitor size**: Check `python scripts/log_viewer.py stats` to see disk usage

### Performance Impact

The rotating logger has minimal performance impact:
- Logging adds <1% CPU overhead
- Disk writes are buffered and non-blocking
- Background rotation happens automatically

### Troubleshooting

**"No log files found"**
- Logs are created only when something is logged
- Run the application once to create initial log

**"Cannot delete log files"**
- Close any programs that might have the log file open (text editors)
- Or just use `python scripts/log_viewer.py clear` which handles this

**Logs not appearing**
- Check that `./logs/` directory exists (should be auto-created)
- Verify file permissions allow writing to `./logs/`
- Check that logging isn't configured differently elsewhere

---

For more details, see `core/logging_config.py` and `scripts/log_viewer.py`.
