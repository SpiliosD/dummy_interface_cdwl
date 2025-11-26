# Sandbox Mode

The sandbox provides a safe testing environment for the periscope control interface without requiring real hardware.

## Features

- **Mock Controller**: Simulates periscope behavior with realistic responses
- **Test Data**: Sample analysis results for testing visualization
- **Safe Testing**: No risk of damaging hardware during development

## Usage

### Enable Sandbox Mode

Set the environment variable before running:

```bash
# Windows PowerShell
$env:SANDBOX_MODE="true"
python main.py

# Windows CMD
set SANDBOX_MODE=true
python main.py

# Linux/Mac
export SANDBOX_MODE=true
python main.py
```

Or modify `src/config.py` and set:
```python
SANDBOX_MODE = True
```

### Create Test Data

Generate sample analysis results:

```bash
python sandbox/create_test_data.py
```

This creates test runs in `sandbox/results/` with:
- Sample data files (CSV)
- Sample plots (PNG)
- Sample summary files (TXT)

## Mock Controller Behavior

The mock controller simulates:
- Connection/disconnection
- Homing and zeroing operations
- Movement commands (azimuth and elevation)
- Position reporting
- Status queries
- Realistic timing and responses

All commands are executed instantly with simulated motion feedback.

## Test Data Structure

Test runs are created in `sandbox/results/run_YYYYMMDD_HHMMSS/` with:
- `data_*.csv` - Sample data files
- `analysis_*.png` - Sample plot images
- `summary_*.txt` - Sample summary text files

