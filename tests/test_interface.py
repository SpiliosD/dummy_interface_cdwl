"""
Test script to launch the interface in sandbox mode for design review.

This script will:
1. Generate test data if needed (creates sample analysis results)
2. Launch the GUI in sandbox mode (no real hardware required)
3. Display the interface for visual inspection and testing

Usage:
    python test_interface.py

The interface will open in a window. You can:
- Test all periscope controls (they use mock hardware)
- Load and view test analysis results
- Review the design and layout
- Provide feedback on the interface design

Close the window when done reviewing.
"""

import sys
import os
from pathlib import Path

# Get the project root directory (parent of tests/)
project_root = Path(__file__).parent.parent
# Add project root to path so we can import src
sys.path.insert(0, str(project_root))

def generate_test_data_if_needed():
    """Generate test data if sandbox results directory is empty."""
    from src import config
    
    sandbox_results = config.SANDBOX_RESULTS_DIR
    sandbox_results.mkdir(parents=True, exist_ok=True)
    
    # Check if we have any runs
    existing_runs = list(sandbox_results.glob("run_*"))
    
    if not existing_runs:
        print("Generating test data...")
        # Import and run the test data generator
        from sandbox.create_test_data import main as create_data
        create_data()
        print("Test data generated successfully!")
    else:
        print(f"Found {len(existing_runs)} existing test runs")
    
    return sandbox_results


def main():
    """Launch the interface in sandbox mode for testing."""
    print("=" * 60)
    print("Periscope Control Interface - Design Test Mode")
    print("=" * 60)
    print("\nThis will launch the interface in SANDBOX MODE")
    print("(No real hardware required)\n")
    
    # Generate test data
    results_dir = generate_test_data_if_needed()
    print(f"Results directory: {results_dir}\n")
    
    # Set sandbox mode
    os.environ["SANDBOX_MODE"] = "true"
    
    # Import and start GUI
    print("Starting GUI...")
    print("-" * 60)
    
    try:
        from src.gui import PeriscopeGUI
        from src import config
        import tkinter as tk
        
        # Create root window
        root = tk.Tk()
        
        # Create application in sandbox mode
        app = PeriscopeGUI(root, sandbox_mode=True)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("\nInterface launched successfully!")
        print("Window should now be visible.")
        print("\nYou can:")
        print("  - Test all controls (they use mock hardware)")
        print("  - Load test data from the visualization panel")
        print("  - Review the design and layout")
        print("\nClose the window when done.\n")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"\nERROR: Failed to start interface: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

