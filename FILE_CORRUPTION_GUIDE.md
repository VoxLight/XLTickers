# File Corruption Troubleshooting

## What Happened

When trying to load an Excel file with openpyxl, you got:
```
KeyError: "There is no item named '[Content_Types].xml' in the archive"
```

This means the Excel file (which is a .zip archive internally) is corrupted.

## Why This Happened

Excel files are actually ZIP archives. The error means the ZIP structure is corrupted:
- Missing internal XML files
- Incomplete write
- File was interrupted during creation/saving

## How to Prevent It

### 1. Close Excel Files
```powershell
# Close Excel completely before running updates
taskkill /IM EXCEL.EXE /F
```

### 2. Check Disk Space
```powershell
# Ensure enough space for backup files
Get-Volume | Where {$_.DriveLetter -eq 'C'} | Select SizeRemaining
```

### 3. Verify File Permissions
```powershell
# Check if you can write to the folder
Test-Path "C:\Path\To\Excel\Folder" -PathShouldExist
```

### 4. Use Unproblematic Files
- Start with the original test file
- Ensure it's not locked
- Try smaller files first

## If a File is Already Corrupted

### Option 1: Delete Corrupted Backup
```powershell
# List all backups
dir "C:\Path\*_*.xlsx"

# Delete the corrupted ones
Remove-Item "C:\Path\Corrupted_File_2025-12-21_141650.xlsx"
```

### Option 2: Recover from Last Good Backup
```powershell
# Find the most recent backup that's not corrupted
dir "C:\Path\Original_*_*.xlsx" | Sort LastWriteTime | Select -Last 1

# Use that as your working file
Copy-Item "C:\Path\Original_2025-12-21_120000.xlsx" -Destination "C:\Path\working_copy.xlsx"
```

### Option 3: Start Fresh
If all backups are corrupted:
1. Delete all backup files
2. Use the original file
3. Make a fresh backup by running the updater

## Configuration to Reduce Issues

The backup retention is now set to **2** files by default:
```ini
[DATA]
backup_retention = 2
```

This means:
- You'll have at most 2 backup files
- Less disk I/O = less chance of corruption
- More aggressive cleanup of old backups
- Faster operations

### To Change Retention

Edit `config.ini`:
```ini
[DATA]
backup_retention = 1  # Only keep current
backup_retention = 2  # Keep current + 1 (DEFAULT)
backup_retention = 3  # Keep current + 2
backup_retention = 0  # Keep all (not recommended)
```

## Error Handling Improvements

The backup system now:
1. ✅ Cleans up old backups BEFORE saving new one
2. ✅ Validates save operation
3. ✅ Removes incomplete backup files if save fails
4. ✅ Returns detailed error messages
5. ✅ Never leaves corrupted files in place

## Testing Your Setup

### Test 1: Verify Config
```bash
python -c "from core.config import Config; print(f'Retention: {Config().backup_retention}')"
# Should output: Retention: 2
```

### Test 2: Test Backup System
```bash
python -m pytest tests/test_core_modules.py::TestExcelProcessor -v
# Should show all tests passing
```

### Test 3: Manual Backup Test
```bash
python test_phase1_1_full.py
# Should create timestamped backups without errors
```

## Getting Help

If corruption persists:
1. Check for error messages in the terminal output
2. Look for permission issues (file locked, read-only)
3. Ensure Excel is closed
4. Try with a clean copy of the original file
5. Check available disk space

---

**Updated**: 2025-12-21  
**Backup Retention Default**: 2 files  
**Configuration**: config.ini [DATA] section
