"""
Mock periscope controller for sandbox/testing mode.
Simulates periscope behavior without requiring real hardware.
"""

import time
import threading
from typing import Optional, Callable
from pathlib import Path


class MockPeriscopeController:
    """Mock controller that simulates periscope behavior."""
    
    def __init__(self, output_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize mock controller.
        
        Args:
            output_callback: Function to call with simulated terminal output lines
        """
        self.output_callback = output_callback
        self.is_connected = False
        self.is_moving = False
        self.last_error = None
        
        # Simulated position state
        self.azimuth = 0.0
        self.elevation = 0.0
        self.azimuth_offset = 0.0  # System-wide azimuth offset
        self._motion_thread: Optional[threading.Thread] = None
    
    def set_azimuth_offset(self, offset: float):
        """Set the system azimuth offset from true north."""
        self.azimuth_offset = offset
    
    def get_azimuth_offset(self) -> float:
        """Get the current azimuth offset."""
        return self.azimuth_offset
    
    def _apply_azimuth_offset(self, azimuth: float) -> float:
        """Apply azimuth offset to convert from true north to system coordinates."""
        return (azimuth - self.azimuth_offset) % 360
    
    def _log(self, message: str):
        """Log a message via callback."""
        if self.output_callback:
            self.output_callback(message)
    
    def _simulate_motion(self, duration: float, target_azimuth: Optional[float] = None, 
                        target_elevation: Optional[float] = None):
        """Simulate motion over time."""
        self.is_moving = True
        start_az = self.azimuth
        start_el = self.elevation
        
        steps = int(duration * 10)  # Update 10 times per second
        if steps == 0:
            steps = 1
        
        for i in range(steps + 1):
            if not self.is_moving:  # Can be stopped
                break
            
            progress = i / steps
            if target_azimuth is not None:
                self.azimuth = start_az + (target_azimuth - start_az) * progress
            if target_elevation is not None:
                self.elevation = start_el + (target_elevation - start_el) * progress
            
            self._log(f"Local Elevation:{self.elevation:.2f}, Local Azimuth:{self.azimuth:.2f}")
            time.sleep(duration / steps)
        
        self.is_moving = False
    
    def connect(self) -> bool:
        """Simulate connection."""
        self._log("Command: STATUS")
        self._log("Elevation axis status: Operation enabled")
        self._log("Azimuth axis status: Operation enabled")
        self.is_connected = True
        return True
    
    def disconnect(self) -> bool:
        """Simulate disconnection."""
        if self.is_moving:
            self.brake()
        self.is_connected = False
        self._log("Disconnected")
        return True
    
    def initialize(self) -> bool:
        """Simulate initialization."""
        self._log("Command: NETWORK")
        self._log("Scanning network...")
        self._log("Found 2 devices")
        return True
    
    def home(self) -> bool:
        """Simulate homing."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        self._log("Command: HOME")
        self._log("AZIMUTH Homing")
        self._log("AZIMUTH Zeroing")
        
        def home_thread():
            self._simulate_motion(3.0, target_azimuth=0.0)
            self._log("AZIMUTH Position Reached")
            self._log("ELEVATION Homing")
            self._log("ELEVATION Zeroing")
            self._simulate_motion(3.0, target_elevation=0.0)
            self._log("ELEVATION Position Reached")
            self._log("Axes at home")
            self.azimuth = 0.0
            self.elevation = 0.0
        
        self._motion_thread = threading.Thread(target=home_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def zero(self) -> bool:
        """Simulate zeroing."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        self._log("Command: ZERO")
        self._log("Homing to local zero...")
        
        def zero_thread():
            self._simulate_motion(2.0, target_azimuth=0.0, target_elevation=0.0)
            self._log("AZIMUTH Position Reached")
            self._log("ELEVATION Position Reached")
            self._log("Axes at zero")
            self.azimuth = 0.0
            self.elevation = 0.0
        
        self._motion_thread = threading.Thread(target=zero_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def set_azimuth(self, angle: float) -> bool:
        """Simulate setting azimuth angle (relative to true north)."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        # Apply offset
        system_azimuth = self._apply_azimuth_offset(angle)
        self._log(f"Command: GO,{system_azimuth},0,A (true north: {angle}°, offset: {self.azimuth_offset}°)")
        self._log(f"AZIMUTH Moving to: {system_azimuth} °, speed: 150 RPM, relative to current position: False")
        
        def move_thread():
            self._simulate_motion(2.0, target_azimuth=system_azimuth)
            self._log("AZIMUTH Position Reached")
        
        self._motion_thread = threading.Thread(target=move_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def set_elevation(self, angle: float) -> bool:
        """Simulate setting elevation angle."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        self._log(f"Command: GO,0,{angle},A")
        self._log(f"ELEVATION Moving to: {angle} °, speed: 150 RPM, relative to current position: False")
        
        def move_thread():
            self._simulate_motion(2.0, target_elevation=angle)
            self._log("ELEVATION Position Reached")
        
        self._motion_thread = threading.Thread(target=move_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def set_position(self, azimuth: float, elevation: float, mode: str = "A") -> bool:
        """Simulate setting both angles (azimuth relative to true north for absolute mode)."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        # Apply offset only for absolute mode
        if mode == "A":
            system_azimuth = self._apply_azimuth_offset(azimuth)
        else:
            system_azimuth = azimuth
        
        self._log(f"Command: GO,{system_azimuth},{elevation},{mode}")
        self._log(f"AZIMUTH Moving to: {system_azimuth} °, speed: 150 RPM")
        self._log(f"ELEVATION Moving to: {elevation} °, speed: 150 RPM")
        
        def move_thread():
            self._simulate_motion(3.0, target_azimuth=system_azimuth, target_elevation=elevation)
            self._log("AZIMUTH Position Reached")
            self._log("ELEVATION Position Reached")
            self.azimuth = system_azimuth
            self.elevation = elevation
        
        self._motion_thread = threading.Thread(target=move_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def jog_azimuth(self, step: float) -> bool:
        """Simulate azimuth jog."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        target = self.azimuth + step
        self._log(f"Command: GO,{step},0,R")
        self._log(f"AZIMUTH Moving to: {target} °, speed: 24 RPM, Relative to current position")
        
        def move_thread():
            self._simulate_motion(1.0, target_azimuth=target)
            self._log("AZIMUTH Position Reached")
        
        self._motion_thread = threading.Thread(target=move_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def jog_elevation(self, step: float) -> bool:
        """Simulate elevation jog."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        target = self.elevation + step
        self._log(f"Command: GO,0,{step},R")
        self._log(f"ELEVATION Moving to: {target} °, speed: 24 RPM, Relative to current position")
        
        def move_thread():
            self._simulate_motion(1.0, target_elevation=target)
            self._log("ELEVATION Position Reached")
        
        self._motion_thread = threading.Thread(target=move_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def stop(self) -> bool:
        """Simulate emergency stop."""
        self._log("Command: STOP")
        self.is_moving = False
        self._log("Movement stopped")
        return True
    
    def brake(self) -> bool:
        """Simulate brake."""
        self._log("Command: BRAKE")
        self.is_moving = False
        self._log("Braking...")
        time.sleep(0.5)
        self._log("Stopped")
        return True
    
    def get_position(self) -> dict:
        """Get simulated position."""
        self._log("Command: POSITION")
        output = f"Elevation position. Local:{self.elevation:.2f} Absolute:{self.elevation:.4f}\n"
        output += f"Azimuth position. Local:{self.azimuth:.2f} Absolute:{self.azimuth:.4f}"
        self._log(output)
        return {
            "azimuth": self.azimuth,
            "elevation": self.elevation,
            "raw_output": output
        }
    
    def get_status(self) -> dict:
        """Get simulated status."""
        self._log("Command: STATUS")
        output = "Elevation axis status: Operation enabled\n"
        output += "Azimuth axis status: Operation enabled"
        self._log(output)
        return {
            "connected": self.is_connected,
            "moving": self.is_moving,
            "error": self.last_error,
            "raw_output": output
        }
    
    def get_errors(self) -> dict:
        """Get simulated errors."""
        self._log("Command: ERROR")
        output = "Elevation axis error: None\n"
        output += "Azimuth axis error: None"
        self._log(output)
        return {
            "has_errors": False,
            "raw_output": output
        }
    
    def los_mode(self, elevation: float, azimuth: float) -> bool:
        """Simulate LOS mode movement (azimuth relative to true north)."""
        if not self.is_connected:
            self.last_error = "Not connected"
            return False
        
        # Apply system-wide offset
        system_azimuth = self._apply_azimuth_offset(azimuth)
        
        self._log(f"Command: LOS Mode - Elevation: {elevation}°, Azimuth: {azimuth}° (true north)")
        self._log(f"System azimuth (with offset {self.azimuth_offset}°): {system_azimuth}°")
        
        def los_thread():
            self._simulate_motion(2.5, target_azimuth=system_azimuth, target_elevation=elevation)
            self._log("AZIMUTH Position Reached")
            self._log("ELEVATION Position Reached")
            self._log("LOS position reached")
            self.azimuth = system_azimuth
            self.elevation = elevation
        
        self._motion_thread = threading.Thread(target=los_thread, daemon=True)
        self._motion_thread.start()
        return True
    
    def send_raw_command(self, command: str) -> tuple[int, str]:
        """Simulate raw command."""
        self._log(f"Command: {command}")
        self._log(f"[MOCK] Command '{command}' executed")
        return 0, f"[MOCK] Command '{command}' executed successfully"

