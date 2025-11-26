# Project Structure

This document describes the organization of the Periscope Control Interface project.

## Directory Layout

```
dummy_interface_cdwl/
├── src/                          # Main source code package
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration settings
│   ├── gui.py                   # Main GUI application
│   ├── periscope_controller.py # Hardware controller wrapper
│   ├── file_monitor.py          # File system monitoring
│   └── visualizer.py            # Visualization components
│
├── sandbox/                      # Sandbox/testing environment
│   ├── __init__.py              # Package initialization
│   ├── mock_controller.py       # Mock hardware controller
│   ├── create_test_data.py     # Test data generator script
│   ├── README.md               # Sandbox documentation
│   └── results/                 # Generated test results (gitignored)
│       └── run_*/              # Test run directories
│
├── tests/                        # Unit tests (optional, for future use)
│
├── data/                         # Data directory
│   └── results/                 # Production analysis results
│       └── run_*/              # Analysis run directories
│
├── periscope_software/          # Periscope software suite (external)
│   ├── dist/                   # Compiled executables
│   │   ├── Periscope Control System.exe
│   │   ├── Wind Positioner.exe
│   │   └── system_configuration.txt
│   └── ...                     # Other software files
│
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # Main project documentation
├── PROJECT_STRUCTURE.md         # This file
└── .gitignore                  # Git ignore rules
```

## Module Descriptions

### Source Code (`src/`)

- **`config.py`**: Central configuration file containing:
  - Paths to periscope software
  - Results directory configuration
  - File pattern definitions
  - Sandbox mode settings

- **`gui.py`**: Main GUI application implementing:
  - Two-column layout (control panel + visualization)
  - Event handlers for all controls
  - Status updates and error handling
  - Integration with controller and visualizer

- **`periscope_controller.py`**: Wrapper for periscope terminal commands:
  - Executes commands via subprocess
  - Parses terminal output
  - Manages connection state
  - Provides high-level control methods

- **`file_monitor.py`**: Monitors results directory:
  - Detects new analysis files
  - Maintains list of available runs
  - Uses watchdog for file system events
  - Supports both production and sandbox directories

- **`visualizer.py`**: Handles result visualization:
  - Loads images, text, and data files
  - Creates matplotlib plots
  - Manages current run state
  - Error handling for file operations

### Sandbox (`sandbox/`)

- **`mock_controller.py`**: Simulates periscope hardware:
  - Implements same interface as real controller
  - Simulates motion and responses
  - Provides realistic timing
  - Safe for testing without hardware

- **`create_test_data.py`**: Generates test analysis results:
  - Creates sample run directories
  - Generates CSV data files
  - Creates plot images
  - Generates summary text files

### Data Directories

- **`data/results/`**: Production analysis results from external software
- **`sandbox/results/`**: Test data for sandbox mode (gitignored)

## Usage Patterns

### Development Workflow

1. **Normal Development**: Work with real hardware
   ```bash
   python main.py
   ```

2. **Sandbox Testing**: Test without hardware
   ```bash
   $env:SANDBOX_MODE="true"
   python main.py
   ```

3. **Generate Test Data**: Create sample results
   ```bash
   python sandbox/create_test_data.py
   ```

## Import Structure

All source modules use relative imports within the `src` package:

```python
from . import config
from .periscope_controller import PeriscopeController
from .file_monitor import FileMonitor
from .visualizer import Visualizer
```

The main entry point imports from `src`:

```python
from src.gui import PeriscopeGUI
from src import config
```

## Configuration Flow

1. `src/config.py` defines all settings
2. Sandbox mode can be enabled via:
   - Environment variable: `SANDBOX_MODE=true`
   - Config file: `SANDBOX_MODE = True`
3. Results directory automatically switches based on sandbox mode
4. File monitor uses appropriate directory for current mode

## File Naming Conventions

- **Run directories**: `run_YYYYMMDD_HHMMSS/`
- **Data files**: `data_*.csv`
- **Plot files**: `analysis_*.png`
- **Summary files**: `summary_*.txt`

Patterns are configurable in `src/config.py`.

