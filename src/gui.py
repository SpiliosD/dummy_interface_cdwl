"""
Main GUI application for periscope control and visualization.
Implements a two-column layout with control panel and visualization area.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
import threading
import time
from typing import Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from . import config

from .periscope_controller import PeriscopeController
from .file_monitor import FileMonitor
from .visualizer import Visualizer
from .heatmap_visualizer import HeatmapVisualizer


class PeriscopeGUI:
    """Main GUI application."""
    
    def __init__(self, root: tk.Tk, sandbox_mode: bool = False):
        """
        Initialize GUI.
        
        Args:
            root: Tkinter root window
            sandbox_mode: If True, use mock controller instead of real hardware
        """
        self.root = root
        title = "Periscope Control Interface"
        if sandbox_mode:
            title += " [SANDBOX MODE]"
        self.root.title(title)
        self.root.geometry("1200x800")
        
        # Initialize components
        if sandbox_mode:
            # Import mock controller for sandbox mode
            import sys
            from pathlib import Path
            sandbox_path = Path(__file__).parent.parent / "sandbox"
            if str(sandbox_path) not in sys.path:
                sys.path.insert(0, str(sandbox_path.parent))
            from sandbox.mock_controller import MockPeriscopeController
            self.controller = MockPeriscopeController(output_callback=self._append_console)
            # Set initial azimuth offset from config
            self.controller.set_azimuth_offset(config.AZIMUTH_OFFSET)
            # Use sandbox results directory
            results_dir = config.SANDBOX_RESULTS_DIR
        else:
            self.controller = PeriscopeController(output_callback=self._append_console)
            # Set initial azimuth offset from config
            self.controller.set_azimuth_offset(config.AZIMUTH_OFFSET)
            results_dir = config.RESULTS_DIR
        
        # Initialize file monitor with appropriate results directory
        if sandbox_mode:
            if not results_dir.exists():
                results_dir.mkdir(parents=True, exist_ok=True)
            self.monitor = FileMonitor(new_file_callback=self._on_new_file_detected, 
                                      results_dir=results_dir)
        else:
            self.monitor = FileMonitor(new_file_callback=self._on_new_file_detected)
        
        self.visualizer = Visualizer()
        self.heatmap_visualizer = HeatmapVisualizer()
        
        # State variables
        self.auto_refresh = False
        self.los_mode_active = False
        self.refresh_thread: Optional[threading.Thread] = None
        self.los_update_thread: Optional[threading.Thread] = None
        
        # Create UI
        self._create_widgets()
        
        # Start file monitoring
        self.monitor.start_monitoring()
        
        # Start refresh thread
        self._start_refresh_thread()
        
        # Update status periodically
        self._update_status()
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container with two columns
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Left column: Control Panel (narrower)
        left_frame = ttk.Frame(main_frame, padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        main_frame.columnconfigure(0, weight=1, minsize=400)
        main_frame.rowconfigure(0, weight=1)
        
        # Right column: Visualization (wider)
        right_frame = ttk.Frame(main_frame, padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=2, minsize=600)
        
        # Build left panel
        self._create_control_panel(left_frame)
        
        # Build right panel
        self._create_visualization_panel(right_frame)
    
    def _create_control_panel(self, parent: ttk.Frame):
        """Create left control panel."""
        # Title
        title_label = ttk.Label(parent, text="Periscope Control", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Status indicators frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection status
        self.connection_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.connection_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Motion status
        self.motion_label = ttk.Label(status_frame, text="Idle", foreground="gray")
        self.motion_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Error indicator
        self.error_label = ttk.Label(status_frame, text="", foreground="red", wraplength=350)
        self.error_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Connection controls
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="5")
        conn_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(conn_frame, text="Connect", command=self._on_connect).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(conn_frame, text="Disconnect", command=self._on_disconnect).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(conn_frame, text="Initialize", command=self._on_initialize).grid(row=0, column=2, padx=2, pady=2)
        
        # System Settings
        settings_frame = ttk.LabelFrame(parent, text="System Settings", padding="5")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Azimuth Offset (°):").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.azimuth_offset_entry = ttk.Entry(settings_frame, width=10)
        self.azimuth_offset_entry.insert(0, str(config.AZIMUTH_OFFSET))
        self.azimuth_offset_entry.grid(row=0, column=1, padx=2, pady=2)
        ttk.Label(settings_frame, text="(offset from true north)", font=("Arial", 8)).grid(row=0, column=2, padx=2, sticky=tk.W)
        ttk.Button(settings_frame, text="Set", command=self._on_set_azimuth_offset).grid(row=0, column=3, padx=2, pady=2)
        
        # Homing
        home_frame = ttk.LabelFrame(parent, text="Homing", padding="5")
        home_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(home_frame, text="Home", command=self._on_home).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(home_frame, text="Zero", command=self._on_zero).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(home_frame, text="Stop", command=self._on_stop).grid(row=0, column=2, padx=2, pady=2)
        ttk.Button(home_frame, text="Brake", command=self._on_brake).grid(row=0, column=3, padx=2, pady=2)
        
        # Azimuth controls
        az_frame = ttk.LabelFrame(parent, text="Azimuth (relative to true north)", padding="5")
        az_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(az_frame, text="◄ Jog -", command=lambda: self._on_jog_azimuth(-config.DEFAULT_AZIMUTH_JOG_STEP)).grid(row=0, column=0, padx=2)
        ttk.Button(az_frame, text="Jog + ►", command=lambda: self._on_jog_azimuth(config.DEFAULT_AZIMUTH_JOG_STEP)).grid(row=0, column=1, padx=2)
        
        ttk.Label(az_frame, text="Set angle:").grid(row=1, column=0, padx=2, pady=5)
        self.azimuth_entry = ttk.Entry(az_frame, width=10)
        self.azimuth_entry.grid(row=1, column=1, padx=2)
        ttk.Button(az_frame, text="Set", command=self._on_set_azimuth).grid(row=1, column=2, padx=2)
        
        # Elevation controls
        el_frame = ttk.LabelFrame(parent, text="Elevation", padding="5")
        el_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(el_frame, text="▼ Jog -", command=lambda: self._on_jog_elevation(-config.DEFAULT_ELEVATION_JOG_STEP)).grid(row=0, column=0, padx=2)
        ttk.Button(el_frame, text="Jog + ▲", command=lambda: self._on_jog_elevation(config.DEFAULT_ELEVATION_JOG_STEP)).grid(row=0, column=1, padx=2)
        
        ttk.Label(el_frame, text="Set angle:").grid(row=1, column=0, padx=2, pady=5)
        self.elevation_entry = ttk.Entry(el_frame, width=10)
        self.elevation_entry.grid(row=1, column=1, padx=2)
        ttk.Button(el_frame, text="Set", command=self._on_set_elevation).grid(row=1, column=2, padx=2)
        
        # LOS Mode controls
        los_frame = ttk.LabelFrame(parent, text="Line-of-Sight (LOS) Mode", padding="5")
        los_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(los_frame, text="Elevation (°):").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.los_elevation_entry = ttk.Entry(los_frame, width=10)
        self.los_elevation_entry.grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(los_frame, text="Azimuth (°):").grid(row=0, column=2, padx=2, pady=2, sticky=tk.W)
        self.los_azimuth_entry = ttk.Entry(los_frame, width=10)
        self.los_azimuth_entry.grid(row=0, column=3, padx=2, pady=2)
        ttk.Label(los_frame, text="(relative to true north)", font=("Arial", 8)).grid(row=0, column=4, padx=2, sticky=tk.W)
        
        ttk.Button(los_frame, text="Start LOS Mode", command=self._on_start_los_mode,
                  style="Accent.TButton").grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # LOS status indicator
        self.los_status_label = ttk.Label(los_frame, text="LOS Mode: Inactive", foreground="gray")
        self.los_status_label.grid(row=2, column=0, columnspan=4, padx=2, pady=2, sticky=tk.W)
        
        # Console log
        console_frame = ttk.LabelFrame(parent, text="Console", padding="5")
        console_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(8, weight=1)
        
        self.console = scrolledtext.ScrolledText(console_frame, height=8, width=45, state=tk.DISABLED)
        self.console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        # Advanced: Raw command
        adv_frame = ttk.LabelFrame(parent, text="Advanced", padding="5")
        adv_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(adv_frame, text="Raw command:").grid(row=0, column=0, padx=2, pady=2)
        self.raw_command_entry = ttk.Entry(adv_frame, width=25)
        self.raw_command_entry.grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(adv_frame, text="Send", command=self._on_send_raw_command).grid(row=0, column=2, padx=2, pady=2)
    
    def _create_visualization_panel(self, parent: ttk.Frame):
        """Create right visualization panel."""
        # Title
        title_label = ttk.Label(parent, text="Analysis Results", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status and controls frame
        viz_control_frame = ttk.Frame(parent)
        viz_control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status indicator
        self.viz_status_label = ttk.Label(viz_control_frame, text="No data loaded", foreground="gray")
        self.viz_status_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        
        # New data indicator
        self.new_data_label = ttk.Label(viz_control_frame, text="", foreground="green")
        self.new_data_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Control buttons
        ttk.Button(viz_control_frame, text="Load Latest", command=self._on_load_latest).grid(row=0, column=2, padx=2)
        ttk.Button(viz_control_frame, text="Browse...", command=self._on_browse_run).grid(row=0, column=3, padx=2)
        ttk.Button(viz_control_frame, text="Refresh", command=self._on_refresh_viz).grid(row=0, column=4, padx=2)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(viz_control_frame, text="Auto-refresh", variable=self.auto_refresh_var,
                       command=self._on_toggle_auto_refresh).grid(row=0, column=5, padx=5)
        
        # Run selection
        run_frame = ttk.Frame(parent)
        run_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(run_frame, text="Run:").grid(row=0, column=0, padx=5)
        self.run_combo = ttk.Combobox(run_frame, width=40, state="readonly")
        self.run_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.run_combo.bind("<<ComboboxSelected>>", self._on_run_selected)
        run_frame.columnconfigure(1, weight=1)
        
        # Visualization area
        viz_frame = ttk.LabelFrame(parent, text="Visualization", padding="5")
        viz_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)
        
        # Matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.text(0.5, 0.5, 'No data loaded', ha='center', va='center', transform=self.ax.transAxes)
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
        # Text summary area (for text files)
        summary_frame = ttk.LabelFrame(parent, text="Summary", padding="5")
        summary_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        parent.rowconfigure(4, weight=1)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=6, state=tk.DISABLED)
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        
        # Initial update
        self._update_run_list()
    
    # Control panel event handlers
    def _on_connect(self):
        """Handle connect button."""
        def connect_thread():
            success = self.controller.connect()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_disconnect(self):
        """Handle disconnect button."""
        def disconnect_thread():
            self.controller.disconnect()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=disconnect_thread, daemon=True).start()
    
    def _on_initialize(self):
        """Handle initialize button."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        def init_thread():
            success = self.controller.initialize()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def _on_home(self):
        """Handle home button."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        def home_thread():
            success = self.controller.home()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=home_thread, daemon=True).start()
    
    def _on_zero(self):
        """Handle zero button."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        def zero_thread():
            success = self.controller.zero()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=zero_thread, daemon=True).start()
    
    def _on_stop(self):
        """Handle stop button (emergency stop)."""
        def stop_thread():
            self.controller.stop()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def _on_brake(self):
        """Handle brake button (normal stop)."""
        def brake_thread():
            self.controller.brake()
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=brake_thread, daemon=True).start()
    
    def _on_jog_azimuth(self, step: float):
        """Handle azimuth jog."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        def jog_thread():
            self.controller.jog_azimuth(step)
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=jog_thread, daemon=True).start()
    
    def _on_jog_elevation(self, step: float):
        """Handle elevation jog."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        def jog_thread():
            self.controller.jog_elevation(step)
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=jog_thread, daemon=True).start()
    
    def _on_set_azimuth(self):
        """Handle set azimuth angle."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        try:
            angle = float(self.azimuth_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
            return
        
        def set_thread():
            self.controller.set_azimuth(angle)
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=set_thread, daemon=True).start()
    
    def _on_set_elevation(self):
        """Handle set elevation angle."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        try:
            angle = float(self.elevation_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
            return
        
        def set_thread():
            self.controller.set_elevation(angle)
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=set_thread, daemon=True).start()
    
    def _on_set_azimuth_offset(self):
        """Handle setting azimuth offset."""
        try:
            offset = float(self.azimuth_offset_entry.get())
            self.controller.set_azimuth_offset(offset)
            # Update config
            config.AZIMUTH_OFFSET = offset
            messagebox.showinfo("Azimuth Offset Set", 
                              f"Azimuth offset set to {offset}°.\nThis will be applied to all azimuth commands.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
    
    def _on_send_raw_command(self):
        """Handle raw command send."""
        command = self.raw_command_entry.get().strip()
        if not command:
            return
        
        def cmd_thread():
            returncode, output = self.controller.send_raw_command(command)
            self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=cmd_thread, daemon=True).start()
    
    def _on_start_los_mode(self):
        """Handle LOS mode initiation."""
        if not self.controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        
        try:
            elevation = float(self.los_elevation_entry.get())
            azimuth = float(self.los_azimuth_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for elevation and azimuth.")
            return
        
        def los_thread():
            # Move periscope to LOS position (offset is applied automatically)
            success = self.controller.los_mode(elevation, azimuth)
            
            if success:
                # Wait for movement to complete
                while self.controller.is_moving:
                    time.sleep(0.1)
                
                # Scan for _Peak.txt file and read timestamp
                self.root.after(0, lambda: self._initiate_los_visualization())
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "LOS Mode Failed", "Failed to move to LOS position."))
                self.root.after(0, lambda: self._update_status())
        
        threading.Thread(target=los_thread, daemon=True).start()
    
    def _initiate_los_visualization(self):
        """Initialize LOS mode visualization after movement completes."""
        from . import config
        
        # Find most recent _Peak.txt file
        search_dir = config.SANDBOX_RESULTS_DIR if config.SANDBOX_MODE else config.RESULTS_DIR
        peak_file = self.heatmap_visualizer.find_latest_peak_file(search_dir)
        
        if peak_file:
            timestamp = self.heatmap_visualizer.read_last_timestamp(peak_file)
            if timestamp:
                self.heatmap_visualizer.set_start_timestamp(timestamp)
                self.los_mode_active = True
                self.los_status_label.config(text=f"LOS Mode: Active (Started: {timestamp.strftime('%H:%M:%S')})", 
                                           foreground="green")
                self.viz_title_label.config(text="LOS Mode: Range Profile Heatmap", foreground="blue")
                self._start_los_update_thread()
                messagebox.showinfo("LOS Mode Active", 
                                  f"LOS mode activated. Monitoring data from {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                messagebox.showwarning("No Timestamp", "Could not read timestamp from peak file.")
        else:
            messagebox.showwarning("No Peak File", "Could not find _Peak.txt file. LOS mode visualization may not work.")
            # Still activate LOS mode but without timestamp
            self.los_mode_active = True
            self.los_status_label.config(text="LOS Mode: Active (No timestamp)", foreground="orange")
            self._start_los_update_thread()
    
    def _start_los_update_thread(self):
        """Start thread for continuous LOS data updates."""
        def los_update_loop():
            from . import config
            while self.los_mode_active:
                time.sleep(config.LOS_DATA_UPDATE_INTERVAL)
                
                # Scan for new data (placeholder - will be implemented based on file format)
                search_dir = config.SANDBOX_RESULTS_DIR if config.SANDBOX_MODE else config.RESULTS_DIR
                new_data = self.heatmap_visualizer.scan_for_new_data(search_dir)
                
                for timestamp, profile in new_data:
                    self.heatmap_visualizer.add_profile(timestamp, profile)
                
                # Update visualization
                if self.los_mode_active:
                    self.root.after(0, self._update_heatmap_display)
        
        if self.los_update_thread is None or not self.los_update_thread.is_alive():
            self.los_update_thread = threading.Thread(target=los_update_loop, daemon=True)
            self.los_update_thread.start()
    
    def _update_heatmap_display(self):
        """Update the heatmap display."""
        if not self.los_mode_active:
            return
        
        time_axis, range_axis, heatmap_data = self.heatmap_visualizer.get_heatmap_data()
        self.heatmap_visualizer.create_heatmap_plot(self.ax, time_axis, range_axis, heatmap_data)
        self.canvas.draw()
    
    # Visualization event handlers
    def _on_load_latest(self):
        """Load the latest run."""
        latest = self.monitor.get_latest_run()
        if latest:
            self._load_run(latest)
        else:
            messagebox.showinfo("No Data", "No runs found in results directory.")
    
    def _on_browse_run(self):
        """Browse for a run directory."""
        initial_dir = str(config.RESULTS_DIR) if config.RESULTS_DIR.exists() else "."
        dir_path = filedialog.askdirectory(initialdir=initial_dir, title="Select Run Directory")
        if dir_path:
            self._load_run(Path(dir_path))
    
    def _on_run_selected(self, event=None):
        """Handle run selection from combobox."""
        selection = self.run_combo.get()
        if selection:
            # Find the run path
            runs = self.monitor.get_all_runs()
            for run in runs:
                if run.name == selection:
                    self._load_run(run)
                    break
    
    def _on_refresh_viz(self):
        """Refresh visualization."""
        if self.visualizer.current_run:
            self._load_run(self.visualizer.current_run)
        else:
            self._on_load_latest()
    
    def _on_toggle_auto_refresh(self):
        """Toggle auto-refresh mode."""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self.new_data_label.config(text="Auto-refresh ON", foreground="green")
        else:
            self.new_data_label.config(text="")
    
    def _on_new_file_detected(self, file_path: str):
        """Handle new file detection."""
        if self.auto_refresh:
            self.root.after(0, lambda: self._on_load_latest())
        else:
            self.root.after(0, lambda: self.new_data_label.config(
                text="New data available", foreground="green"))
    
    # Helper methods
    def _load_run(self, run_dir: Path):
        """Load and display a run."""
        success = self.visualizer.load_run(run_dir)
        
        if not success:
            self.viz_status_label.config(text=f"Error: {self.visualizer.load_error}", foreground="red")
            messagebox.showerror("Load Error", self.visualizer.load_error)
            return
        
        # Update status
        self.viz_status_label.config(text=f"Loaded: {run_dir.name}", foreground="green")
        self.new_data_label.config(text="")
        
        # Update run combo
        self._update_run_list()
        self.run_combo.set(run_dir.name)
        
        # Display visualization
        self._display_visualization()
    
    def _display_visualization(self):
        """Display the loaded visualization."""
        # If LOS mode is active, show heatmap instead
        if self.los_mode_active:
            self._update_heatmap_display()
            return
        
        self.ax.clear()
        
        # Try to display images first
        images = self.visualizer.get_image_files()
        if images:
            img = self.visualizer.load_image(images[0])
            if img is not None:
                self.ax.imshow(img)
                self.ax.axis('off')
                self.canvas.draw()
                return
        
        # Try to display data files
        data_files = self.visualizer.get_data_files()
        if data_files:
            data = self.visualizer.load_data_file(data_files[0])
            if data is not None:
                self.visualizer.create_plot_from_data(data, self.ax)
                self.canvas.draw()
                return
        
        # Display text summary
        text_files = self.visualizer.get_text_files()
        if text_files:
            text = self.visualizer.load_text_file(text_files[0])
            if text:
                self.summary_text.config(state=tk.NORMAL)
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.insert(1.0, text)
                self.summary_text.config(state=tk.DISABLED)
        
        # No data to display
        self.ax.text(0.5, 0.5, 'No visualization data available', 
                    ha='center', va='center', transform=self.ax.transAxes)
        self.canvas.draw()
    
    def _update_run_list(self):
        """Update the run combobox list."""
        runs = self.monitor.get_all_runs()
        run_names = [run.name for run in runs]
        self.run_combo['values'] = run_names
    
    def _update_status(self):
        """Update status indicators."""
        # Connection status
        if self.controller.is_connected:
            self.connection_label.config(text="Connected", foreground="green")
        else:
            self.connection_label.config(text="Disconnected", foreground="red")
        
        # Motion status
        if self.controller.is_moving:
            self.motion_label.config(text="Moving...", foreground="orange")
        else:
            self.motion_label.config(text="Idle", foreground="gray")
        
        # Error status
        if self.controller.last_error:
            self.error_label.config(text=f"Error: {self.controller.last_error}")
        else:
            self.error_label.config(text="")
        
        # Schedule next update
        self.root.after(1000, self._update_status)
    
    def _append_console(self, text: str):
        """Append text to console."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text + "\n")
        
        # Limit console size
        lines = int(self.console.index('end-1c').split('.')[0])
        if lines > config.MAX_CONSOLE_LINES:
            self.console.delete(1.0, f"{lines - config.MAX_CONSOLE_LINES}.0")
        
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def _start_refresh_thread(self):
        """Start background thread for periodic refresh."""
        def refresh_loop():
            while True:
                time.sleep(config.FILE_CHECK_INTERVAL)
                if self.auto_refresh:
                    self.root.after(0, self._update_run_list)
        
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def on_closing(self):
        """Handle window closing."""
        self.los_mode_active = False  # Stop LOS updates
        self.monitor.stop_monitoring()
        if self.controller.is_connected:
            self.controller.disconnect()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = PeriscopeGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

