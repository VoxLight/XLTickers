# XLTickers Desktop App Migration Plan

## Project Overview
Transform XLTickers from a CLI-based tool to a professional desktop application with:
- Modern dark-themed GUI using CustomTkinter
- One-click file processing with progress tracking
- Robust error handling and user feedback
- PyInstaller packaging support
- Inno Setup Windows installer integration

---

## Current Architecture Analysis

### Existing Components
- **libs/stock_data.py**: Fetches ticker prices from yfinance (cached)
- **scripts/price_updater.py**: Core logic to update Excel cells with prices
- **libs/toucher.py**: Iterates through Excel rows between "start"/"stop" markers
- **libs/opener.py**: File selection dialog (already uses tkinter)
- **libs/menu.py**: CLI-based menu system
- **main.py**: CLI entry point
- **config.ini**: Configuration (column mappings, rounding)

### Decoupling Needed
- Remove dependency on `input()` and `print()` for flow control
- Extract pure logic from CLI presentation layer
- Create a business logic layer for Excel operations
- Maintain configuration system

---

## New Project Structure

```
XLTickers/
├── main.py                      # GUI entry point (replaces current main.py)
├── gui/
│   ├── __init__.py
│   ├── app.py                   # Main application window (CustomTkinter)
│   ├── theme.py                 # Dark theme configuration
│   └── widgets/
│       ├── __init__.py
│       ├── file_browser.py      # File selection widget
│       ├── progress_bar.py      # Custom progress indicator
│       └── result_panel.py       # Results/errors display
├── core/
│   ├── __init__.py
│   ├── excel_processor.py        # Refactored Excel logic (no CLI)
│   ├── ticker_fetcher.py         # Refactored yfinance logic
│   └── config.py                 # Config management (replaces libs/common.py)
├── libs/                         # Existing utilities (gradually migrate)
│   ├── __init__.py
│   ├── common.py                 # Keep for now, gradually deprecate
│   ├── stock_data.py             # Keep, gradually refactor
│   ├── toucher.py                # Keep, gradually refactor
│   └── ...
├── scripts/                      # Keep existing
│   └── ...
├── assets/
│   ├── icon.ico                 # App icon for taskbar/installer
│   └── logo.png                 # For GUI
├── config.ini                    # Keep existing configuration
├── requirements.txt              # Updated dependencies
├── requirements-dev.txt          # Development dependencies
├── setup.py                      # For PyInstaller hooks
├── installer/
│   └── XLTickers.iss             # Inno Setup script
└── README.md                     # Updated documentation
```

---

## Phase 1: Core Logic Decoupling

### 1.1 Create `core/config.py`
- Migrate configuration management from `libs/common.py`
- Make it pure configuration (no globals, no print statements)
- Support both INI file and GUI parameter passing

### 1.2 Create `core/ticker_fetcher.py`
- Refactor `libs/stock_data.py` logic
- Remove print statements and logging from core logic
- Return tuples of (success: bool, price: float, date: date, error_msg: str)
- Implement caching as before

### 1.3 Create `core/excel_processor.py`
- Refactor `scripts/price_updater.py` and `libs/toucher.py`
- Core function: `process_excel(file_path, action_type, callback=None)`
- Callback receives progress updates: `(current_row, total_rows, status_msg)`
- Return: `(success: bool, results: dict, errors: dict)`

---

## Phase 2: GUI Foundation (CustomTkinter)

### 2.1 Create `gui/theme.py`
- Define dark color palette (modern professional)
- Setup color constants for consistent styling
- Define fonts and sizes

### 2.2 Create `gui/app.py` (Main Window)
**Layout:**
```
┌─────────────────────────────────────┐
│ XLTickers - Ticker Price Updater    │  (Title bar)
├─────────────────────────────────────┤
│                                     │
│  📁 Selected File:                  │  (Label)
│  [C:\Users\...\data.xlsx          ]│  (File path display)
│  [Browse...]                       │  (Browse button)
│                                     │
│  Select Action:                     │  (Label)
│  ◉ Update Prices      ○ Update      │  (Radio buttons)
│                                     │
│  [                RUN               ]│  (Large Run button)
│                                     │
├─────────────────────────────────────┤
│ ████████░░ 45%  (45/100 rows)       │  (Progress bar)
│                                     │
│ Status: Processing ticker AAPL...   │  (Status label)
│                                     │
│ Results:                            │  (Results panel)
│ ✓ 87 tickers updated successfully   │
│ ⚠ 3 tickers failed (details...)     │
│ ⓘ 10 rows skipped                   │
│                                     │
│ [Errors] [Save] [Close]             │  (Action buttons)
│                                     │
└─────────────────────────────────────┘
```

