"""
Plot Manager Module
Handles visualization of lidar data for different scanning profiles
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from typing import Optional


class PlotManager:
    """Manages plotting for different lidar scanning profiles"""
    
    def __init__(self):
        self.data_cache = {}
    
    def plot_vad(self, ax, data: Optional[np.ndarray] = None):
        """
        Plot Velocity Azimuth Display (VAD) data
        
        VAD displays wind speed and direction as a function of azimuth angle
        at a fixed elevation angle.
        
        Args:
            ax: Matplotlib axes object
            data: Optional data array (if None, generates sample data)
        """
        ax.clear()
        
        if data is None:
            # Generate sample VAD data
            azimuth = np.linspace(0, 360, 72)  # 5-degree resolution
            wind_speed = 5 + 2 * np.sin(np.radians(azimuth - 45)) + np.random.normal(0, 0.5, len(azimuth))
            wind_direction = 180 + 30 * np.cos(np.radians(azimuth)) + np.random.normal(0, 5, len(azimuth))
        else:
            azimuth, wind_speed, wind_direction = data
        
        # Plot wind speed vs azimuth
        ax.plot(azimuth, wind_speed, 'b-', linewidth=2, label='Wind Speed')
        ax.set_xlabel('Azimuth Angle (degrees)', fontsize=12)
        ax.set_ylabel('Wind Speed (m/s)', fontsize=12)
        ax.set_title('Velocity Azimuth Display (VAD)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 45))
        
        # Add secondary y-axis for wind direction
        ax2 = ax.twinx()
        ax2.plot(azimuth, wind_direction, 'r--', linewidth=2, label='Wind Direction')
        ax2.set_ylabel('Wind Direction (degrees)', fontsize=12, color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.set_ylim(0, 360)
        ax2.set_yticks(np.arange(0, 361, 45))
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    def plot_los(self, ax, data: Optional[np.ndarray] = None):
        """
        Plot Line of Sight (LOS) data
        
        LOS displays radial velocity as a function of range along a single
        line of sight direction.
        
        Args:
            ax: Matplotlib axes object
            data: Optional data array (if None, generates sample data)
        """
        ax.clear()
        
        if data is None:
            # Generate sample LOS data
            range_km = np.linspace(0.1, 10, 200)
            radial_velocity = 3 * np.exp(-range_km / 5) * np.sin(range_km * 2) + np.random.normal(0, 0.3, len(range_km))
            signal_strength = 100 * np.exp(-range_km / 3) + np.random.normal(0, 5, len(range_km))
        else:
            range_km, radial_velocity, signal_strength = data
        
        # Plot radial velocity
        ax.plot(range_km, radial_velocity, 'b-', linewidth=2, label='Radial Velocity')
        ax.set_xlabel('Range (km)', fontsize=12)
        ax.set_ylabel('Radial Velocity (m/s)', fontsize=12, color='b')
        ax.set_title('Line of Sight (LOS) Profile', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='y', labelcolor='b')
        
        # Add secondary y-axis for signal strength
        ax2 = ax.twinx()
        ax2.plot(range_km, signal_strength, 'g--', linewidth=2, label='Signal Strength')
        ax2.set_ylabel('Signal Strength (dB)', fontsize=12, color='g')
        ax2.tick_params(axis='y', labelcolor='g')
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    def plot_ppi(self, ax, data: Optional[np.ndarray] = None):
        """
        Plot Plan Position Indicator (PPI) data
        
        PPI displays a 2D horizontal cross-section of wind velocity at a
        fixed elevation angle, typically shown as a polar plot.
        
        Args:
            ax: Matplotlib axes object (should be polar projection)
            data: Optional data array (if None, generates sample data)
        """
        ax.clear()
        
        if data is None:
            # Generate sample PPI data
            azimuth = np.linspace(0, 360, 72)
            range_km = np.linspace(0.1, 10, 50)
            Az, Rg = np.meshgrid(azimuth, range_km)
            
            # Create sample wind field pattern
            radial_velocity = 5 * np.exp(-Rg / 5) * np.sin(np.radians(Az - 45)) + np.random.normal(0, 0.5, Az.shape)
        else:
            Az, Rg, radial_velocity = data
        
        # Plot as filled contour
        contour = ax.contourf(np.radians(Az), Rg, radial_velocity, levels=20, cmap='RdYlBu_r')
        ax.contour(np.radians(Az), Rg, radial_velocity, levels=20, colors='black', alpha=0.3, linewidths=0.5)
        
        # Add colorbar
        fig = ax.figure
        cbar = fig.colorbar(contour, ax=ax, pad=0.1)
        cbar.set_label('Radial Velocity (m/s)', fontsize=12)
        
        ax.set_title('Plan Position Indicator (PPI)', fontsize=14, fontweight='bold', pad=20)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_rlabel_position(45)
        
        # Add range circles
        max_range = np.max(Rg)
        for r in np.arange(2, max_range + 1, 2):
            circle = Circle((0, 0), r, fill=False, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
            ax.add_patch(circle)

