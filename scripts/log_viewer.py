"""
Log viewer and management utility for XLTickers.

Usage:
    python -m scripts.log_viewer list    # List all log files
    python -m scripts.log_viewer view    # View current log file
    python -m scripts.log_viewer stats   # Show log statistics
    python -m scripts.log_viewer clear   # Clear old log files (keep latest 5)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logging_config import list_log_files, get_log_stats, get_latest_log, get_log_directory


def list_logs():
    """List all log files with their sizes."""
    log_files = list_log_files()
    
    if not log_files:
        print("No log files found.")
        return
    
    print(f"\nLog Files ({len(log_files)} total):")
    print("-" * 70)
    
    for i, log_file in enumerate(log_files, 1):
        size_kb = log_file.stat().st_size / 1024
        modified = log_file.stat().st_mtime
        from datetime import datetime
        mod_time = datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')
        
        marker = " <- current" if i == 1 else ""
        print(f"{i}. {log_file.name:<25} {size_kb:>8.2f} KB  {mod_time}{marker}")


def view_logs(lines: int = 50):
    """View the current log file (last N lines)."""
    log_file = get_latest_log()
    
    if not log_file.exists():
        print("No log file found yet.")
        return
    
    print(f"\nCurrent Log File: {log_file}")
    print(f"Size: {log_file.stat().st_size / 1024:.2f} KB")
    print("-" * 70)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # Show last N lines
        display_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        if len(all_lines) > lines:
            print(f"(Showing last {lines} of {len(all_lines)} lines)\n")
        
        for line in display_lines:
            print(line.rstrip())
    
    except Exception as e:
        print(f"Error reading log file: {e}")


def show_stats():
    """Show log statistics."""
    stats = get_log_stats()
    
    print(f"\nLog Statistics:")
    print("-" * 70)
    print(f"Total log files: {stats['log_count']}")
    print(f"Total size: {stats['total_size_mb']} MB")
    print(f"Log directory: {get_log_directory()}\n")
    
    if stats['log_files']:
        print("Details:")
        for i, log_info in enumerate(stats['log_files'], 1):
            marker = " <- current" if i == 1 else ""
            print(f"  {i}. {log_info['name']:<25} {log_info['size_kb']:>8.2f} KB  {log_info['modified']}{marker}")
    else:
        print("No log files found.")


def clear_logs(keep: int = 5):
    """Remove old log files, keeping only the most recent N."""
    log_files = list_log_files()
    
    if len(log_files) <= keep:
        print(f"Only {len(log_files)} log file(s) exist. Keeping all.")
        return
    
    to_delete = log_files[keep:]
    
    print(f"\nRemoving {len(to_delete)} old log file(s), keeping {keep}:")
    print("-" * 70)
    
    for log_file in to_delete:
        size_kb = log_file.stat().st_size / 1024
        try:
            log_file.unlink()
            print(f"✓ Deleted {log_file.name} ({size_kb:.2f} KB)")
        except Exception as e:
            print(f"✗ Failed to delete {log_file.name}: {e}")
    
    print(f"\nDone. {len(log_files) - len(to_delete)} log file(s) remaining.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_logs()
    elif command == 'view':
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        view_logs(lines)
    elif command == 'stats':
        show_stats()
    elif command == 'clear':
        keep = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        clear_logs(keep)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
