"""
Configuration settings for the periscope control interface.
Modify these paths and settings according to your system setup.
"""

import os
from pathlib import Path

# Base directory for periscope software suite
PERISCOPE_SOFTWARE_DIR = Path(__file__).parent / "periscope_software"

# Path to the periscope terminal application executable
# Options: "Periscope Control System.exe" or "Wind Positioner.exe" in dist/ folder
PERISCOPE_APP_PATH = PERISCOPE_SOFTWARE_DIR / "dist" / "Periscope Control System.exe"

# Directory where external analysis results are written
RESULTS_DIR = Path(__file__).parent.parent / "data" / "results"  # Update with actual path

# Expected subdirectory naming pattern (e.g., "run_20240101_120000")
RESULTS_SUBDIR_PATTERN = "run_*"

# Expected result file patterns within subdirectories
RESULT_FILE_PATTERNS = [
    "analysis_*.png",  # Plot images
    "summary_*.txt",   # Summary text files
    "data_*.csv",      # Data files
]

# Refresh interval for checking new files (seconds)
FILE_CHECK_INTERVAL = 2.0

# Maximum console log lines
MAX_CONSOLE_LINES = 100

# Default jog step sizes (degrees)
DEFAULT_AZIMUTH_JOG_STEP = 1.0
DEFAULT_ELEVATION_JOG_STEP = 1.0

# System azimuth offset from true north (degrees)
# This offset is applied to all azimuth commands to convert from true north to system coordinates
AZIMUTH_OFFSET = 0.0  # Default: no offset. Update this based on your system's physical orientation.

# Sandbox mode - set to True to use mock controller instead of real hardware
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "False").lower() == "true"

# Sandbox directory for test data
SANDBOX_DIR = Path(__file__).parent.parent / "sandbox"
SANDBOX_RESULTS_DIR = SANDBOX_DIR / "results"

# LOS Mode Configuration
LOS_PEAK_FILE_PATTERN = "*_Peak.txt"  # Pattern for peak log files
LOS_HEATMAP_TIME_WINDOW_MINUTES = 60  # 60-minute sliding window
LOS_HEATMAP_RANGE_MAX_KM = 12.0  # Maximum range in km
LOS_HEATMAP_RANGE_MIN_KM = 0.0  # Minimum range in km
LOS_DATA_UPDATE_INTERVAL = 1.0  # Seconds between data checks

