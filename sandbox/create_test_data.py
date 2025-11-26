"""
Script to create test data for sandbox mode.
Generates sample analysis results for testing the visualization interface.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import os


def create_test_run(run_name: str, results_dir: Path):
    """Create a test run with sample data."""
    run_dir = results_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample data file (matching pattern data_*.csv)
    data_file = run_dir / "data_sample.csv"
    x = np.linspace(0, 10, 100)
    y = np.sin(x) * np.exp(-x/5)
    data = np.column_stack([x, y])
    np.savetxt(data_file, data, delimiter=',', header='x,y', comments='')
    
    # Create sample plot (matching pattern analysis_*.png)
    plot_file = run_dir / "analysis_sample.png"
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x, y, 'b-', linewidth=2)
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Amplitude', fontsize=12)
    ax.set_title('Sample Analysis Result', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_file, dpi=100)
    plt.close()
    
    # Create summary file (matching pattern summary_*.txt)
    summary_file = run_dir / "summary_sample.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Analysis Summary for {run_name}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Results:\n")
        f.write(f"  - Peak value: {np.max(y):.4f}\n")
        f.write(f"  - Mean value: {np.mean(y):.4f}\n")
        f.write(f"  - Std deviation: {np.std(y):.4f}\n")
        f.write(f"  - Data points: {len(x)}\n")
    
    print(f"Created test run: {run_name}")
    print(f"  - Data file: {data_file}")
    print(f"  - Plot file: {plot_file}")
    print(f"  - Summary file: {summary_file}")


def main():
    """Create multiple test runs."""
    # Get sandbox results directory
    script_dir = Path(__file__).parent
    results_dir = script_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a few test runs
    timestamps = [
        "20240101_120000",
        "20240101_130000",
        "20240101_140000",
    ]
    
    for ts in timestamps:
        run_name = f"run_{ts}"
        create_test_run(run_name, results_dir)
    
    print(f"\nTest data created in: {results_dir}")
    print("You can now test the interface in sandbox mode!")


if __name__ == "__main__":
    main()