### 2.3 Create `gui/widgets/file_browser.py`
- Widget for file selection and display
- Browse button with file dialog
- Display selected file path with validation indicator

### 2.4 Create `gui/widgets/progress_bar.py`
- CustomTkinter progress bar with percentage
- Real-time status updates
- Animated/smooth updates

### 2.5 Create `gui/widgets/result_panel.py`
- Display results summary
- Show errors with expandable details
- Warnings and success counts

---

## Phase 3: Application Logic Integration

### 3.1 Create `main.py` (New Entry Point)
```python
from gui.app import Application
if __name__ == "__main__":
    app = Application()
    app.run()
```

### 3.2 Refactor `gui/app.py` for Threading
- Run Excel processing in background thread (prevents UI freezing)
- Use `threading.Thread` or `concurrent.futures.ThreadPoolExecutor`
- Queue-based communication between worker thread and GUI
- Graceful cancellation support

### 3.3 Error Handling Strategy
```python
class ProcessingError(Exception):
    """Base exception for processing errors"""
    
class FileAccessError(ProcessingError):
    """File is open or inaccessible"""
    
class TickerError(ProcessingError):
    """Invalid ticker or network error"""
    
class ConfigError(ProcessingError):
    """Configuration issue"""
```

---

## Phase 4: Dependencies & Packaging

### 4.1 Update `requirements.txt`
```
openpyxl          # Excel reading/writing
yfinance           # Stock data
pandas             # Data processing
customtkinter      # Modern GUI
pillow             # Image handling (icons)
```

### 4.2 Create `requirements-dev.txt`
```
pyinstaller        # Packaging
pyinstaller-hooks-contrib
```

### 4.3 Create `setup.py`
- Define PyInstaller hooks
- Configure binary paths
- Icon/asset inclusion

### 4.4 Create `installer/XLTickers.iss`
- Inno Setup script for Windows installer
- Installation directory configuration
- Start menu shortcuts
- Uninstaller support

---

## Phase 5: Enhancement & Polish

### 5.1 Advanced Features
- [ ] Drag-and-drop file selection
- [ ] Recent files list
- [ ] Settings/preferences dialog
- [ ] About dialog
- [ ] Export results to CSV
- [ ] Undo/Redo capability

### 5.2 Performance Optimizations
- [ ] Lazy loading of ticker data
- [ ] Batch API requests to yfinance
- [ ] Caching with TTL
- [ ] Progress estimation

### 5.3 User Experience
- [ ] Keyboard shortcuts
- [ ] Tooltip help text
- [ ] Dark/Light theme toggle
- [ ] Application logging to file
- [ ] Crash report generation

---

## Implementation Sequence

### Week 1: Foundation
1. **Day 1-2**: Create core logic modules (config, ticker_fetcher, excel_processor)
2. **Day 3-4**: Build basic GUI structure and theme
3. **Day 5**: Integrate core logic with GUI, test basic flow

### Week 2: Polish & Packaging
1. **Day 1-2**: Error handling and edge cases
2. **Day 3-4**: Progress bar integration and threading
3. **Day 5**: PyInstaller setup and Inno Setup script

### Week 3: Testing & Deployment
1. Full end-to-end testing
2. Performance optimization
3. Create Windows installer
4. Documentation and release

---

## Key Design Principles

1. **Separation of Concerns**
   - GUI logic separate from business logic
   - No print/input in core modules
   - Testable components

2. **Error Resilience**
   - Graceful handling of missing files
   - Validation before processing
   - Informative error messages to user

3. **Responsiveness**
   - Threading for long operations
   - Real-time progress updates
   - Cancellation support

4. **Maintainability**
   - Clean code structure
   - Type hints where applicable
   - Comprehensive logging
   - Configuration-driven behavior

---

## Success Criteria

✓ Single-click Excel file update experience
✓ Professional, dark-themed GUI
✓ Handles large files without freezing
✓ Comprehensive error messages
✓ Standalone .exe executable
✓ Professional Windows installer
✓ Configuration preserved from original
✓ No external dependencies visible to user
