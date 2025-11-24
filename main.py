"""
Coherent Doppler Wind Lidar System Interface
Main application for controlling periscope and visualizing lidar data
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGroupBox, QComboBox, QPushButton, 
                             QLabel, QDoubleSpinBox, QSpinBox, QFormLayout)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from lidar_controller import LidarController
from plot_manager import PlotManager


class LidarInterface(QMainWindow):
    """Main window for the Coherent Doppler Wind Lidar System Interface"""
    
    def __init__(self):
        super().__init__()
        self.controller = LidarController()
        self.plot_manager = PlotManager()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Coherent Doppler Wind Lidar System")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left column - Control Panel (1/3 width)
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)  # Stretch factor 1
        
        # Right column - Visualization Panel (2/3 width)
        visualization_panel = self.create_visualization_panel()
        main_layout.addWidget(visualization_panel, 2)  # Stretch factor 2
        
    def create_control_panel(self):
        """Create the left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # System Status Group
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e9; border-radius: 3px;")
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Scanning Profile Selection
        profile_group = QGroupBox("Scanning Profile")
        profile_layout = QVBoxLayout()
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["VAD", "LOS", "PPI"])
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(QLabel("Select Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # Periscope Control Group
        periscope_group = QGroupBox("Periscope Control")
        periscope_layout = QFormLayout()
        
        self.azimuth_spin = QDoubleSpinBox()
        self.azimuth_spin.setRange(-180.0, 180.0)
        self.azimuth_spin.setSuffix("°")
        self.azimuth_spin.setDecimals(1)
        self.azimuth_spin.setValue(0.0)
        periscope_layout.addRow("Azimuth:", self.azimuth_spin)
        
        self.elevation_spin = QDoubleSpinBox()
        self.elevation_spin.setRange(-90.0, 90.0)
        self.elevation_spin.setSuffix("°")
        self.elevation_spin.setDecimals(1)
        self.elevation_spin.setValue(0.0)
        periscope_layout.addRow("Elevation:", self.elevation_spin)
        
        self.move_button = QPushButton("Move Periscope")
        self.move_button.clicked.connect(self.move_periscope)
        self.move_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        periscope_layout.addRow(self.move_button)
        
        periscope_group.setLayout(periscope_layout)
        layout.addWidget(periscope_group)
        
        # Profile-Specific Parameters
        self.params_group = QGroupBox("Profile Parameters")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)
        
        # Initialize parameters for default profile
        self.update_profile_parameters("VAD")
        
        # Control Buttons
        buttons_group = QGroupBox("System Control")
        buttons_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Start Acquisition")
        self.start_button.clicked.connect(self.start_acquisition)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Acquisition")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        buttons_layout.addWidget(self.stop_button)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def create_visualization_panel(self):
        """Create the right visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Initialize with default plot
        self.update_plot("VAD")
        
        return panel
    
    def update_profile_parameters(self, profile):
        """Update parameter controls based on selected profile"""
        # Clear existing parameters
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if profile == "VAD":
            self.vad_elevation = QDoubleSpinBox()
            self.vad_elevation.setRange(0.0, 90.0)
            self.vad_elevation.setSuffix("°")
            self.vad_elevation.setDecimals(1)
            self.vad_elevation.setValue(15.0)
            self.params_layout.addRow("Elevation Angle:", self.vad_elevation)
            
            self.vad_azimuth_start = QDoubleSpinBox()
            self.vad_azimuth_start.setRange(0.0, 360.0)
            self.vad_azimuth_start.setSuffix("°")
            self.vad_azimuth_start.setDecimals(1)
            self.vad_azimuth_start.setValue(0.0)
            self.params_layout.addRow("Azimuth Start:", self.vad_azimuth_start)
            
            self.vad_azimuth_end = QDoubleSpinBox()
            self.vad_azimuth_end.setRange(0.0, 360.0)
            self.vad_azimuth_end.setSuffix("°")
            self.vad_azimuth_end.setDecimals(1)
            self.vad_azimuth_end.setValue(360.0)
            self.params_layout.addRow("Azimuth End:", self.vad_azimuth_end)
            
        elif profile == "LOS":
            self.los_azimuth = QDoubleSpinBox()
            self.los_azimuth.setRange(0.0, 360.0)
            self.los_azimuth.setSuffix("°")
            self.los_azimuth.setDecimals(1)
            self.los_azimuth.setValue(0.0)
            self.params_layout.addRow("Azimuth:", self.los_azimuth)
            
            self.los_elevation = QDoubleSpinBox()
            self.los_elevation.setRange(0.0, 90.0)
            self.los_elevation.setSuffix("°")
            self.los_elevation.setDecimals(1)
            self.los_elevation.setValue(30.0)
            self.params_layout.addRow("Elevation:", self.los_elevation)
            
            self.los_range_max = QDoubleSpinBox()
            self.los_range_max.setRange(0.1, 20.0)
            self.los_range_max.setSuffix(" km")
            self.los_range_max.setDecimals(1)
            self.los_range_max.setValue(10.0)
            self.params_layout.addRow("Max Range:", self.los_range_max)
            
        elif profile == "PPI":
            self.ppi_elevation = QDoubleSpinBox()
            self.ppi_elevation.setRange(0.0, 90.0)
            self.ppi_elevation.setSuffix("°")
            self.ppi_elevation.setDecimals(1)
            self.ppi_elevation.setValue(1.0)
            self.params_layout.addRow("Elevation Angle:", self.ppi_elevation)
            
            self.ppi_azimuth_start = QDoubleSpinBox()
            self.ppi_azimuth_start.setRange(0.0, 360.0)
            self.ppi_azimuth_start.setSuffix("°")
            self.ppi_azimuth_start.setDecimals(1)
            self.ppi_azimuth_start.setValue(0.0)
            self.params_layout.addRow("Azimuth Start:", self.ppi_azimuth_start)
            
            self.ppi_azimuth_end = QDoubleSpinBox()
            self.ppi_azimuth_end.setRange(0.0, 360.0)
            self.ppi_azimuth_end.setSuffix("°")
            self.ppi_azimuth_end.setDecimals(1)
            self.ppi_azimuth_end.setValue(360.0)
            self.params_layout.addRow("Azimuth End:", self.ppi_azimuth_end)
            
            self.ppi_range_max = QDoubleSpinBox()
            self.ppi_range_max.setRange(0.1, 20.0)
            self.ppi_range_max.setSuffix(" km")
            self.ppi_range_max.setDecimals(1)
            self.ppi_range_max.setValue(10.0)
            self.params_layout.addRow("Max Range:", self.ppi_range_max)
    
    def on_profile_changed(self, profile):
        """Handle scanning profile change"""
        self.update_profile_parameters(profile)
        self.update_plot(profile)
    
    def update_plot(self, profile):
        """Update the plot based on selected profile"""
        self.figure.clear()
        
        if profile == "PPI":
            # For PPI, create polar subplot directly
            ax = self.figure.add_subplot(111, projection='polar')
            self.plot_manager.plot_ppi(ax)
        else:
            # For VAD and LOS, use regular Cartesian subplot
            ax = self.figure.add_subplot(111)
            if profile == "VAD":
                self.plot_manager.plot_vad(ax)
            elif profile == "LOS":
                self.plot_manager.plot_los(ax)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def move_periscope(self):
        """Move periscope to specified azimuth and elevation"""
        azimuth = self.azimuth_spin.value()
        elevation = self.elevation_spin.value()
        
        success = self.controller.move_periscope(azimuth, elevation)
        if success:
            self.status_label.setText(f"Status: Periscope moved to Az={azimuth}°, El={elevation}°")
            self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e9; border-radius: 3px;")
        else:
            self.status_label.setText("Status: Error moving periscope")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffebee; border-radius: 3px;")
    
    def start_acquisition(self):
        """Start data acquisition"""
        profile = self.profile_combo.currentText()
        self.controller.start_acquisition(profile)
        self.status_label.setText(f"Status: Acquisition started ({profile} mode)")
        self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0; border-radius: 3px;")
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.controller.stop_acquisition()
        self.status_label.setText("Status: Acquisition stopped")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e9; border-radius: 3px;")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = LidarInterface()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

