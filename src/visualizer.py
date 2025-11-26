"""
Handles loading and displaying analysis result files.
Supports images, text files, and data files.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from . import config


class Visualizer:
    """Manages visualization of analysis results."""
    
    def __init__(self):
        """Initialize visualizer."""
        self.current_run: Optional[Path] = None
        self.current_files: Dict[str, List[Path]] = {}
        self.load_error: Optional[str] = None
    
    def load_run(self, run_dir: Path) -> bool:
        """
        Load files from a run directory.
        
        Args:
            run_dir: Path to run directory
            
        Returns:
            True if successful, False otherwise
        """
        self.load_error = None
        
        if not run_dir.exists():
            self.load_error = f"Directory does not exist: {run_dir}"
            return False
        
        if not run_dir.is_dir():
            self.load_error = f"Path is not a directory: {run_dir}"
            return False
        
        # Scan for result files
        files = {}
        for pattern in config.RESULT_FILE_PATTERNS:
            file_type = pattern.split('_')[0]  # e.g., "analysis" from "analysis_*.png"
            matches = list(run_dir.glob(pattern))
            if matches:
                files[file_type] = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not files:
            self.load_error = f"No result files found in {run_dir}"
            return False
        
        self.current_run = run_dir
        self.current_files = files
        return True
    
    def get_image_files(self) -> List[Path]:
        """Get all image files from current run."""
        return self.current_files.get("analysis", [])
    
    def get_text_files(self) -> List[Path]:
        """Get all text/summary files from current run."""
        return self.current_files.get("summary", [])
    
    def get_data_files(self) -> List[Path]:
        """Get all data files from current run."""
        return self.current_files.get("data", [])
    
    def load_image(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Load an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image array or None if failed
        """
        try:
            if not image_path.exists():
                self.load_error = f"Image file not found: {image_path}"
                return None
            
            img = mpimg.imread(str(image_path))
            return img
        except Exception as e:
            self.load_error = f"Failed to load image: {str(e)}"
            return None
    
    def load_text_file(self, text_path: Path) -> Optional[str]:
        """
        Load a text file.
        
        Args:
            text_path: Path to text file
            
        Returns:
            File contents or None if failed
        """
        try:
            if not text_path.exists():
                self.load_error = f"Text file not found: {text_path}"
                return None
            
            with open(text_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.load_error = f"Failed to load text file: {str(e)}"
            return None
    
    def load_data_file(self, data_path: Path) -> Optional[np.ndarray]:
        """
        Load a CSV data file.
        
        Args:
            data_path: Path to data file
            
        Returns:
            Data array or None if failed
        """
        try:
            if not data_path.exists():
                self.load_error = f"Data file not found: {data_path}"
                return None
            
            data = np.loadtxt(data_path, delimiter=',', skiprows=1)
            return data
        except Exception as e:
            self.load_error = f"Failed to load data file: {str(e)}"
            return None
    
    def create_plot_from_data(self, data: np.ndarray, ax) -> bool:
        """
        Create a plot from data array.
        
        Args:
            data: 2D numpy array with data
            ax: Matplotlib axes to plot on
            
        Returns:
            True if successful
        """
        try:
            ax.clear()
            if data.ndim == 2 and data.shape[1] >= 2:
                ax.plot(data[:, 0], data[:, 1])
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.grid(True)
            else:
                ax.text(0.5, 0.5, 'Data format not supported', 
                       ha='center', va='center', transform=ax.transAxes)
            return True
        except Exception as e:
            self.load_error = f"Failed to create plot: {str(e)}"
            return False

