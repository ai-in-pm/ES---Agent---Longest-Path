"""Core functions for Earned Schedule calculations."""
import numpy as np
from typing import List, Tuple, Dict, Union, Optional


def compute_earned_schedule(pv_series: List[float], ev_series: List[float], at: int) -> Tuple[float, float, float]:
    """
    Compute Earned Schedule metrics for a given period.
    
    Args:
        pv_series: Cumulative Planned Value series
        ev_series: Cumulative Earned Value series
        at: Actual Time (period number, 0-indexed)
    
    Returns:
        Tuple of (ES, SPI(t), SV(t))
    """
    if at < 0 or at >= len(ev_series):
        raise ValueError(f"Invalid period {at}. Must be between 0 and {len(ev_series)-1}")
    
    ev_t = ev_series[at]
    
    # Find N: last index where PV <= EV_t
    n = 0
    for i, pv_val in enumerate(pv_series):
        if pv_val <= ev_t:
            n = i
        else:
            break
    
    # Compute ES
    if n == 0 and pv_series[0] > ev_t:
        # EV is less than first PV
        es_t = ev_t / pv_series[0] if pv_series[0] > 0 else 0
    elif n >= len(pv_series) - 1:
        # EV exceeds final PV
        es_t = float(n)
    else:
        # Interpolate between periods
        prev_pv = pv_series[n]
        next_pv = pv_series[n+1]
        num = ev_t - prev_pv
        denom = next_pv - prev_pv if next_pv > prev_pv else 1  # Avoid division by zero
        frac = num / denom
        es_t = float(n) + frac
    
    # Compute SPI(t) and SV(t)
    at_float = float(at)
    spi_t = es_t / at_float if at_float > 0 else 1.0  # Define SPI=1 at t=0
    sv_t = es_t - at_float
    
    return es_t, spi_t, sv_t


def compute_ieac(planned_duration: float, spi_t: float) -> float:
    """
    Compute Independent Estimate at Completion (time-based)
    
    Args:
        planned_duration: Planned Duration (PD)
        spi_t: Schedule Performance Index (time-based)
    
    Returns:
        IEAC(t): Forecasted project duration
    """
    if spi_t <= 0:
        return float('inf')  # Avoid division by zero or negative SPI
    
    return planned_duration / spi_t
