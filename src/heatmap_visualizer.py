"""
Heatmap visualization for LOS mode.
Displays time-series range profiles as a continuously updating heatmap.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import re
from . import config


class HeatmapVisualizer:
    """Manages heatmap visualization for LOS mode."""
    
    def __init__(self):
        """Initialize heatmap visualizer."""
        self.start_timestamp: Optional[datetime] = None
        self.data_buffer: List[Tuple[datetime, np.ndarray]] = []  # (timestamp, range_profile)
        self.time_window_minutes = config.LOS_HEATMAP_TIME_WINDOW_MINUTES
        self.range_max_km = config.LOS_HEATMAP_RANGE_MAX_KM
        self.range_min_km = config.LOS_HEATMAP_RANGE_MIN_KM
        self.range_bins = 100  # Number of range bins
        
        # Create range axis (fixed from 0 to 12 km)
        self.range_axis = np.linspace(self.range_min_km, self.range_max_km, self.range_bins)
    
    def set_start_timestamp(self, timestamp: datetime):
        """Set the start timestamp from the _Peak.txt file."""
        self.start_timestamp = timestamp
        self.data_buffer = []
    
    def add_profile(self, timestamp: datetime, profile_data: np.ndarray):
        """
        Add a new range profile to the buffer.
        
        Args:
            timestamp: Timestamp of the profile
            profile_data: 1D array of values for each range bin
        """
        if len(profile_data) != self.range_bins:
            # Interpolate to match range bins if needed
            if HAS_SCIPY:
                old_range = np.linspace(self.range_min_km, self.range_max_km, len(profile_data))
                f = interp1d(old_range, profile_data, kind='linear', fill_value=0, bounds_error=False)
                profile_data = f(self.range_axis)
            else:
                # Simple linear interpolation using numpy
                old_indices = np.linspace(0, len(profile_data) - 1, self.range_bins)
                profile_data = np.interp(old_indices, np.arange(len(profile_data)), profile_data)
        
        self.data_buffer.append((timestamp, profile_data))
        
        # Remove data older than time window
        cutoff_time = timestamp - timedelta(minutes=self.time_window_minutes)
        self.data_buffer = [(t, d) for t, d in self.data_buffer if t >= cutoff_time]
    
    def get_heatmap_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get heatmap data for visualization.
        
        Returns:
            Tuple of (time_axis, range_axis, heatmap_matrix)
            time_axis: Array of timestamps
            range_axis: Array of range values (km)
            heatmap_matrix: 2D array (time x range) of values
        """
        if not self.data_buffer:
            # Return empty arrays
            time_axis = np.array([])
            heatmap_matrix = np.zeros((0, self.range_bins))
            return time_axis, self.range_axis, heatmap_matrix
        
        # Sort by timestamp
        sorted_buffer = sorted(self.data_buffer, key=lambda x: x[0])
        
        # Extract timestamps and profiles
        timestamps = [t for t, _ in sorted_buffer]
        profiles = np.array([d for _, d in sorted_buffer])
        
        # Create time axis
        time_axis = np.array(timestamps)
        
        return time_axis, self.range_axis, profiles.T  # Transpose for (range x time)
    
    def create_heatmap_plot(self, ax, time_axis: np.ndarray, range_axis: np.ndarray, 
                           heatmap_data: np.ndarray):
        """
        Create heatmap plot on given axes.
        
        Args:
            ax: Matplotlib axes
            time_axis: Array of timestamps
            range_axis: Array of range values
            heatmap_data: 2D array (range x time) of values
        """
        ax.clear()
        
        if len(time_axis) == 0:
            ax.text(0.5, 0.5, 'Waiting for data...', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_xlabel('Time')
            ax.set_ylabel('Range (km)')
            return
        
        # Convert timestamps to numeric values for plotting
        time_numeric = [(t - time_axis[0]).total_seconds() / 60.0 for t in time_axis]
        
        # Create meshgrid
        T, R = np.meshgrid(time_numeric, range_axis)
        
        # Create heatmap
        im = ax.pcolormesh(T, R, heatmap_data, shading='auto', cmap='viridis')
        
        # Format time axis labels
        ax.set_xlabel('Time (minutes from start)')
        ax.set_ylabel('Range (km)')
        ax.set_title('LOS Mode: Range Profile Heatmap')
        
        # Add colorbar
        plt.colorbar(im, ax=ax, label='Intensity')
        
        # Set limits
        ax.set_xlim(0, self.time_window_minutes)
        ax.set_ylim(self.range_min_km, self.range_max_km)
        
        # Add UTC time labels on top axis
        ax2 = ax.twiny()
        if len(time_axis) > 0:
            # Show first and last timestamps
            first_time = time_axis[0]
            last_time = time_axis[-1]
            ax2.set_xlim(ax.get_xlim())
            ax2.set_xticks([0, self.time_window_minutes])
            ax2.set_xticklabels([
                first_time.strftime('%H:%M:%S UTC'),
                last_time.strftime('%H:%M:%S UTC')
            ])
            ax2.set_xlabel('UTC Time', labelpad=10)
    
    def find_latest_peak_file(self, search_dir: Path) -> Optional[Path]:
        """
        Find the most recent _Peak.txt file in subdirectories.
        
        Args:
            search_dir: Directory to search in
            
        Returns:
            Path to the most recent _Peak.txt file, or None if not found
        """
        if not search_dir.exists():
            return None
        
        peak_files = []
        for subdir in search_dir.iterdir():
            if subdir.is_dir():
                # Search for _Peak.txt files in subdirectory
                for peak_file in subdir.glob(config.LOS_PEAK_FILE_PATTERN):
                    peak_files.append(peak_file)
        
        if not peak_files:
            return None
        
        # Return the most recently modified file
        return max(peak_files, key=lambda p: p.stat().st_mtime)
    
    def read_last_timestamp(self, peak_file: Path) -> Optional[datetime]:
        """
        Read the last timestamped entry from a _Peak.txt file.
        
        Args:
            peak_file: Path to the _Peak.txt file
            
        Returns:
            Datetime of the last entry, or None if not found
        """
        if not peak_file.exists():
            return None
        
        try:
            with open(peak_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Read from the end to find the last entry
            for line in reversed(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to extract timestamp (format will be defined later)
                # For now, assume format like: "YYYY-MM-DD HH:MM:SS,data..."
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    try:
                        timestamp_str = timestamp_match.group(1)
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        return timestamp
                    except ValueError:
                        continue
            
            return None
        except Exception as e:
            print(f"Error reading peak file: {e}")
            return None
    
    def scan_for_new_data(self, search_dir: Path) -> List[Tuple[datetime, np.ndarray]]:
        """
        Scan for new data entries in peak files.
        This is a placeholder - actual implementation depends on file format.
        
        Args:
            search_dir: Directory to search in
            
        Returns:
            List of (timestamp, profile_data) tuples
        """
        # This will be implemented based on actual file format
        # For now, return empty list
        return []

