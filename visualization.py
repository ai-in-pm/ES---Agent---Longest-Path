"""Functions for visualizing Earned Schedule analysis."""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional


def plot_pv_ev_curves(pv_series: List[float], ev_series: List[float], 
                     periods: List[int] = None, title: str = "PV vs EV Curves") -> None:
    """
    Plot PV and EV curves.
    
    Args:
        pv_series: Cumulative Planned Value series
        ev_series: Cumulative Earned Value series
        periods: List of period numbers (x-axis)
        title: Plot title
    """
    if periods is None:
        periods = list(range(1, len(pv_series) + 1))
    
    plt.figure(figsize=(10, 6))
    plt.plot(periods, pv_series, 'b-', marker='o', label='Planned Value (PV)')
    plt.plot(periods, ev_series, 'g-', marker='s', label='Earned Value (EV)')
    plt.title(title)
    plt.xlabel('Period')
    plt.ylabel('Value')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()


def plot_es_metrics(periods: List[int], es_values: List[float], spi_t_values: List[float],
                  title: str = "Earned Schedule Metrics") -> None:
    """
    Plot ES and SPI(t) metrics.
    
    Args:
        periods: List of period numbers
        es_values: List of ES values
        spi_t_values: List of SPI(t) values
        title: Plot title
    """
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot ES on primary axis
    ax1.plot(periods, es_values, 'b-', marker='o', label='ES')
    ax1.set_xlabel('Period')
    ax1.set_ylabel('Earned Schedule (ES)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    # Plot SPI(t) on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(periods, spi_t_values, 'r-', marker='s', label='SPI(t)')
    ax2.set_ylabel('SPI(t)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Add reference line at SPI(t) = 1
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
    
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()


def plot_ieac_forecasts(periods: List[int], path_ieacs: Dict[str, List[float]], 
                      overall_ieac: List[float], planned_duration: float,
                      controlling_path: List[str], anomalies: Optional[Dict] = None,
                      title: str = "IEAC(t) Forecasts by Path") -> None:
    """
    Plot IEAC(t) forecasts for all paths.
    
    Args:
        periods: List of period numbers
        path_ieacs: Dictionary mapping paths to their IEAC history
        overall_ieac: List of overall project IEAC values
        planned_duration: Planned duration
        controlling_path: List of controlling path at each period
        anomalies: Dictionary of anomalies identified
        title: Plot title
    """
    plt.figure(figsize=(12, 7))
    
    # Plot planned duration reference line
    plt.axhline(y=planned_duration, color='black', linestyle='-', 
                label=f'Planned Duration ({planned_duration})')
    
    # Plot overall project IEAC
    plt.plot(periods, overall_ieac, 'k--', marker='o', linewidth=2,
             label='Overall Project IEAC(t)')
    
    # Plot each path's IEAC
    colors = plt.cm.tab10(np.linspace(0, 1, len(path_ieacs)))
    for (path, ieacs), color in zip(path_ieacs.items(), colors):
        # Pad shorter paths with NaN
        padded_ieacs = ieacs + [np.nan] * (len(periods) - len(ieacs))
        plt.plot(periods, padded_ieacs, marker='s', linestyle='-', color=color, 
                 alpha=0.7, label=f'{path} IEAC(t)')
    
    # Highlight controlling path at each period
    for i, period in enumerate(periods):
        if i < len(controlling_path):
            ctrl_path = controlling_path[i]
            if i < len(path_ieacs[ctrl_path]):
                ieac_val = path_ieacs[ctrl_path][i]
                plt.plot(period, ieac_val, 'go', markersize=10, alpha=0.7)
    
    # Mark anomalies if provided
    if anomalies:
        for period, (path, ieac) in anomalies.items():
            plt.plot(int(period), ieac, 'rx', markersize=10, mew=2)
    
    plt.title(title)
    plt.xlabel('Period')
    plt.ylabel('IEAC(t) - Duration Forecast')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')
    plt.tight_layout()


def plot_completion_date_forecast(periods: List[int], ieac_values: List[float], 
                                 start_date: datetime, planned_duration: float,
                                 title: str = "Forecast Completion Date") -> None:
    """
    Plot forecast completion dates over time.
    
    Args:
        periods: List of period numbers
        ieac_values: List of IEAC(t) values (controlling path)
        start_date: Project start date
        planned_duration: Planned duration in periods
        title: Plot title
    """
    if not isinstance(start_date, datetime):
        return  # Cannot plot dates without start_date
    
    # Convert to datetime
    planned_end = start_date + timedelta(days=planned_duration * 7)  # Assuming periods are weeks
    forecast_dates = [start_date + timedelta(days=ieac * 7) for ieac in ieac_values]
    update_dates = [start_date + timedelta(days=period * 7) for period in periods]
    
    plt.figure(figsize=(10, 6))
    plt.plot(update_dates, forecast_dates, 'b-', marker='o')
    plt.axhline(y=planned_end, color='r', linestyle='--', 
                label=f'Planned End: {planned_end.strftime("%Y-%m-%d")}')
    
    # Format x-axis as dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    # Format y-axis as dates
    plt.gca().yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().yaxis.set_major_locator(mdates.MonthLocator())
    
    plt.title(title)
    plt.xlabel('Status Date')
    plt.ylabel('Forecast Completion')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
