# Periscope Control Interface

A minimal graphical interface for controlling a coherent Doppler wind lidar periscope subsystem and visualizing externally processed analysis results.

## Features

- **Left Panel**: Periscope control interface wrapping existing terminal commands
  - Connection management (connect/disconnect)
  - Initialization and homing
  - Azimuth and elevation controls (jog and set angles)
  - **Line-of-Sight (LOS) Mode**: Point to exact direction with azimuth offset
  - Status indicators (connection, motion, limits, errors)
  - Console log for terminal output
  - Manual command input (advanced)

- **Right Panel**: Visualization of externally processed results
  - **LOS Mode Heatmap**: Real-time range profile heatmap (0-12 km, 60-minute sliding window)
  - Automatic detection of new analysis files
  - File browser for selecting previous runs
  - Refresh mechanism for latest data
  - Plot visualization components
  - Status indicators (new data available, file loaded, etc.)

### Line-of-Sight (LOS) Mode

LOS mode allows precise pointing to a specific direction:
1. **Input Parameters**:
   - Elevation angle (degrees)
   - Azimuth angle (degrees, relative to true north)
   - Azimuth offset (degrees, system's offset from true north)

2. **Automatic Operations**:
   - Periscope moves to exact pointing direction
   - System scans for most recent `_Peak.txt` file
   - Captures timestamp from last entry
   - Begins real-time heatmap visualization

3. **Heatmap Visualization**:
   - X-axis: Time (human-readable + UTC labels)
   - Y-axis: Range (0 to 12 km, fixed)
   - 60-minute sliding window (most recent data)
   - Continuous automatic updates as new data arrives
   - Data shifts right-to-left with new entries at right boundary

## Requirements

- Python 3.8+ (tkinter is included with Python on most systems)
- Existing periscope terminal application
- External analysis software that writes results to a known directory structure

## Installation

```bash
pip install -r requirements.txt
```

**Note**: If tkinter is not available on your system, install it using your system package manager:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- macOS: tkinter is included with Python
- Windows: tkinter is included with Python

## Configuration

The periscope software suite is located in the `periscope_software/` directory. The configuration in `config.py` automatically references:
- `periscope_software/dist/Periscope Control System.exe` - The main executable
- `periscope_software/dist/system_configuration.txt` - System configuration (must be alongside executable)

Before running, you may need to configure in `config.py`:
- Directory where external analysis results are written (`RESULTS_DIR`)
- Expected file naming patterns (`RESULT_FILE_PATTERNS`)

## Usage

### Normal Mode

```bash
python main.py
```

### Sandbox Mode (Testing without hardware)

```bash
# Windows PowerShell
$env:SANDBOX_MODE="true"
python main.py

# Linux/Mac
export SANDBOX_MODE=true
python main.py
```

Or set `SANDBOX_MODE = True` in `src/config.py`.

See `sandbox/README.md` for more details on sandbox mode.

## Project Structure

```
.
├── src/                    # Main source code
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── gui.py             # Main GUI application
│   ├── periscope_controller.py  # Hardware controller wrapper
│   ├── file_monitor.py    # File system monitoring
│   └── visualizer.py      # Visualization components
├── sandbox/               # Sandbox/testing environment
│   ├── mock_controller.py # Mock hardware controller
│   ├── create_test_data.py # Test data generator
│   └── results/           # Sandbox test results (generated)
├── tests/                 # Unit tests (optional)
├── data/                  # Data directory
│   └── results/           # Analysis results (production)
├── periscope_software/    # Periscope software suite
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Architecture

- `main.py`: Main application entry point
- `src/gui.py`: GUI layout and event handling
- `src/periscope_controller.py`: Wrapper for terminal commands (includes LOS mode)
- `src/file_monitor.py`: Monitors analysis result directory for new files
- `src/visualizer.py`: Handles loading and displaying analysis results
- `src/heatmap_visualizer.py`: LOS mode heatmap visualization (60-minute sliding window)
- `src/config.py`: Configuration settings
- `sandbox/mock_controller.py`: Mock controller for testing without hardware

