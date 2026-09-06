import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(days: int = 30) -> pd.DataFrame:
    """
    Generates synthetic daily cost data with obvious injected anomalies for demo purposes.
    """
    np.random.seed(42)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Base cost between $50 and $70
    base_costs = np.random.uniform(50, 70, size=days)
    
    # Add weekly seasonality (weekends are cheaper)
    day_of_week = dates.dayofweek
    seasonality = np.where(day_of_week >= 5, -20, 0)  # weekends are $20 cheaper
    
    # Add some random noise
    noise = np.random.normal(0, 5, size=days)
    
    costs = base_costs + seasonality + noise
    costs = np.maximum(costs, 0) # ensure no negative costs
    
    # Inject obvious anomalies (4-5x normal cost)
    # Put an anomaly around 15 days ago and 3 days ago
    if days > 15:
        costs[-15] = costs[-15] * 4.5
    if days > 3:
        costs[-3] = costs[-3] * 5.0
        
    df = pd.DataFrame({
        'date': dates,
        'cost': costs
    })
    
    return df
