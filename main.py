"""
Main entry point for the Periscope Control Interface.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.gui import PeriscopeGUI
from src import config
import tkinter as tk


def main():
    """Main entry point."""
    # Check for sandbox mode
    sandbox_mode = config.SANDBOX_MODE or os.getenv("SANDBOX_MODE", "").lower() == "true"
    
    if sandbox_mode:
        print("Starting in SANDBOX MODE - using mock controller")
        print(f"Sandbox results directory: {config.SANDBOX_RESULTS_DIR}")
    
    root = tk.Tk()
    app = PeriscopeGUI(root, sandbox_mode=sandbox_mode)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

