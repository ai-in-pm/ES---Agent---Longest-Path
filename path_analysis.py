"""Functions for path-specific ES analysis and critical path selection."""
from typing import Dict, List, Tuple, Set
import es_core


def compute_path_es_metrics(path_pv: List[float], path_ev: List[float], period: int, 
                           planned_duration: float) -> Tuple[float, float, float, float]:
    """
    Compute ES metrics for a specific path at a given period.
    
    Args:
        path_pv: PV series for the path
        path_ev: EV series for the path
        period: Current period (0-indexed)
        planned_duration: Planned duration
    
    Returns:
        Tuple of (ES(L), SPI(t), SV(t), IEAC(t)) for the path
    """
    es, spi_t, sv_t = es_core.compute_earned_schedule(path_pv, path_ev, period)
    ieac_t = es_core.compute_ieac(planned_duration, spi_t)
    
    return es, spi_t, sv_t, ieac_t


def select_controlling_path(path_ieacs: Dict[str, float], path_es_values: Dict[str, float], 
                           prev_controlling: str = None, prev_es: float = None) -> str:
    """
    Select the controlling (longest) path based on IEAC values and ES non-decreasing rule.
    
    Args:
        path_ieacs: Dictionary of path names to their IEAC values
        path_es_values: Dictionary of path names to their ES values
        prev_controlling: Previously selected controlling path
        prev_es: ES value of the previously controlling path
    
    Returns:
        Name of the selected controlling path
    """
    # Sort paths by IEAC (largest first)
    sorted_paths = sorted(path_ieacs.keys(), key=lambda p: path_ieacs[p], reverse=True)
    
    if not prev_controlling or prev_es is None:
        # No previous selection, just take the longest
        return sorted_paths[0]
    
    # Check if the new longest path violates the non-decreasing ES rule
    candidate = sorted_paths[0]
    
    if candidate != prev_controlling and path_es_values[candidate] < prev_es:
        # Anomaly detected - ES decreased. Try next best path
        for path in sorted_paths[1:]:
            if path_es_values[path] >= prev_es:
                return path
        
        # If all paths have decreasing ES, stick with previous path
        return prev_controlling
    
    return candidate


def identify_anomalies(path_ieacs_history: Dict[str, List[float]], 
                      threshold_factor: float = 2.0) -> Dict[str, List[int]]:
    """
    Identify anomalous IEAC forecasts in path history.
    
    Args:
        path_ieacs_history: Dictionary of path names to their IEAC history
        threshold_factor: Factor to determine what constitutes an anomaly
    
    Returns:
        Dictionary of path names to lists of anomalous periods
    """
    anomalies = {}
    
    for path, ieacs in path_ieacs_history.items():
        path_anomalies = []
        
        if len(ieacs) < 3:
            continue
            
        for i in range(1, len(ieacs)-1):
            # Check for spike - current value much larger than neighbors
            if (ieacs[i] > threshold_factor * ieacs[i-1] and 
                ieacs[i] > threshold_factor * ieacs[i+1]):
                path_anomalies.append(i)
                
        if path_anomalies:
            anomalies[path] = path_anomalies
            
    return anomalies
