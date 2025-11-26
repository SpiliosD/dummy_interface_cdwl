"""
Monitors the results directory for new analysis files.
Detects new files and maintains a list of available runs.
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import config


class ResultsFileHandler(FileSystemEventHandler):
    """Handles file system events for results directory."""
    
    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize handler.
        
        Args:
            callback: Function called when new files are detected
        """
        self.callback = callback
    
    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory:
            self.callback(event.src_path)
    
    def on_modified(self, event):
        """Called when a file is modified."""
        if not event.is_directory:
            self.callback(event.src_path)


class FileMonitor:
    """Monitors results directory for new analysis files."""
    
    def __init__(self, new_file_callback: Optional[Callable[[str], None]] = None, 
                 results_dir: Optional[Path] = None):
        """
        Initialize file monitor.
        
        Args:
            new_file_callback: Called when new files are detected
            results_dir: Optional custom results directory (defaults to config.RESULTS_DIR)
        """
        if results_dir is None:
            # Use sandbox directory if in sandbox mode
            if config.SANDBOX_MODE:
                self.results_dir = config.SANDBOX_RESULTS_DIR
            else:
                self.results_dir = Path(config.RESULTS_DIR)
        else:
            self.results_dir = results_dir
        self.new_file_callback = new_file_callback
        self.observer: Optional[Observer] = None
        self.available_runs: List[Path] = []
        self.latest_run: Optional[Path] = None
        self._scan_existing_runs()
    
    def _scan_existing_runs(self):
        """Scan for existing run directories."""
        if not self.results_dir.exists():
            return
        
        runs = []
        for item in self.results_dir.iterdir():
            if item.is_dir() and self._matches_run_pattern(item.name):
                runs.append(item)
        
        # Sort by modification time (newest first)
        runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        self.available_runs = runs
        if runs:
            self.latest_run = runs[0]
    
    def _matches_run_pattern(self, name: str) -> bool:
        """Check if directory name matches expected pattern."""
        import fnmatch
        return fnmatch.fnmatch(name, config.RESULTS_SUBDIR_PATTERN)
    
    def start_monitoring(self):
        """Start monitoring for new files."""
        if not self.results_dir.exists():
            return
        
        handler = ResultsFileHandler(self._on_file_event)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.results_dir), recursive=True)
        self.observer.start()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def _on_file_event(self, file_path: str):
        """Handle file system event."""
        path = Path(file_path)
        # Check if file is in a run subdirectory
        if path.parent != self.results_dir:
            # Rescan to update available runs
            self._scan_existing_runs()
            if self.new_file_callback:
                self.new_file_callback(file_path)
    
    def get_latest_run(self) -> Optional[Path]:
        """Get the most recent run directory."""
        self._scan_existing_runs()
        return self.latest_run
    
    def get_all_runs(self) -> List[Path]:
        """Get all available run directories, sorted newest first."""
        self._scan_existing_runs()
        return self.available_runs
    
    def get_result_files(self, run_dir: Path) -> dict[str, List[Path]]:
        """
        Get result files in a run directory, organized by type.
        
        Args:
            run_dir: Path to run directory
            
        Returns:
            Dictionary mapping file types to lists of file paths
        """
        if not run_dir.exists() or not run_dir.is_dir():
            return {}
        
        files_by_type = {}
        for pattern in config.RESULT_FILE_PATTERNS:
            file_type = pattern.split('_')[0]  # e.g., "analysis" from "analysis_*.png"
            matches = list(run_dir.glob(pattern))
            if matches:
                files_by_type[file_type] = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)
        
        return files_by_type

