"""
Simple test script to launch the interface in sandbox mode.
Run this from the project root: python test_gui.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
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
    try:
        results_dir = generate_test_data_if_needed()
        print(f"Results directory: {results_dir}\n")
    except Exception as e:
        print(f"Warning: Could not generate test data: {e}")
        print("Continuing anyway...\n")
    
    # Set sandbox mode
    os.environ["SANDBOX_MODE"] = "true"
    
    # Import and start GUI
    print("Starting GUI...")
    print("-" * 60)
    
    try:
        from src.gui import PeriscopeGUI
        import tkinter as tk
        
        # Create root window
        root = tk.Tk()
        
        # Create application in sandbox mode
        app = PeriscopeGUI(root, sandbox_mode=True)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("\n✓ Interface launched successfully!")
        print("  Window should now be visible.")
        print("\nYou can:")
        print("  - Test all controls (they use mock hardware)")
        print("  - Click 'Load Latest' to view test data")
        print("  - Review the design and layout")
        print("\nClose the window when done.\n")
        
        # Start main loop
        root.mainloop()
        
    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print("\nMake sure you're running from the project root directory.")
        print("And that all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: Failed to start interface: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

