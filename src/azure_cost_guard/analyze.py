import pandas as pd
import numpy as np
from typing import Tuple

# The threshold added to the base k-value to classify an anomaly as "Mild" (usually k+0)
SEVERITY_MILD_THRESHOLD = 0
# The threshold added to the base k-value to classify an anomaly as "Moderate" (usually k+1)
SEVERITY_MODERATE_THRESHOLD = 1
# The threshold added to the base k-value to classify an anomaly as "Severe" (usually k+2)
SEVERITY_SEVERE_THRESHOLD = 2

def determine_severity(z_score: float, threshold_k: float) -> str:
    if z_score > threshold_k + SEVERITY_SEVERE_THRESHOLD:
        return "Severe"
    elif z_score > threshold_k + SEVERITY_MODERATE_THRESHOLD:
        return "Moderate"
    elif z_score > threshold_k + SEVERITY_MILD_THRESHOLD:
        return "Mild"
    return "Normal"

def analyze_simple(df: pd.DataFrame, threshold_k: float = 3.0, window: int = 7) -> pd.DataFrame:
    """
    Simple rolling mean + rolling std anomaly detection.
    """
    df = df.copy()
    if len(df) < window:
        # Not enough data
        df['expected_cost'] = df['cost']
        df['deviation'] = 0.0
        df['is_anomaly'] = False
        df['severity'] = "Normal"
        df['z_score'] = 0.0
        return df

    # We shift by 1 so the current day's cost isn't included in its own mean/std calculation
    rolling = df['cost'].shift(1).rolling(window=window, min_periods=3)
    df['expected_cost'] = rolling.mean().fillna(df['cost'])
    rolling_std = rolling.std().fillna(1.0)
    # prevent division by zero
    rolling_std = np.where(rolling_std < 0.1, 0.1, rolling_std)
    
    df['z_score'] = (df['cost'] - df['expected_cost']) / rolling_std
    df['deviation'] = (df['cost'] - df['expected_cost']) / np.where(df['expected_cost'] > 0, df['expected_cost'], 1) * 100
    
    df['is_anomaly'] = df['z_score'] > threshold_k
    df['severity'] = df['z_score'].apply(lambda z: determine_severity(z, threshold_k))
    
    return df

def analyze_seasonal(df: pd.DataFrame, threshold_k: float = 3.0) -> pd.DataFrame:
    """
    Seasonal trend decomposition using LOESS (STL) for weekly seasonality.
    Requires at least 14 days of data to find weekly patterns.
    """
    from statsmodels.tsa.seasonal import STL
    
    df = df.copy()
    if len(df) < 14:
        # Fallback to simple if not enough data for seasonal decomposition
        return analyze_simple(df, threshold_k)
        
    # STL requires time series to be indexed and sorted
    series = df.set_index('date')['cost']
    
    # period=7 for weekly seasonality on daily data
    stl = STL(series, period=7, robust=True)
    res = stl.fit()
    
    # Expected cost is trend + seasonal (what we expect without the remainder/noise)
    df['expected_cost'] = (res.trend + res.seasonal).values
    df['residual'] = res.resid.values
    
    # Calculate Z-score of the residual
    # We use regular standard deviation. Even though it's inflated by anomalies, 
    # it prevents false positives caused by trend distortion near large spikes.
    std_resid = np.std(df['residual'])
    
    if std_resid < 1.0:
        std_resid = 1.0
        
    df['z_score'] = df['residual'] / std_resid
    df['deviation'] = (df['cost'] - df['expected_cost']) / np.where(df['expected_cost'] > 0, df['expected_cost'], 1) * 100
    
    df['is_anomaly'] = df['z_score'] > threshold_k
    df['severity'] = df['z_score'].apply(lambda z: determine_severity(z, threshold_k))
    
    return df
