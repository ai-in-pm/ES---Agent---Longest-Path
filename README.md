# Earned Schedule & Critical Path Analysis AI Agent

This project implements an AI agent that analyzes project schedules using both Critical Path Method (CPM) and Earned Schedule (ES) techniques. It identifies the true "Longest Path" of a project and provides accurate forecasts of project completion times based on current progress.

The development of this repository was inspired by the Earned Schedule Community in their development of Earned Schedule tools. To learn more visit https://www.earnedschedule.com/Calculator.shtml

https://github.com/user-attachments/assets/257f16fb-ab1a-45b5-9409-93784afcc8d0

## Key Features

- **Earned Schedule Calculation**: Converts earned value into time units for more reliable schedule analysis
- **Path-Specific Analysis**: Applies ES calculations to individual project paths to identify the controlling path
- **Anomaly Detection**: Identifies and filters out abnormal forecasts caused by temporary work stoppages or data issues
- **Dynamic Critical Path**: Tracks which path is truly controlling the project at each update period
- **Visualization**: Generates informative charts showing PV/EV curves, SPI(t) trends, and completion forecasts
- **Web Interface**: Modern, user-friendly web application for interactive analysis with an "Execute" button

## Theoretical Background

- **Longest Path vs Critical Path**: The longest path is the sequence of activities with the greatest total duration
- **Earned Schedule (ES)**: An extension of EVM that measures schedule progress in time units rather than cost
- **SPI(t)**: Schedule Performance Index (time) = ES / AT, where AT is actual time elapsed
- **IEAC(t)**: Independent Estimate at Completion (time) = Planned Duration / SPI(t)

## Usage

### Command Line Interface
```bash
python main.py [path_to_excel_file]
```

If no Excel file is provided, the program will search for Excel files in the current directory and prompt you to select one.

### Web Interface

For a more interactive experience with a modern UI:

1. Double-click `Launch_ES_Analysis.bat` (Windows) or run:
   ```bash
   python start_web_app.py
   ```

2. A browser window will open automatically to http://localhost:5000
3. Upload your Excel file and click the "Execute Analysis" button
4. View interactive results, visualizations, and path analysis

## Input Data Format

The tool expects an Excel file with the following structure:

- Sheet named "Data Entry" containing:
  - Cumulative PV values in column B, starting from row 4
  - Cumulative EV values in column C, starting from row 4
  - Planned Duration in cell E16
  - Project start date in cell E4 (optional)
- Special marker "XX" can be used to indicate planned downtime (PV) or work stoppages (EV)

Optionally, for path-specific analysis:
- Sheet named "Paths" with path definitions
- Individual sheets for each path with path-specific PV/EV data

## Output

The analysis generates:

1. An Excel file (`es_analysis_results.xlsx`) with detailed metrics for the overall project and each path
2. Visualization charts saved in the `results` directory:
   - PV/EV curves
   - ES metrics over time
   - IEAC forecasts by path
   - Forecast completion date chart (if start date is available)
3. A SQLite database (`es_analysis.db`) that stores analysis history for multiple projects

## Requirements

- Python 3.6+
- openpyxl
- matplotlib
- numpy
- flask (for web interface)

Install requirements with:
```bash
pip install -r requirements.txt
```

## Project Structure

```
ES - Agent - Longest Path/
├── main.py                     # Main analysis script
├── es_core.py                  # Core ES calculations
├── path_analysis.py            # Path-specific analysis
├── data_handler.py             # Data loading/processing
├── visualization.py            # Chart generation
├── database.py                 # Persistent storage
├── web_app.py                  # Flask web application
├── templates/                  # HTML templates
│   └── index.html              # Main web interface
├── results/                    # Output directory
├── requirements.txt            # Python dependencies
├── Launch_ES_Analysis.bat      # Easy launcher for Windows
└── start_web_app.py            # Web app launcher script
```

## References

- Walt Lipke's Earned Schedule methodology (earnedschedule.com)
- Critical Path Method in project management (planacademy.com)
- Path-specific ES analysis techniques (mosaicprojects.com.au)
