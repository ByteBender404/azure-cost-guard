import pytest
from azure_cost_guard.analyze import analyze_simple, analyze_seasonal
from azure_cost_guard.demo_data import generate_synthetic_data

def test_analyze_simple():
    df = generate_synthetic_data(days=30)
    
    # Run analysis
    df_analyzed = analyze_simple(df, threshold_k=3.0)
    
    anomalies = df_analyzed[df_analyzed['is_anomaly']]
    
    # Given our fixed seed in generate_synthetic_data, we should see 2 anomalies
    assert len(anomalies) == 2
    
    # They should be severe since we injected 4-5x spikes
    assert all(anomalies['severity'] == "Severe")
    
    # Check that normal data is not flagged
    normal_data = df_analyzed[~df_analyzed['is_anomaly']]
    assert len(normal_data) == 28

def test_analyze_seasonal():
    df = generate_synthetic_data(days=30)
    
    # Run analysis
    df_analyzed = analyze_seasonal(df, threshold_k=3.0)
    
    anomalies = df_analyzed[df_analyzed['is_anomaly']]
    
    # Should detect the same 2 anomalies
    assert len(anomalies) == 2
    
    # They should be at least Mild
    assert all(anomalies['severity'].isin(["Mild", "Moderate", "Severe"]))
