"""
Wrapper for periscope terminal commands.
Executes terminal commands and captures output/return codes.
"""

import subprocess
import threading
from typing import Optional, Callable, List
from pathlib import Path
from queue import Queue
from . import config


class PeriscopeController:
    """Wraps terminal commands for periscope control."""
    
    def __init__(self, output_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize controller.
        
        Args:
            output_callback: Function to call with terminal output lines
        """
        self.app_path = config.PERISCOPE_APP_PATH
        self.output_callback = output_callback
        self.is_connected = False
        self.is_moving = False
        self.last_error = None
        self._process: Optional[subprocess.Popen] = None
        self.azimuth_offset = config.AZIMUTH_OFFSET  # System-wide azimuth offset
    
    def set_azimuth_offset(self, offset: float):
        """
        Set the system azimuth offset from true north.
        
        Args:
            offset: Azimuth offset in degrees
        """
        self.azimuth_offset = offset
    
    def get_azimuth_offset(self) -> float:
        """Get the current azimuth offset."""
        return self.azimuth_offset
    
    def _apply_azimuth_offset(self, azimuth: float) -> float:
        """
        Apply azimuth offset to convert from true north to system coordinates.
        
        Args:
            azimuth: Azimuth angle relative to true north (degrees)
            
        Returns:
            Azimuth angle in system coordinates (degrees)
        """
        return (azimuth - self.azimuth_offset) % 360
        
    def _run_command(self, command: str, timeout: float = 10.0) -> tuple[int, str]:
        """
        Run a terminal command and capture output.
        The periscope software uses interactive commands sent via stdin.
        
        Args:
            command: Command string (e.g., "GO,90,45,A" or "HOME")
            timeout: Maximum time to wait for command
            
        Returns:
            Tuple of (return_code, output_text)
        """
        try:
            # Convert Path to string if needed
            app_path_str = str(self.app_path) if isinstance(self.app_path, Path) else self.app_path
            
            # The periscope software is interactive, so we send commands via stdin
            # Send command followed by EXIT to terminate the session
            process = subprocess.Popen(
                [app_path_str],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(config.PERISCOPE_SOFTWARE_DIR / "dist")  # Ensure config file is found
            )
            
            # Send command and exit
            input_text = f"{command}\nEXIT\n"
            stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            output = stdout + stderr
            returncode = process.returncode
            
            if self.output_callback:
                self.output_callback(f"Command: {command}")
                if output:
                    self.output_callback(output)
                if returncode != 0:
                    self.output_callback(f"Return code: {returncode}")
            
            return returncode, output
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout}s"
            self.last_error = error_msg
            if self.output_callback:
                self.output_callback(f"ERROR: {error_msg}")
            return -1, error_msg
        except Exception as e:
            error_msg = f"Command failed: {str(e)}"
            self.last_error = error_msg
            if self.output_callback:
                self.output_callback(f"ERROR: {error_msg}")
            return -1, error_msg
    
    def connect(self) -> bool:
        """Check connection status using NETWORK or STATUS command."""
        # The periscope software doesn't have explicit connect/disconnect
        # Use STATUS to check if system is ready
        returncode, output = self._run_command("STATUS")
        success = (returncode == 0 and 
                  ("Operation enabled" in output or "Switched on" in output or 
                   "Ready to switch on" in output))
        self.is_connected = success
        if not success:
            self.last_error = output if returncode != 0 else "System not ready"
        return success
    
    def disconnect(self) -> bool:
        """Disconnect from periscope (stop any operations)."""
        # Stop any ongoing operations
        self._run_command("BRAKE")
        self.is_connected = False
        return True
    
    def initialize(self) -> bool:
        """Initialize periscope system (check network and status)."""
        returncode, output = self._run_command("NETWORK", timeout=30.0)
        return returncode == 0
    
    def home(self) -> bool:
        """Home/zero the periscope using HOME command."""
        self.is_moving = True
        returncode, output = self._run_command("HOME", timeout=60.0)
        self.is_moving = False
        # Check for success indicators in output
        success = returncode == 0 and ("Axes at home" in output or "Position Reached" in output)
        return success
    
    def zero(self) -> bool:
        """Zero the periscope using ZERO command (faster but less accurate)."""
        self.is_moving = True
        returncode, output = self._run_command("ZERO", timeout=60.0)
        self.is_moving = False
        success = returncode == 0 and "Axes at zero" in output
        return success
    
    def set_azimuth(self, angle: float) -> bool:
        """
        Set azimuth angle in degrees (absolute mode, relative to true north).
        
        Args:
            angle: Azimuth angle relative to true north (degrees)
        """
        # Apply offset to convert to system coordinates
        system_azimuth = self._apply_azimuth_offset(angle)
        self.is_moving = True
        # Use current elevation (0 as placeholder - could get from POSITION)
        returncode, output = self._run_command(f"GO,{system_azimuth},0,A", timeout=30.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success
    
    def set_elevation(self, angle: float) -> bool:
        """Set elevation angle in degrees (absolute mode)."""
        self.is_moving = True
        # Use current azimuth (0 as placeholder - could get from POSITION)
        returncode, output = self._run_command(f"GO,0,{angle},A", timeout=30.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success
    
    def set_position(self, azimuth: float, elevation: float, mode: str = "A") -> bool:
        """Set both azimuth and elevation angles.
        
        Args:
            azimuth: Azimuth angle in degrees (relative to true north for absolute mode)
            elevation: Elevation angle in degrees
            mode: Operation mode - "A" (absolute), "R" (relative), "L" (local)
        """
        # Apply offset only for absolute mode
        if mode == "A":
            azimuth = self._apply_azimuth_offset(azimuth)
        self.is_moving = True
        returncode, output = self._run_command(f"GO,{azimuth},{elevation},{mode}", timeout=30.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success
    
    def jog_azimuth(self, step: float) -> bool:
        """Jog azimuth by step degrees (positive or negative) using relative mode."""
        self.is_moving = True
        returncode, output = self._run_command(f"GO,{step},0,R", timeout=15.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success
    
    def jog_elevation(self, step: float) -> bool:
        """Jog elevation by step degrees (positive or negative) using relative mode."""
        self.is_moving = True
        returncode, output = self._run_command(f"GO,0,{step},R", timeout=15.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success
    
    def stop(self) -> bool:
        """Stop movement immediately (emergency stop)."""
        returncode, output = self._run_command("STOP", timeout=5.0)
        self.is_moving = False
        return returncode == 0
    
    def brake(self) -> bool:
        """Stop movement with normal deceleration."""
        returncode, output = self._run_command("BRAKE", timeout=5.0)
        self.is_moving = False
        return returncode == 0
    
    def get_position(self) -> dict:
        """Get current position using POSITION command."""
        returncode, output = self._run_command("POSITION")
        # Parse output to extract position information
        azimuth = None
        elevation = None
        if output:
            for line in output.split('\n'):
                if 'Azimuth' in line and 'Local:' in line:
                    try:
                        parts = line.split('Local:')[1].split()[0]
                        azimuth = float(parts)
                    except:
                        pass
                if 'Elevation' in line and 'Local:' in line:
                    try:
                        parts = line.split('Local:')[1].split()[0]
                        elevation = float(parts)
                    except:
                        pass
        
        return {
            "azimuth": azimuth,
            "elevation": elevation,
            "raw_output": output
        }
    
    def get_status(self) -> dict:
        """Get current status using STATUS command."""
        returncode, output = self._run_command("STATUS")
        # Parse output to extract status information
        return {
            "connected": self.is_connected,
            "moving": self.is_moving,
            "error": self.last_error,
            "raw_output": output
        }
    
    def get_errors(self) -> dict:
        """Get error status using ERROR command."""
        returncode, output = self._run_command("ERROR")
        return {
            "has_errors": "None" not in output or returncode != 0,
            "raw_output": output
        }
    
    def send_raw_command(self, command: str) -> tuple[int, str]:
        """Send a raw command string (for advanced users)."""
        return self._run_command(command, timeout=30.0)
    
    def los_mode(self, elevation: float, azimuth: float) -> bool:
        """
        Line-of-Sight (LOS) mode: Move to exact pointing direction.
        
        Args:
            elevation: Elevation angle in degrees
            azimuth: Azimuth angle in degrees (relative to true north)
            
        Returns:
            True if movement completed successfully
        """
        # Apply system-wide azimuth offset
        system_azimuth = self._apply_azimuth_offset(azimuth)
        
        self.is_moving = True
        returncode, output = self._run_command(f"GO,{system_azimuth},{elevation},A", timeout=30.0)
        self.is_moving = False
        success = returncode == 0 and "Position Reached" in output
        return success

