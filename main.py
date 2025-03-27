"""Main script for Earned Schedule and Longest Path Analysis"""
import os
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

# Import our modules
import es_core
import path_analysis
import data_handler
import visualization
import database


def analyze_project(excel_file: str, output_dir: str = None, project_name: str = None) -> Dict:
    """
    Perform full Earned Schedule and Longest Path analysis on project data.
    
    Args:
        excel_file: Path to Excel file with project data
        output_dir: Directory for output files (defaults to script directory)
        project_name: Name of the project (defaults to Excel filename)
    
    Returns:
        Dictionary of analysis results
    """
    print(f"Loading project data from {excel_file}...")
    project_data = data_handler.load_project_data(excel_file)
    
    # Ensure we have path data (simulate if needed)
    if not project_data['path_data'] or len(project_data['path_data']) == 0:
        print("Simulating path-specific data...")
        project_data = data_handler.simulate_path_data(project_data)
    
    # Extract key data
    pv_series = project_data['pv_series']
    ev_series = project_data['ev_series']
    planned_duration = project_data['planned_duration']
    start_date = project_data['start_date']
    paths = project_data['paths']
    path_data = project_data['path_data']
    
    print(f"Loaded {len(pv_series)} periods of data")
    print(f"Planned Duration: {planned_duration} periods")
    if start_date:
        print(f"Start Date: {start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date}")
    print(f"Found {len(paths)} paths: {', '.join(paths.keys())}")
    
    # Step 1: Compute overall project ES metrics
    print("\nStep 1: Computing overall project Earned Schedule metrics...")
    overall_metrics = []
    for period in range(len(ev_series)):
        es_t, spi_t, sv_t = es_core.compute_earned_schedule(pv_series, ev_series, period)
        ieac_t = es_core.compute_ieac(planned_duration, spi_t)
        overall_metrics.append((es_t, spi_t, ieac_t))
        print(f"  Period {period}: ES={es_t:.2f}, SPI(t)={spi_t:.2f}, IEAC(t)={ieac_t:.2f} periods")
    
    # Step 2: Compute path-specific ES metrics
    print("\nStep 2: Computing path-specific Earned Schedule metrics...")
    path_metrics = {}
    path_ieacs_history = {}
    path_es_history = {}
    
    for path_name, path_data_items in path_data.items():
        print(f"\n  Analyzing path: {path_name}")
        path_pv = path_data_items['pv']
        path_ev = path_data_items['ev']
        path_results = []
        path_ieacs = []
        path_es_values = []
        
        for period in range(len(path_ev)):
            es_l, spi_t, sv_t, ieac_t = path_analysis.compute_path_es_metrics(
                path_pv, path_ev, period, planned_duration)
            path_results.append((es_l, spi_t, sv_t, ieac_t))
            path_ieacs.append(ieac_t)
            path_es_values.append(es_l)
            print(f"    Period {period}: ES(L)={es_l:.2f}, SPI(t)={spi_t:.2f}, IEAC(t)={ieac_t:.2f} periods")
        
        path_metrics[path_name] = path_results
        path_ieacs_history[path_name] = path_ieacs
        path_es_history[path_name] = path_es_values
    
    # Step 3: Select controlling path for each period
    print("\nStep 3: Determining the controlling path for each period...")
    controlling_path = []
    prev_path = None
    prev_es = None
    anomalies = {}
    
    for period in range(len(ev_series)):
        period_ieacs = {}
        period_es = {}
        
        for path, metrics in path_metrics.items():
            if period < len(metrics):
                period_ieacs[path] = metrics[period][3]  # IEAC is index 3
                period_es[path] = metrics[period][0]     # ES is index 0
        
        # Select controlling path for this period
        selected_path = path_analysis.select_controlling_path(
            period_ieacs, period_es, prev_path, prev_es)
        
        # Check for anomalies
        if selected_path != prev_path and prev_path is not None:
            # If path switched and previous had much higher IEAC, mark as anomaly
            if prev_path in period_ieacs and period_ieacs[prev_path] > 1.5 * period_ieacs[selected_path]:
                anomalies[period] = (prev_path, period_ieacs[prev_path])
                print(f"  Period {period}: Anomaly detected! Path {prev_path} showed IEAC={period_ieacs[prev_path]:.2f}")
        
        controlling_path.append(selected_path)
        print(f"  Period {period}: Controlling path is {selected_path} with IEAC(t)={period_ieacs[selected_path]:.2f} periods")
        prev_path = selected_path
        prev_es = period_es[selected_path] if selected_path in period_es else None
    
    # Prepare results
    results = {
        'overall_metrics': overall_metrics,
        'path_metrics': path_metrics,
        'controlling_path': controlling_path,
        'anomalies': anomalies
    }
    
    # Create output directory if needed
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(output_dir, "results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output files
    output_excel = os.path.join(output_dir, "es_analysis_results.xlsx")
    data_handler.write_results_to_excel(project_data, results, output_excel)
    print(f"\nAnalysis results written to {output_excel}")
    
    # Generate visualizations
    generate_visualizations(project_data, results, output_dir)
    
    # Save to database
    if project_name is None:
        project_name = os.path.splitext(os.path.basename(excel_file))[0]
    
    print("\nSaving results to database...")
    db = database.get_db_instance()
    project_id = db.add_project(
        name=project_name,
        planned_duration=planned_duration,
        start_date=start_date if isinstance(start_date, datetime) else None,
        excel_file=os.path.abspath(excel_file)
    )
    analysis_id = db.add_analysis(project_id, results)
    print(f"Saved as project ID: {project_id}, analysis ID: {analysis_id}")
    db.close()
    
    # Print final forecast
    final_period = len(controlling_path) - 1
    final_path = controlling_path[final_period]
    final_ieac = path_metrics[final_path][final_period][3]  # IEAC is index 3
    
    print("\nProject Forecast Summary:")
    print(f"  Planned Duration: {planned_duration} periods")
    print(f"  Current Period: {final_period}")
    print(f"  Controlling Path: {final_path}")
    print(f"  Forecast Duration: {final_ieac:.2f} periods")
    
    if start_date and isinstance(start_date, datetime):
        planned_end = start_date + timedelta(days=planned_duration * 7)  # Assuming weeks
        forecast_end = start_date + timedelta(days=final_ieac * 7)
        print(f"  Planned End Date: {planned_end.strftime('%Y-%m-%d')}")
        print(f"  Forecast End Date: {forecast_end.strftime('%Y-%m-%d')}")
        
        if final_ieac > planned_duration:
            delay = (forecast_end - planned_end).days
            print(f"  Project is forecasted to be {delay} days late")
        else:
            ahead = (planned_end - forecast_end).days
            print(f"  Project is forecasted to be {ahead} days ahead of schedule")
    
    return results


def generate_visualizations(project_data: Dict, results: Dict, output_dir: str) -> None:
    """
    Generate and save visualizations.
    
    Args:
        project_data: Dictionary of project data
        results: Dictionary of analysis results
        output_dir: Directory to save visualizations
    """
    print("\nGenerating visualizations...")
    # Extract data for plotting
    periods = list(range(1, len(project_data['ev_series']) + 1))
    
    # Extract metrics
    overall_es = [m[0] for m in results['overall_metrics']]
    overall_spi = [m[1] for m in results['overall_metrics']]
    overall_ieac = [m[2] for m in results['overall_metrics']]
    
    # PV vs EV curve
    visualization.plot_pv_ev_curves(project_data['pv_series'], project_data['ev_series'], periods)
    pv_ev_file = os.path.join(output_dir, "pv_ev_curves.png")
    plt.savefig(pv_ev_file)
    print(f"  PV/EV curves saved to {pv_ev_file}")
    plt.close()
    
    # ES and SPI(t) metrics
    visualization.plot_es_metrics(periods, overall_es, overall_spi)
    es_metrics_file = os.path.join(output_dir, "es_metrics.png")
    plt.savefig(es_metrics_file)
    print(f"  ES metrics chart saved to {es_metrics_file}")
    plt.close()
    
    # Prepare path IEACs for plotting
    path_ieacs_for_plot = {}
    for path, metrics in results['path_metrics'].items():
        path_ieacs_for_plot[path] = [m[3] for m in metrics]  # IEAC is index 3
    
    # IEAC forecasts
    visualization.plot_ieac_forecasts(
        periods, path_ieacs_for_plot, overall_ieac, 
        project_data['planned_duration'], results['controlling_path'], 
        results['anomalies'])
    ieac_file = os.path.join(output_dir, "ieac_forecasts.png")
    plt.savefig(ieac_file)
    print(f"  IEAC forecasts chart saved to {ieac_file}")
    plt.close()
    
    # Completion date forecast (if start date is available)
    if isinstance(project_data['start_date'], datetime):
        # Get controlling path IEAC for each period
        controlling_ieacs = []
        for i, path in enumerate(results['controlling_path']):
            path_metrics = results['path_metrics'][path]
            if i < len(path_metrics):
                controlling_ieacs.append(path_metrics[i][3])  # IEAC is index 3
            else:
                controlling_ieacs.append(overall_ieac[i])  # Fallback to overall
        
        visualization.plot_completion_date_forecast(
            periods, controlling_ieacs, project_data['start_date'], 
            project_data['planned_duration'])
        completion_file = os.path.join(output_dir, "completion_forecast.png")
        plt.savefig(completion_file)
        print(f"  Completion date forecast saved to {completion_file}")
        plt.close()


def print_introduction():
    """Print introduction and explanation of the tool"""
    print("\n" + "=" * 80)
    print("EARNED SCHEDULE & CRITICAL PATH ANALYSIS AI AGENT".center(80))
    print("=" * 80)
    print("\nThis AI agent analyzes project schedules using both Critical Path Method (CPM)")
    print("and Earned Schedule (ES) techniques. It identifies the true 'Longest Path' of")
    print("a project and provides accurate forecasts of project completion times.")
    print("\nThe analysis will:")
    print("  1. Calculate overall Earned Schedule metrics")
    print("  2. Analyze each path separately to identify the controlling path")
    print("  3. Detect and filter anomalies in the forecast")
    print("  4. Generate visualizations and forecast project completion")
    print("  5. Store results in a database for historical tracking")
    print("\nResults will be saved to Excel and as visualization charts.")
    print("=" * 80 + "\n")


def main():
    print_introduction()
    
    # Check if Excel file is provided
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        # Don't prompt for project name in non-interactive mode
        project_name = os.path.splitext(os.path.basename(excel_file))[0]
    else:
        # Look for Excel files in the current directory
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~$')]
        
        if not excel_files:
            print("No Excel files found. Please provide an Excel file path.")
            print("Usage: python main.py [path_to_excel_file]")
            sys.exit(1)
        
        if len(excel_files) == 1:
            excel_file = excel_files[0]
            project_name = os.path.splitext(excel_file)[0]
        else:
            print("Multiple Excel files found. Using the first one by default.")
            excel_file = excel_files[0]
            project_name = os.path.splitext(excel_file)[0]
    
    # Create output directory
    output_dir = "results"
    
    # Analyze project
    try:
        analyze_project(excel_file, output_dir, project_name)
        print("\nAnalysis complete! Results and visualizations saved to the 'results' directory.")
        print("The database file 'es_analysis.db' contains all historical analyses.")
        print("\nThe AI Agent has successfully analyzed the Critical Path and Earned Schedule of your project.")
        print("Review the Excel file and visualization images to see the performance trends.")
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
