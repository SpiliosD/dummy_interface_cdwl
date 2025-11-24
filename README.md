# Coherent Doppler Wind Lidar System Interface

A lean, user-friendly interface for operating a coherent Doppler wind lidar system and visualizing processed data. This interface controls the periscope component and displays analysis results for different scanning profiles.

## Features

- **Periscope Control**: Direct control of azimuth and elevation angles
- **Multiple Scanning Profiles**: Support for VAD, LOS, and PPI scanning modes
- **Real-time Visualization**: Dynamic plotting of lidar data based on selected profile
- **Modern UI**: Clean, intuitive two-column layout with responsive controls

## System Components

The lidar system consists of three main components:
- **Laser**: Controlled by external software
- **Data Recorder**: Controlled by external software  
- **Periscope**: Controlled by this interface

## Interface Layout

The interface is split into two vertical columns:

- **Left Column (1/3 width)**: System control elements
  - System status display
  - Scanning profile selection
  - Periscope control (azimuth/elevation)
  - Profile-specific parameters
  - System control buttons

- **Right Column (2/3 width)**: Graphical visualization
  - Dynamic plots based on selected scanning profile
  - VAD: Velocity Azimuth Display
  - LOS: Line of Sight profile
  - PPI: Plan Position Indicator

## Scanning Profiles

### VAD (Velocity Azimuth Display)
Displays wind speed and direction as a function of azimuth angle at a fixed elevation angle.

### LOS (Line of Sight)
Shows radial velocity and signal strength as a function of range along a single line of sight direction.

### PPI (Plan Position Indicator)
Displays a 2D horizontal cross-section of wind velocity at a fixed elevation angle as a polar plot.

## Installation

1. Install Python 3.8 or higher

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Operating the Interface

1. **Select Scanning Profile**: Choose VAD, LOS, or PPI from the dropdown menu
2. **Configure Parameters**: Adjust profile-specific parameters in the left panel
3. **Control Periscope**: Set azimuth and elevation angles, then click "Move Periscope"
4. **Start Acquisition**: Click "Start Acquisition" to begin data collection
5. **View Results**: The right panel automatically updates to show the appropriate visualization

## Project Structure

```
.
├── main.py              # Main application window and UI
├── lidar_controller.py  # Periscope control and data acquisition
├── plot_manager.py      # Visualization functions for each profile
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Development Notes

- The periscope control interface currently uses simulated movement. Replace the `move_periscope()` method in `lidar_controller.py` with actual hardware communication.
- Data acquisition coordination with external laser and data recorder software needs to be implemented in the `start_acquisition()` and `stop_acquisition()` methods.
- Sample data generators are included for demonstration. Replace with actual data processing pipelines as needed.

## Requirements

- Python 3.8+
- PyQt6
- matplotlib
- numpy

## License

This project is provided as-is for lidar system control and visualization.

